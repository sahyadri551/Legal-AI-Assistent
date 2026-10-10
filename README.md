# LexAssist AI

Legal research workspace for Indian legal materials. The application uses React, Redux Toolkit, Tailwind CSS, FastAPI, hybrid BM25 + FAISS retrieval, Reciprocal Rank Fusion (RRF), and Groq for grounded answer generation.

## Requirements

- Python 3.12
- Node.js 20 or newer
- A Groq API key

## Setup

From the repository root, create and activate a virtual environment and install the backend:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -e ".[dev]"
    Copy-Item .env.example .env

Set GROQ_API_KEY in .env.

Install frontend dependencies:

    cd web
    npm install
    cd ..

## Run locally

Terminal 1 — backend, from the repository root:

    $env:PYTHONPATH="$PWD\src"
    uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

Terminal 2 — frontend, from the repository root:

    cd web
    npm run dev

Open http://localhost:5173. The frontend uses http://127.0.0.1:8000 by default. Set VITE_API_URL in web/.env.local to override it.

## Features

- Legal question answering with retrieved evidence and citations
- Case-law search with retrieval-score visualization
- PDF text extraction and document analysis
- Voice input where supported by the browser
- Research sessions, export, pinning, rename, and deletion
- Persistent light and dark themes

## API

- GET /health — backend health
- POST /qa — grounded legal question answering
- POST /search — hybrid case-law search
- POST /document-analysis — analyze an uploaded PDF

## Tests

From the repository root:

    pytest -q

Build the frontend:

    cd web
    npm run build

## Architecture

- src/ingestion/ — PDF extraction, normalization, and chunking
- src/retrieval/ — BM25, FAISS dense retrieval, and RRF
- src/generation/groq.py — Groq answer generation
- src/backend/ — FastAPI endpoints and QA service
- web/src/ — React application, Redux state, API client, and styles
- data/indexes/ — BM25 and FAISS retrieval indexes

Embeddings run on CPU. Chat generation uses the Groq API; no local chat-model weights are required. Keep API keys in environment variables and never commit secrets.
