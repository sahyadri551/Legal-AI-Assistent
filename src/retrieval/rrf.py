"""Reciprocal Rank Fusion for BM25 and dense retrieval."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from retrieval.bm25 import BM25Result
from retrieval.dense import DenseResult
@dataclass(frozen=True)
class RRFResult:
    chunk_id:str; doc_id:str; text:str; score:float; bm25_rank:int|None; dense_rank:int|None; metadata:dict[str,Any]
def reciprocal_rank_fusion(bm25_results:list[BM25Result],dense_results:list[DenseResult],rrf_k:int=60,top_k:int=8)->list[RRFResult]:
    if rrf_k<=0 or top_k<=0: raise ValueError("rrf_k and top_k must be greater than zero")
    merged={}
    for source,results,rank_key in [("bm25",bm25_results,"bm25_rank"),("dense",dense_results,"dense_rank")]:
        for r in results:
            x=merged.setdefault(r.chunk_id,{"r":r,"score":0.0,"bm25_rank":None,"dense_rank":None})
            x["score"]+=1.0/(rrf_k+r.rank); x[rank_key]=r.rank
    ranked=sorted(merged.values(),key=lambda x:(-x["score"],x["r"].chunk_id))[:top_k]
    return [RRFResult(x["r"].chunk_id,x["r"].doc_id,x["r"].text,x["score"],x["bm25_rank"],x["dense_rank"],x["r"].metadata) for x in ranked]
