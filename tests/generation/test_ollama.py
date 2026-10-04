from types import SimpleNamespace
from retrieval.rrf import RRFResult
from generation.ollama import OllamaGenerator

def result(): return RRFResult("c1","d1","Section 439 concerns bail.",0.1,1,1,{})
class FakeClient:
    def __init__(self): self.kwargs=None
    def chat(self,**kwargs):
        self.kwargs=kwargs
        return SimpleNamespace(message=SimpleNamespace(content="[SOURCE: c1] Section 439 concerns bail."))

def test_prompt_contains_source_query_and_output_rules():
    p=OllamaGenerator(client=FakeClient()).build_prompt("What is bail?",[result()])
    assert "[SOURCE: c1]" in p and "What is bail?" in p
    assert "Return only the final answer" in p
    assert "Do not include analysis" in p

def test_system_prompt_rejects_reasoning_narration():
    p=OllamaGenerator(client=FakeClient()).system_prompt
    assert "Return only the final answer" in p
    assert "Do not describe your reasoning" in p

def test_generate_returns_citation():
    c=FakeClient()
    r=OllamaGenerator(client=c).generate("What is bail?",[result()])
    assert r.model=="qwen3:4b" and r.citations==["c1"] and c.kwargs["options"]["temperature"]==0.2
    assert c.kwargs["think"] is False

def test_empty_answer_fails():
    class Empty:
        def chat(self,**kwargs): return SimpleNamespace(message=SimpleNamespace(content=""))
    try: OllamaGenerator(client=Empty()).generate("Question",[result()])
    except RuntimeError as exc: assert "empty answer" in str(exc)
    else: raise AssertionError("expected RuntimeError")
