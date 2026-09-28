"""Run: python -m ingestion.chunking_cli --project-root <repo>."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingestion.chunking import chunk_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk normalized legal documents.")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--overlap-chars", type=int, default=150)
    args = parser.parse_args()

    root = args.project_root.resolve()
    input_path = args.input or root / "data" / "processed" / "documents.jsonl"
    output_path = args.output or root / "data" / "processed" / "chunks.jsonl"

    report = chunk_documents(
        input_path=input_path,
        output_path=output_path,
        max_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
