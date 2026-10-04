# Architecture

Legal corpus
  ↓
Normalization + metadata
  ↓
Deterministic chunking
  ├───────────────┐
  ↓               ↓
BM25          BGE-small-en-v1.5
  ↓               ↓
  │             FAISS
  └─────── RRF ───┘
          ↓
     Top-K evidence
          ↓
    Groq GPT-OSS 120B
          ↓
  Grounded answer + citations

Generation is delegated to Groq because local Ollama generation overloaded the available CPU/RAM on the development machine. BM25, embeddings, FAISS, and RRF remain local.

The application exposes three workspaces:

- Legal Research QA — hybrid retrieval followed by grounded generation.
- Document Analysis — temporary PDF upload, page extraction, and Groq analysis grounded only in that uploaded document. Uploaded documents are not added to the corpus or indexes.
- Case Law Search — hybrid retrieval restricted to judgment:* records.
