from types import SimpleNamespace

from retrieval.rrf import RRFResult
from generation.ollama import OllamaGenerator


def result():
    return RRFResult("c1", "d1", "Section 439 concerns bail.", 0.1, 1, 1, {})


class FakeClient:
    def __init__(self):
        self.kwargs = None

    def chat(self, **kwargs):
        self.kwargs = kwargs
        return iter(
            [
                SimpleNamespace(
                    message=SimpleNamespace(content="[SOURCE: c1] Section 439 ")
                ),
                SimpleNamespace(
                    message=SimpleNamespace(content="concerns bail.")
                ),
            ]
        )


def test_prompt_contains_source_query_and_output_rules():
    prompt = OllamaGenerator(client=FakeClient()).build_prompt(
        "What is bail?", [result()]
    )
    assert "[SOURCE: c1]" in prompt
    assert "What is bail?" in prompt
    assert "Return only the final answer" in prompt
    assert "Do not include analysis" in prompt


def test_system_prompt_rejects_reasoning_narration():
    prompt = OllamaGenerator(client=FakeClient()).system_prompt
    assert "Return only the final answer" in prompt
    assert "Do not describe your reasoning" in prompt


def test_generate_streams_and_returns_citation():
    client = FakeClient()
    generated = OllamaGenerator(client=client).generate("What is bail?", [result()])

    assert generated.model == "qwen3:4b"
    assert generated.answer == "[SOURCE: c1] Section 439 concerns bail."
    assert generated.citations == ["c1"]
    assert client.kwargs["stream"] is True
    assert client.kwargs["think"] is False
    assert client.kwargs["keep_alive"] == "10m"
    assert client.kwargs["options"]["temperature"] == 0.2


def test_empty_answer_fails():
    class Empty:
        def chat(self, **kwargs):
            return iter([SimpleNamespace(message=SimpleNamespace(content=""))])

    try:
        OllamaGenerator(client=Empty()).generate("Question", [result()])
    except RuntimeError as exc:
        assert "empty answer" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
