"""Build or query the dense FAISS index."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from retrieval.dense import DenseRetriever, build_dense_index

def main() -> None:
    parser = argparse.ArgumentParser(description="Build/query the legal dense FAISS index.")
    subs = parser.add_subparsers(dest="command", required=True)
    build = subs.add_parser("build")
    build.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
    build.add_argument("--output", type=Path, default=Path("data/indexes/faiss"))
    build.add_argument("--model", default="BAAI/bge-small-en-v1.5")
    build.add_argument("--device", default="cpu")
    build.add_argument("--batch-size", type=int, default=8)
    search = subs.add_parser("search")
    search.add_argument("query")
    search.add_argument("--index", type=Path, default=Path("data/indexes/faiss"))
    search.add_argument("--model", default="BAAI/bge-small-en-v1.5")
    search.add_argument("--device", default="cpu")
    search.add_argument("--top-k", type=int, default=8)
    args = parser.parse_args()
    if args.command == "build":
        result = build_dense_index(args.chunks, args.output, args.model, args.device, args.batch_size)
    else:
        result = [r.__dict__ for r in DenseRetriever(args.index, args.model, args.device).retrieve(args.query, args.top_k)]
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
