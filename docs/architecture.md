## Request flow

1. The React frontend sends a question to the FastAPI backend.
2. BM25 and FAISS dense retrieval run in parallel.
3. Reciprocal Rank Fusion combines the rankings.
4. The top passages are sent to Groq for grounded answer generation.
5. The API returns the answer, citations, and retrieved passages.

## Components

- Frontend: React, Redux Toolkit, Tailwind CSS, Vite
- API: FastAPI
- Sparse retrieval: BM25
- Dense retrieval: BAAI/bge-small-en-v1.5 embeddings with FAISS, running on CPU
- Ranking fusion: Reciprocal Rank Fusion
- Answer generation: Groq API

Chat-model weights are not loaded locally. The backend requires GROQ_API_KEY for answer generation.
