User

&#x20;↓

Query preprocessing

&#x20;↓

&#x20;┌───────────────┬────────────────┐

&#x20;│                   │                     │

BM25              Embedding             Metadata

&#x20;│                   │

&#x20;│                 FAISS

&#x20;│                   │

&#x20;└───────┬───────┘

&#x20;          ↓

&#x20;  Reciprocal Rank Fusion

&#x20;        ↓

&#x20;   Top-K chunks

&#x20;        ↓

&#x20;    Qwen3 4B

&#x20;        ↓

Answer + citations

