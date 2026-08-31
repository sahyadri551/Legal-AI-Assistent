# Indian Legal Research Assistant (Hybrid RAG)

CPU-first research prototype: hybrid BM25 + dense retrieval, Reciprocal Rank Fusion, FastAPI, Streamlit, and Ollama (`qwen3:4b`). Embeddings use `BAAI/bge-small-en-v1.5` on CPU. There is no local LoRA/QLoRA training.

This repository currently contains **directory layout and configuration only**. Application code, indexes, and corpora are not included yet.

## Layout

| Path | Role |
|------|------|
| `configs/` | Default, retrieval, generation, and evaluation settings |
| `src/backend/` | FastAPI (to be implemented) |
| `src/frontend/` | Streamlit (to be implemented) |
| `src/ingestion/` | Document load and chunking (to be implemented) |
| `src/retrieval/` | BM25, FAISS, RRF (to be implemented) |
| `src/generation/` | Ollama client (to be implemented) |
| `src/evaluation/` | Baseline comparison harness (to be implemented) |
| `data/raw/` | User-supplied source documents only (empty) |
| `data/processed/` | Chunks and metadata produced by ingestion |
| `data/indexes/` | BM25 and FAISS artifacts |
| `experiments/runs/` | Evaluation outputs |
| `docs/architecture.md` | Retrieval–generation pipeline sketch |

## Constraints

- Run embeddings and serving on CPU; do not assume a discrete GPU.
- Generate with a running Ollama server; do not load the chat model in-process.
- Do not add training stacks, CUDA wheels, or orchestration frameworks unless a later step requires them.
- Do not commit corpora, embeddings, or invented legal content.

## Local setup (later)

1. Copy `.env.example` to `.env`.
2. Create a virtual environment and install `requirements.txt`.
3. Pull the Ollama model named in `configs/generation.yaml` on this machine.
4. Place licensed or otherwise authorized source files in `data/raw/` when ingestion is implemented.

## Research question

Whether hybrid BM25 + dense retrieval with RRF improves retrieval and answer quality versus BM25-only and dense-only baselines for Indian legal question answering, with generation held fixed.
