"""Pure helpers that turn backend data into safe, readable UI text.

Everything that ends up inside raw HTML goes through ``esc`` first. Legal text
and LLM output regularly contain ``<``, ``&`` and quotes, which would otherwise
break the layout (or inject markup).
"""
from __future__ import annotations

import html
import re
from typing import Any

SOURCE_RE = re.compile(r"\[SOURCE:\s*([^\]]+?)\s*\]")


def esc(value: object) -> str:
    """HTML-escape any value for use inside raw HTML."""
    return html.escape(str(value), quote=True)


def source_label(chunk_id: str) -> str:
    """Turn ``judgment:12:3`` / ``statute:BNS:5`` into a human-readable label."""
    parts = str(chunk_id).strip().split(":")
    if len(parts) == 3 and parts[2].isdigit():
        kind, ident, chunk = parts
        if kind == "judgment":
            return f"Judgment {ident} · chunk {chunk}"
        if kind == "statute":
            return f"{ident} · chunk {chunk}"
    return str(chunk_id).strip()


def _tags(ids: str) -> str:
    labels = [part.strip() for part in re.split(r"[;,]", ids) if part.strip()]
    return " ".join(f'<span class="source-tag">{esc(source_label(label))}</span>' for label in labels)


def prepare_answer(answer: str, show_citations: bool = True) -> str:
    """Escape model output, then turn ``[SOURCE: id]`` markers into tags.

    The result is markdown with a few trusted inline ``<span>`` elements, so it
    must be rendered with ``unsafe_allow_html=True``. All model-provided text is
    escaped before the trusted spans are added.
    """
    text = html.escape(answer, quote=False)
    if show_citations:
        return SOURCE_RE.sub(lambda m: _tags(m.group(1)), text)
    return re.sub(r"[ \t]{2,}", " ", SOURCE_RE.sub("", text)).strip()


def user_text(query: str) -> str:
    """Escape a user's question for a chat bubble, preserving line breaks."""
    return esc(query).replace("\n", "<br>")


def first_line(text: str | None, limit: int = 110) -> str:
    """First non-empty line of ``text``, shortened to ``limit`` characters."""
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"
    return ""


def shorten(text: str, limit: int = 320) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def source_badges(chunk: dict[str, Any], cited: bool) -> str:
    """Badges showing how a chunk was found (BM25 rank, dense rank, RRF score)."""
    badges: list[str] = []
    if cited:
        badges.append('<span class="badge cited">Cited in answer</span>')
    if chunk.get("bm25_rank") is not None:
        badges.append(f'<span class="badge bm25">BM25 #{esc(chunk["bm25_rank"])}</span>')
    if chunk.get("dense_rank") is not None:
        badges.append(f'<span class="badge dense">Dense #{esc(chunk["dense_rank"])}</span>')
    score = chunk.get("score")
    if isinstance(score, (int, float)):
        badges.append(f'<span class="badge rrf">RRF {score:.4f}</span>')
    return "".join(badges)


_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|>~:$])")


def md_escape(text: str) -> str:
    """Backslash-escape markdown/directive characters (for button labels)."""
    return _MD_SPECIAL.sub(r"\\\1", " ".join(str(text).split()))


def initials(name: str) -> str:
    """Up to two initials for an avatar circle."""
    letters = [word[0] for word in name.split() if word[:1].isalnum()]
    return "".join(letters[:2]).upper() or "U"
