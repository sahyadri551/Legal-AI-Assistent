# Reciprocal Rank Fusion

Reciprocal Rank Fusion combines BM25 and dense retrieval rankings without comparing their raw scores. Each ranked result contributes 1 / (rrf_k + rank); the default rrf_k is 60.

## Query

    $env:PYTHONPATH="$PWD\src"
    python -m retrieval.rrf_cli "bail under section 439" --top-k 8

## Embedding model cache

The sentence-transformers embedding model is cached locally. Set HF_HOME to change the cache directory. The first run may download the model; later runs reuse the cached files.
