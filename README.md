# Indian Legal Research Assistant (Hybrid RAG)

CPU-first legal research application using hybrid BM25 + dense retrieval, Reciprocal Rank Fusion, FastAPI, Streamlit, and Groq GPT-OSS 120B. Embeddings use BAAI/bge-small-en-v1.5 on CPU. There is no local LoRA/QLoRA training.

## Application

The application provides PDF ingestion, normalization, deterministic chunking, BM25 and dense retrieval with Reciprocal Rank Fusion, grounded Groq generation, FastAPI endpoints, browser voice typing, temporary PDF document analysis, case-law search, citations, and retrieved-source inspection.

No legal corpus, embeddings, or index artifacts are committed.

## Run

Install dependencies:

    pip install -e ".[dev]"

Set GROQ_API_KEY in .env. GROQ_MODEL defaults to openai/gpt-oss-120b.

Start the backend:

    $env:PYTHONPATH="$PWD\src"
    uvicorn backend.app:app --host 127.0.0.1 --port 8000

In a second PowerShell window, start the frontend:

    $env:PYTHONPATH="$PWD\src"
    streamlit run src/frontend/app.py --server.port 8501

Open the Streamlit URL shown by the command, normally http://localhost:8501.

The frontend calls the FastAPI backend at http://127.0.0.1:8000 by default. Set BACKEND_URL to use another backend URL.

## API

Health: GET /health

Legal QA: POST /qa with {"query": "What are the powers of the High Court regarding bail?"}

The response includes the generated answer, model name, citation IDs, and retrieved chunks used for generation.

## Data pipeline

From the repository root:

    python -m ingestion --project-root .
    python -m ingestion.chunking_cli --project-root .

Build the BM25 and FAISS indexes using the retrieval CLIs after the processed corpus exists.

## Test

    pytest -q

## Layout

| Path | Role |
|------|------|
| configs/ | Application and retrieval/generation/evaluation settings |
| src/ingestion/ | Document matching, PDF extraction, normalization, and chunking |
| src/retrieval/ | BM25, FAISS, and RRF |
| src/generation/ | Groq grounded generation |
| src/backend/ | FastAPI application and QA service |
| src/frontend/ | Streamlit UI and backend client |
| src/evaluation/ | Evaluation harness |
| data/raw/ | User-supplied source documents |
| data/processed/ | Generated documents and chunks |
| data/indexes/ | Generated BM25 and FAISS artifacts |
| experiments/runs/ | Evaluation outputs |

## Constraints

- Run embeddings and serving on CPU.
- Generate through Groq; do not load chat-model weights in-process.
- Browser voice typing uses the Web Speech API when supported; speech is transcribed into the existing chat input and is never auto-submitted.
- Document Analysis accepts temporary PDFs and does not add them to the indexed legal corpus.
- Case Law Search filters retrieval to judgment records.
- Do not commit corpora, embeddings, or invented legal content.

## Research question

Whether hybrid BM25 + dense retrieval with RRF improves retrieval and answer quality versus BM25-only and dense-only baselines for Indian legal question answering, with generation held fixed.
