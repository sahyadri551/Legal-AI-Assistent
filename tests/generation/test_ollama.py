from types import SimpleNamespace

from ollama import ResponseError

from retrieval.rrf import RRFResult
from generation.ollama import OllamaGenerator


def result():
    return RRFResult("c1", "d1", "Section 439 concerns bail.", 0.1, 1, 1, {})


class FakeClient:
    def __init__(self, content='{"answer":"[SOURCE: c1] Section 439 concerns bail."}'):
        self.kwargs = None
        self.content = content

    def chat(self, **kwargs):
        self.kwargs = kwargs
        midpoint = max(1, len(self.content) // 2)
        return iter(
            [
                SimpleNamespace(message=SimpleNamespace(content=self.content[:midpoint])),
                SimpleNamespace(message=SimpleNamespace(content=self.content[midpoint:])),
            ]
        )


def test_prompt_contains_source_query_and_output_rules():
    prompt = OllamaGenerator(client=FakeClient()).build_prompt(
        "What is bail?", [result()]
    )
    assert "[SOURCE: c1]" in prompt
    assert "What is bail?" in prompt
    assert '"answer"' in prompt
    assert "Do not put analysis" in prompt


def test_system_prompt_rejects_reasoning_narration():
    prompt = OllamaGenerator(client=FakeClient()).system_prompt
    assert "required JSON object" in prompt
    assert "never reasoning" in prompt


def test_generate_extracts_only_structured_answer():
    client = FakeClient()
    generated = OllamaGenerator(client=client).generate("What is bail?", [result()])

    assert generated.model == "qwen3:4b"
    assert generated.answer == "[SOURCE: c1] Section 439 concerns bail."
    assert generated.citations == ["c1"]
    assert client.kwargs["stream"] is True
    assert client.kwargs["think"] is False
    assert client.kwargs["keep_alive"] == "10m"
    assert client.kwargs["format"] == OllamaGenerator.RESPONSE_SCHEMA
    assert client.kwargs["options"]["num_ctx"] == 2048
    assert client.kwargs["options"]["num_predict"] == 384


def test_malformed_structured_output_fails():
    client = FakeClient("Hmm, the user is asking about bail.")
    try:
        OllamaGenerator(client=client).generate("What is bail?", [result()])
    except RuntimeError as exc:
        assert "malformed structured output" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_empty_answer_fails():
    client = FakeClient('{"answer":""}')
    try:
        OllamaGenerator(client=client).generate("Question", [result()])
    except RuntimeError as exc:
        assert "contains no answer" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


class OOMClient:
    def chat(self, **kwargs):
        def stream():
            raise ResponseError(
                "llama-server reported out-of-memory during startup: "
                "failed to allocate CPU buffer",
                500,
            )
            yield None

        return stream()


def test_oom_response_becomes_actionable_runtime_error():
    try:
        OllamaGenerator(client=OOMClient()).generate("What is bail?", [result()])
    except RuntimeError as exc:
        assert "ran out of CPU memory" in str(exc)
        assert "2048-token context" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
