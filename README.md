# Indian Legal Research Assistant (Hybrid RAG)

CPU-first research prototype for Indian legal research using hybrid BM25 + dense retrieval, Reciprocal Rank Fusion, FastAPI, Streamlit, and Ollama (qwen3:4b). Embeddings use BAAI/bge-small-en-v1.5 on CPU. There is no local LoRA/QLoRA training.

## Current implementation

The ingestion stage now:
1. matches judgment PDFs to metadata by integer pair ID;
2. validates missing/duplicate/unreadable inputs;
3. extracts PDF text with pypdf;
4. writes normalized records to data/processed/documents.jsonl;
5. chunks normalized text into data/processed/chunks.jsonl.

No legal corpus, embeddings, or index artifacts are committed.

## Commands

From the repository root:

    python -m ingestion --project-root .

    python -m ingestion.chunking_cli --project-root .

The first command builds documents.jsonl. The second builds chunks.jsonl using the defaults in configs/retrieval.yaml (1200 characters with 150-character overlap).

## Layout

| Path | Role |
|------|------|
| configs/ | Application and retrieval/generation/evaluation settings |
| src/ingestion/ | Document matching, PDF extraction, normalization, and chunking |
| src/retrieval/ | BM25, FAISS, and RRF (later milestone) |
| src/generation/ | Ollama client (later milestone) |
| src/backend/ | FastAPI (later milestone) |
| src/frontend/ | Streamlit (later milestone) |
| src/evaluation/ | Evaluation harness (later milestone) |
| data/raw/ | User-supplied source documents |
| data/processed/ | Generated documents and chunks |
| data/indexes/ | Generated BM25 and FAISS artifacts |
| experiments/runs/ | Evaluation outputs |

## Constraints

- Run embeddings and serving on CPU.
- Generate with a running Ollama server; do not load chat-model weights in-process.
- Do not commit corpora, embeddings, or invented legal content.

## Research question

Whether hybrid BM25 + dense retrieval with RRF improves retrieval and answer quality versus BM25-only and dense-only baselines for Indian legal question answering, with generation held fixed.
