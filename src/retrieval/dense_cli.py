"""Build or query the dense FAISS index."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from retrieval.dense import DenseRetriever,build_dense_index
def main()->None:
 p=argparse.ArgumentParser(); s=p.add_subparsers(dest="command",required=True)
 b=s.add_parser("build"); b.add_argument("--chunks",type=Path,default=Path("data/processed/chunks.jsonl")); b.add_argument("--output",type=Path,default=Path("data/indexes/faiss")); b.add_argument("--model",default="BAAI/bge-small-en-v1.5"); b.add_argument("--device",default="cpu"); b.add_argument("--batch-size",type=int,default=8); b.add_argument("--cache-dir",type=Path,default=Path(".modal_cache"))
 q=s.add_parser("search"); q.add_argument("query"); q.add_argument("--index",type=Path,default=Path("data/indexes/faiss")); q.add_argument("--model",default="BAAI/bge-small-en-v1.5"); q.add_argument("--device",default="cpu"); q.add_argument("--top-k",type=int,default=8); q.add_argument("--cache-dir",type=Path,default=Path(".modal_cache"))
 a=p.parse_args()
 if a.command=="build": r=build_dense_index(a.chunks,a.output,a.model,a.device,a.batch_size,a.cache_dir)
 else: r=[x.__dict__ for x in DenseRetriever(a.index,a.model,a.device,a.cache_dir).retrieve(a.query,a.top_k)]
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
