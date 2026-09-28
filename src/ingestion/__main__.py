"""Run: python -m ingestion --project-root <repo>"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingestion.pipeline import run_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize raw judgments and statutes into documents.jsonl."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (contains data/ and configs/).",
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=None,
        help="Override data/raw directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override documents.jsonl path.",
    )
    args = parser.parse_args()
    report = run_ingestion(
        project_root=args.project_root,
        raw_root=args.raw_root,
        output_path=args.output,
    )
    print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
