# Dense retrieval

Milestone 5 builds a CPU FAISS IndexFlatIP index from data/processed/chunks.jsonl.

## Build

    $env:PYTHONPATH="src"
    python -m retrieval.dense_cli build

The first build downloads BAAI/bge-small-en-v1.5 through sentence-transformers. Generated FAISS artifacts are written to data/indexes/faiss/ and are ignored by git.

## Query

    $env:PYTHONPATH="src"
    python -m retrieval.dense_cli search "bail under section 439" --top-k 8

## Design

- BAAI/bge-small-en-v1.5 is the configured embedding model.
- Embeddings are generated on CPU.
- Embeddings are L2-normalized before indexing.
- FAISS IndexFlatIP therefore provides cosine-similarity ranking.
- Original chunk records are persisted beside the FAISS index.
