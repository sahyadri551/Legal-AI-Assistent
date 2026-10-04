# Milestone 6: Reciprocal Rank Fusion

RRF combines BM25 and dense rankings without comparing their raw scores. Each ranked result contributes 1/(rrf_k + rank). Default rrf_k is 60.

## Query
    $env:PYTHONPATH="$PWD\src"
    python -m retrieval.rrf_cli "bail under section 439" --top-k 8

## Model cache
The embedding model is cached locally in .modal_cache/. The directory is git-ignored, so the first build downloads the model and later builds reuse it.
