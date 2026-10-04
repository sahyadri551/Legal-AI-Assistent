from types import SimpleNamespace

import generation.groq as groq_module
from retrieval.rrf import RRFResult
from generation.groq import GroqGenerator, GroqRateLimitError


def result():
    return RRFResult("c1", "d1", "Section 439 concerns bail.", 0.1, 1, 1, {})


class FakeCompletions:
    def __init__(self, content='{"answer":"[SOURCE: c1] Section 439 concerns bail."}'):
        self.kwargs = None
        self.content = content

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content)
                )
            ]
        )


class FakeClient:
    def __init__(self, content='{"answer":"[SOURCE: c1] Section 439 concerns bail."}'):
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


def test_prompt_contains_source_query_and_output_rules():
    prompt = GroqGenerator(client=FakeClient()).build_prompt(
        "What is bail?", [result()]
    )
    assert "[SOURCE: c1]" in prompt
    assert "What is bail?" in prompt
    assert '"answer"' in prompt
    assert "Do not put analysis" in prompt


def test_generate_uses_gpt_oss_120b_and_strict_json():
    client = FakeClient()
    generated = GroqGenerator(client=client).generate("What is bail?", [result()])

    assert generated.model == "openai/gpt-oss-120b"
    assert generated.answer == "[SOURCE: c1] Section 439 concerns bail."
    assert generated.citations == ["c1"]
    assert client.chat.completions.kwargs["stream"] is False
    assert client.chat.completions.kwargs["reasoning_effort"] == "medium"
    assert client.chat.completions.kwargs["extra_body"] == {"include_reasoning": False}
    assert client.chat.completions.kwargs["max_completion_tokens"] == 2048
    assert client.chat.completions.kwargs["response_format"]["type"] == "json_schema"
    assert client.chat.completions.kwargs["response_format"]["json_schema"]["strict"] is True


def test_malformed_structured_output_fails():
    client = FakeClient("not valid json")
    try:
        GroqGenerator(client=client).generate("What is bail?", [result()])
    except RuntimeError as exc:
        assert "malformed structured output" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_empty_answer_fails():
    client = FakeClient('{"answer":""}')
    try:
        GroqGenerator(client=client).generate("Question", [result()])
    except RuntimeError as exc:
        assert "contains no answer" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


class FakeRateLimitError(groq_module.RateLimitError):
    def __init__(self, retry_after="0"):
        self.response = SimpleNamespace(headers={"retry-after": retry_after})


class RateLimitedCompletions:
    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise FakeRateLimitError("0")
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"answer":"[SOURCE: c1] Section 439 concerns bail."}'
                    )
                )
            ]
        )


def test_rate_limit_retries_using_retry_after(monkeypatch):
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=RateLimitedCompletions())
    )
    sleeps = []
    generator = GroqGenerator(
        client=client,
        max_retries=1,
        sleep_fn=sleeps.append,
    )

    monkeypatch.setattr(groq_module, "RateLimitError", FakeRateLimitError)

    generated = generator.generate("What is bail?", [result()])

    assert generated.answer == "[SOURCE: c1] Section 439 concerns bail."
    assert sleeps == [0.0]


class AlwaysRateLimited:
    def create(self, **kwargs):
        raise FakeRateLimitError("0")


def test_rate_limit_exhaustion_is_actionable(monkeypatch):
    client = SimpleNamespace(
        chat=SimpleNamespace(completions=AlwaysRateLimited())
    )
    generator = GroqGenerator(client=client, max_retries=1, sleep_fn=lambda _: None)
    monkeypatch.setattr(groq_module, "RateLimitError", FakeRateLimitError)

    try:
        generator.generate("What is bail?", [result()])
    except GroqRateLimitError as exc:
        assert "rate limit" in str(exc)
    else:
        raise AssertionError("expected GroqRateLimitError")