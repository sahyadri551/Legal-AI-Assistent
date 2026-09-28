from pathlib import Path

import ingestion.pdf_text as pdf_text


class _Page:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _Reader:
    def __init__(self, _path: str) -> None:
        self.pages = [_Page("first page"), _Page(""), _Page("second page")]


def test_extract_pdf_text_preserves_page_order(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pdf_text, "PdfReader", _Reader)
    path = tmp_path / "sample.pdf"
    path.write_bytes(b"%PDF-fake")

    assert pdf_text.extract_pdf_text(path) == "first page\n\nsecond page"
