"""Query BM25 + dense retrieval with Reciprocal Rank Fusion."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from retrieval.bm25 import BM25Retriever
from retrieval.dense import DenseRetriever
from retrieval.rrf import reciprocal_rank_fusion
def main()->None:
 p=argparse.ArgumentParser(); p.add_argument("query"); p.add_argument("--bm25-index",type=Path,default=Path("data/indexes/bm25")); p.add_argument("--dense-index",type=Path,default=Path("data/indexes/faiss")); p.add_argument("--model",default="BAAI/bge-small-en-v1.5"); p.add_argument("--device",default="cpu"); p.add_argument("--cache-dir",type=Path,default=Path(".modal_cache")); p.add_argument("--retrieval-k",type=int,default=50); p.add_argument("--rrf-k",type=int,default=60); p.add_argument("--top-k",type=int,default=8)
 a=p.parse_args(); s=BM25Retriever(a.bm25_index).retrieve(a.query,a.retrieval_k); d=DenseRetriever(a.dense_index,a.model,a.device,a.cache_dir).retrieve(a.query,a.retrieval_k)
 print(json.dumps([x.__dict__ for x in reciprocal_rank_fusion(s,d,a.rrf_k,a.top_k)],ensure_ascii=False,indent=2))
if __name__=="__main__": main()
