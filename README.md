# Indian Legal Research Assistant (Hybrid RAG)

CPU-first research prototype for Indian legal research using hybrid BM25 + dense retrieval, Reciprocal Rank Fusion, FastAPI, Streamlit, and Groq. Embeddings use BAAI/bge-small-en-v1.5 on CPU. There is no local LoRA/QLoRA training.

## Application

The application provides PDF ingestion, normalization, deterministic chunking, BM25 and dense retrieval with Reciprocal Rank Fusion, grounded Groq generation, FastAPI endpoints, and a Streamlit frontend for questions, answers, citations, and retrieved sources.

BM25 and FAISS retrieval index artifacts required by the deployed backend are committed under `data/indexes/`.

## Run

Install dependencies:

    pip install -e ".[dev]"

Set `GROQ_API_KEY` in your local `.env`.

Start the backend:

    $env:PYTHONPATH="$PWD\src"
    uvicorn backend.app:app --host 127.0.0.1 --port 8000

In a second PowerShell window, start the frontend:

    $env:PYTHONPATH="$PWD\src"
    streamlit run src/frontend/app.py --server.port 8501

Open the Streamlit URL shown by the command, normally http://localhost:8501.

The frontend calls `BACKEND_URL`, defaulting to http://127.0.0.1:8000.

## API

Health: GET /health

Legal QA: POST /qa with {"query": "What are the powers of the High Court regarding bail?"}

Case-law search: POST /search with {"query": "Section 302 IPC"}

Document analysis: POST /document-analysis with a PDF file and query.

The QA response includes the generated answer, model name, citation IDs, and retrieved chunks used for generation.

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
| configs/ | Application, retrieval, generation, and evaluation settings |
| src/ingestion/ | Document matching, PDF extraction, normalization, and chunking |
| src/retrieval/ | BM25, FAISS, and RRF |
| src/generation/ | Groq grounded generation |
| src/backend/ | FastAPI application and QA service |
| src/frontend/ | Streamlit UI and backend client |
| src/evaluation/ | Evaluation harness |
| data/raw/ | User-supplied source documents |
| data/processed/ | Generated documents and chunks |
| data/indexes/ | BM25 and FAISS artifacts |
| experiments/runs/ | Evaluation outputs |

## Constraints

- Run embeddings and serving on CPU.
- Generate through the Groq API; do not load chat-model weights in-process.
- Do not commit raw corpora or invented legal content.

## Research question

Whether hybrid BM25 + dense retrieval with RRF improves retrieval and answer quality versus BM25-only and dense-only baselines for Indian legal question answering, with generation held fixed.

## Render deployment

Render is the deployment target for both application services:

- `legal-ai-backend`: FastAPI, BM25 + FAISS + Groq.
- `legal-ai-frontend`: Streamlit UI.

The repository includes `render.yaml` as a Render Blueprint. It wires the frontend's `BACKEND_URL` to the backend's Render URL and the backend's `FRONTEND_ORIGINS` to the frontend's Render URL.

### Backend

Build command:

    pip install -r requirements.txt

Start command:

    PYTHONPATH=src uvicorn backend.app:app --host 0.0.0.0 --port $PORT

Health check:

    /health

Required secret:

    GROQ_API_KEY=<your Groq API key>

The backend Blueprint uses the Free plan (0.1 CPU / 512 MB RAM). The dense-retrieval stack loads PyTorch and the embedding model, so the backend may hit the Free plan memory limit; if that happens, the deployment requires a lighter embedding architecture or a paid backend.

### Frontend

Build command:

    pip install -r requirements.txt

Start command:

    streamlit run src/frontend/app.py --server.address 0.0.0.0 --server.port $PORT

`BACKEND_URL` is supplied automatically by the Blueprint.

### Render setup

1. Push the repository to GitHub.
2. In Render, create a new Blueprint and select this repository.
3. Approve the two services defined in `render.yaml`.
4. Enter `GROQ_API_KEY` when Render prompts for the secret.
5. Deploy both services.
6. Open the Streamlit frontend URL and verify the backend status is online.

Render supports Python web services with a pip build command and a host/port-bound start command. The service must listen on `0.0.0.0` and Render supplies the `PORT` value.

### UptimeRobot

Render Free web services can spin down after 15 minutes without inbound traffic. Use UptimeRobot to monitor the backend health endpoint:

    https://<backend-service>.onrender.com/health

Recommended monitor type: HTTPS.

The UptimeRobot Free plan checks every 5 minutes. Monitoring the backend can keep it receiving traffic, but Render grants 750 Free instance hours per workspace per month. Keep the monitor on the backend only; do not also keep the frontend continuously awake. UptimeRobot does not prevent Render from restarting a service.

Keep the Groq API key only in Render Environment Variables; never commit it.
