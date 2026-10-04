import json
from pathlib import Path
import numpy as np
import pytest
from retrieval.dense import DenseIndex, DenseRetriever

def _records():
    return [
        {"chunk_id": "c1", "doc_id": "d1", "text": "bail section 439", "doc_type": "judgment"},
        {"chunk_id": "c2", "doc_id": "d2", "text": "contract damages", "doc_type": "judgment"},
        {"chunk_id": "c3", "doc_id": "d3", "text": "murder punishment", "doc_type": "statute"},
    ]

def test_build_normalizes_and_ranks_by_inner_product():
    index = DenseIndex.build(_records(), np.array([[2,0],[0,3],[1,1]], dtype=np.float32))
    results = index.search(np.array([1,0], dtype=np.float32), top_k=2)
    assert index.index.ntotal == 3
    assert results[0].chunk_id == "c1"
    assert results[0].score == pytest.approx(1.0)
    assert results[0].rank == 1

def test_save_and_load_preserves_results(tmp_path: Path):
    index = DenseIndex.build(_records(), np.eye(3, dtype=np.float32))
    index.save(tmp_path)
    loaded = DenseIndex.load(tmp_path)
    results = loaded.search(np.array([0,1,0], dtype=np.float32), top_k=2)
    assert results[0].chunk_id == "c2"
    assert results[0].metadata["doc_type"] == "judgment"
    manifest = json.loads((tmp_path/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["index_type"] == "IndexFlatIP"
    assert manifest["dimension"] == 3

def test_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        DenseIndex.build([], np.ones((0,2), dtype=np.float32))
    with pytest.raises(ValueError):
        DenseIndex.build(_records(), np.zeros((3,2), dtype=np.float32))
    index = DenseIndex.build(_records(), np.eye(3, dtype=np.float32))
    with pytest.raises(ValueError):
        index.search(np.array([1,0,0], dtype=np.float32), top_k=0)

def test_dense_retriever_uses_cpu_encoder(monkeypatch, tmp_path: Path):
    class FakeEncoder:
        def __init__(self, model_name, device="cpu"):
            assert device == "cpu"
        def encode(self, sentences, **kwargs):
            assert sentences == ["bail"]
            return np.array([[1,0]], dtype=np.float32)
    monkeypatch.setattr("retrieval.dense.SentenceTransformerEncoder", FakeEncoder)
    DenseIndex.build(_records(), np.array([[1,0],[0,1],[1,1]], dtype=np.float32)).save(tmp_path)
    assert DenseRetriever(tmp_path).retrieve("bail", top_k=1)[0].chunk_id == "c1"
