import numpy as np
import pytest
from retrieval.rrf import reciprocal_rank_fusion
from retrieval.bm25 import BM25Result
from retrieval.dense import DenseResult
def b(c,r): return BM25Result(c,c,c,1.0,r,{})
def d(c,r): return DenseResult(c,c,c,1.0,r,{})
def test_rrf_overlap():
 out=reciprocal_rank_fusion([b("a",1),b("b",2)],[d("b",1),d("c",2)],60,3)
 assert out[0].chunk_id=="b" and out[0].bm25_rank==2 and out[0].dense_rank==1
 assert [x.chunk_id for x in out]==["b","a","c"]
def test_rrf_invalid():
 with pytest.raises(ValueError): reciprocal_rank_fusion([],[],0,8)
 with pytest.raises(ValueError): reciprocal_rank_fusion([],[],60,0)
