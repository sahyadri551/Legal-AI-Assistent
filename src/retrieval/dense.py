"""Dense embedding and FAISS retrieval."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
import faiss
import numpy as np
class Encoder(Protocol):
    def encode(self, sentences: list[str], **kwargs: Any) -> np.ndarray: ...
@dataclass(frozen=True)
class DenseResult:
    chunk_id: str; doc_id: str; text: str; score: float; rank: int; metadata: dict[str, Any]
class SentenceTransformerEncoder:
    def __init__(self, model_name: str, device: str = "cpu", cache_dir: Path | None = None) -> None:
        if device != "cpu": raise ValueError("Milestone 5 is CPU-only; device must be 'cpu'")
        from sentence_transformers import SentenceTransformer
        self.cache_dir=(cache_dir or Path(".modal_cache")).resolve(); self.cache_dir.mkdir(parents=True,exist_ok=True)
        self.model=SentenceTransformer(model_name,device="cpu",cache_folder=str(self.cache_dir))
    def encode(self,sentences:list[str],**kwargs:Any)->np.ndarray:
        return np.asarray(self.model.encode(sentences,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False,**kwargs),dtype=np.float32)
class DenseIndex:
    FORMAT_VERSION=1
    def __init__(self,index:faiss.Index,records:list[dict[str,Any]],model_name:str|None=None)->None:
        if index.ntotal!=len(records): raise ValueError("FAISS index and records must have equal length")
        self.index=index; self.records=records; self.model_name=model_name
    @classmethod
    def build(cls,records:list[dict[str,Any]],embeddings:np.ndarray,model_name:str|None=None)->"DenseIndex":
        if not records: raise ValueError("cannot build dense index from empty corpus")
        v=_prepare_embeddings(embeddings,len(records)); idx=faiss.IndexFlatIP(v.shape[1]); idx.add(v); return cls(idx,records,model_name)
    def save(self,out:Path)->None:
        out.mkdir(parents=True,exist_ok=True); faiss.write_index(self.index,str(out/"index.faiss"))
        (out/"records.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in self.records),encoding="utf-8")
        (out/"manifest.json").write_text(json.dumps({"format_version":1,"index_type":"IndexFlatIP","dimension":self.index.d,"chunks":len(self.records),"documents":len({r["doc_id"] for r in self.records}),"embedding_model":self.model_name},indent=2),encoding="utf-8")
    @classmethod
    def load(cls,out:Path,expected_model_name:str|None=None)->"DenseIndex":
        m=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
        if m.get("format_version")!=1: raise ValueError("unsupported dense index format")
        stored_model=m.get("embedding_model")
        if expected_model_name is not None and stored_model != expected_model_name: raise ValueError("Dense index embedding model mismatch; rebuild data/indexes/faiss using " + expected_model_name)
        idx=faiss.read_index(str(out/"index.faiss")); records=[json.loads(x) for x in (out/"records.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        if m.get("dimension") != idx.d: raise ValueError("dense index manifest dimension does not match FAISS index")
        return cls(idx,records,stored_model)
    def search(self,q:np.ndarray,top_k:int=8)->list[DenseResult]:
        if top_k<=0: raise ValueError("top_k must be greater than zero")
        scores,ids=self.index.search(_prepare_embeddings(q,1),min(top_k,len(self.records))); out=[]
        for rank,(score,i) in enumerate(zip(scores[0],ids[0]),1):
            if i<0: continue
            r=self.records[int(i)]; meta={k:v for k,v in r.items() if k not in {"chunk_id","doc_id","text"}}
            out.append(DenseResult(str(r["chunk_id"]),str(r["doc_id"]),str(r.get("text") or ""),float(score),rank,meta))
        return out
def _prepare_embeddings(e:np.ndarray,n:int)->np.ndarray:
    v=np.asarray(e,dtype=np.float32)
    if v.ndim==1: v=v.reshape(1,-1)
    if v.ndim!=2 or v.shape[0]!=n: raise ValueError("embeddings must be a 2D array with the expected number of rows")
    norms=np.linalg.norm(v,axis=1,keepdims=True)
    if np.any(norms==0): raise ValueError("embeddings must not contain zero vectors")
    return v/norms
def _load_chunk_records(p:Path)->list[dict[str,Any]]:
    out=[]
    for no,line in enumerate(p.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        r=json.loads(line)
        for f in ("chunk_id","doc_id","text"):
            if f not in r: raise ValueError(f"missing required field {f!r} on line {no}")
        out.append(r)
    return out
def build_dense_index(chunks_path:Path,output_dir:Path,model_name:str="BAAI/bge-small-en-v1.5",device:str="cpu",batch_size:int=8,cache_dir:Path|None=None)->dict[str,int|str]:
    if batch_size<=0: raise ValueError("batch_size must be greater than zero")
    records=_load_chunk_records(chunks_path)
    if not records: raise ValueError("cannot build dense index from empty corpus")
    print(f"Loading embedding model: {model_name}")
    encoder=SentenceTransformerEncoder(model_name,device,cache_dir)
    texts=[str(r.get("text") or "") for r in records]; total=len(texts)
    print(f"Model loaded. Encoding {total} chunks in batches of {batch_size}...")
    batches=[]
    for start in range(0,total,batch_size):
        batches.append(encoder.encode(texts[start:start+batch_size]))
        print(f"Batch {min(start+batch_size,total)}/{total}")
    print("Building FAISS index...")
    idx=DenseIndex.build(records,np.vstack(batches),model_name=model_name)
    print("Saving index..."); idx.save(output_dir); print("Done.")
    return {"chunks":len(records),"documents":len({r["doc_id"] for r in records}),"dimension":idx.index.d,"model":model_name,"device":device,"output_dir":str(output_dir)}
class DenseRetriever:
    def __init__(self,index_dir:Path,model_name:str="BAAI/bge-small-en-v1.5",device:str="cpu",cache_dir:Path|None=None)->None:
        self.encoder=SentenceTransformerEncoder(model_name,device,cache_dir)
        self.index=DenseIndex.load(index_dir,expected_model_name=model_name)
    def retrieve(self,query:str,top_k:int=8)->list[DenseResult]:
        if not query.strip(): return []
        return self.index.search(self.encoder.encode([query]),top_k)
