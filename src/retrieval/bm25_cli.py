"""Build or query the BM25 index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from retrieval.bm25 import BM25Retriever, build_bm25_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/query the legal BM25 index.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--chunks", type=Path, default=Path("data/processed/chunks.jsonl"))
    build.add_argument("--output", type=Path, default=Path("data/indexes/bm25"))

    search = subparsers.add_parser("search")
    search.add_argument("query")
    search.add_argument("--index", type=Path, default=Path("data/indexes/bm25"))
    search.add_argument("--top-k", type=int, default=8)

    args = parser.parse_args()
    if args.command == "build":
        print(json.dumps(build_bm25_index(args.chunks, args.output), indent=2))
    else:
        results = BM25Retriever(args.index).retrieve(args.query, args.top_k)
        print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
