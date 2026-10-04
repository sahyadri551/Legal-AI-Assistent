"""Persistent chat sessions and UI preferences, kept in one small JSON file.

The file is the source of truth: the app builds a ``SessionStore`` on every
Streamlit rerun, so hot reloads and multiple browser tabs always agree. Which
session is open in a given tab lives in ``st.session_state``, not here.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

DEFAULT_TITLE = "New session"
TITLE_LIMIT = 48
FORMAT_VERSION = 1
THEMES = ("light", "dark")


def make_title(query: str) -> str:
    text = " ".join(query.split())
    if not text:
        return DEFAULT_TITLE
    return text if len(text) <= TITLE_LIMIT else text[: TITLE_LIMIT - 1].rstrip() + "…"


def _valid_session(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("id"), str)
        and isinstance(value.get("turns"), list)
    )


class SessionStore:
    def __init__(self, path: Path | str = Path("data/sessions.json")) -> None:
        self.path = Path(path)
        self.sessions: list[dict[str, Any]] = []
        self.theme = "light"
        self.last_active: str | None = None
        self.load_error: str | None = None
        self.save_error: str | None = None
        self._load()

    # ------------------------------------------------------------ persistence
    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("root must be a JSON object")
        except (OSError, ValueError) as exc:
            self.load_error = f"Could not read {self.path}: {exc}"
            try:
                self.path.replace(self.path.with_name(self.path.name + ".bak"))
            except OSError:
                pass
            return

        for raw in payload.get("sessions", []):
            if not _valid_session(raw):
                continue
            now = time.time()
            self.sessions.append(
                {
                    "id": raw["id"],
                    "title": str(raw.get("title") or DEFAULT_TITLE),
                    "created": float(raw.get("created") or now),
                    "updated": float(raw.get("updated") or now),
                    "turns": [t for t in raw["turns"] if isinstance(t, dict)],
                }
            )
        if payload.get("theme") in THEMES:
            self.theme = payload["theme"]
        last = payload.get("last_active")
        self.last_active = last if isinstance(last, str) else None

    def save(self) -> None:
        payload = {
            "format_version": FORMAT_VERSION,
            "theme": self.theme,
            "last_active": self.last_active,
            "sessions": self.sessions,
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_name(self.path.name + ".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.path)
            self.save_error = None
        except OSError as exc:
            self.save_error = f"Could not save {self.path}: {exc}"

    # ---------------------------------------------------------------- queries
    def ordered(self) -> list[dict[str, Any]]:
        """Sessions, most recently used first."""
        return sorted(self.sessions, key=lambda s: s["updated"], reverse=True)

    def get(self, session_id: str | None) -> dict[str, Any] | None:
        for session in self.sessions:
            if session["id"] == session_id:
                return session
        return None

    def initial_active_id(self) -> str:
        """Session to open on a fresh page load."""
        if self.get(self.last_active) is not None:
            return str(self.last_active)
        if self.sessions:
            return self.ordered()[0]["id"]
        return self.new_session()

    def export_text(self, session_id: str) -> str:
        session = self.get(session_id)
        if session is None:
            return ""
        return "\n\n".join(
            f"Q: {turn.get('query', '')}\nA: {turn.get('answer', '')}"
            for turn in session["turns"]
        )

    # -------------------------------------------------------------- mutations
    def new_session(self) -> str:
        """Create a session, or reuse an empty one instead of piling up blanks."""
        for session in self.sessions:
            if not session["turns"]:
                session["updated"] = time.time()
                self.last_active = session["id"]
                self.save()
                return session["id"]
        now = time.time()
        session = {
            "id": uuid.uuid4().hex[:8],
            "title": DEFAULT_TITLE,
            "created": now,
            "updated": now,
            "turns": [],
        }
        self.sessions.append(session)
        self.last_active = session["id"]
        self.save()
        return session["id"]

    def remember_active(self, session_id: str) -> None:
        if self.get(session_id) is not None and self.last_active != session_id:
            self.last_active = session_id
            self.save()

    def add_turn(self, session_id: str, turn: dict[str, Any]) -> None:
        session = self.get(session_id)
        if session is None:
            raise KeyError(f"unknown session {session_id!r}")
        session["turns"].append(turn)
        if session["title"] == DEFAULT_TITLE:
            session["title"] = make_title(str(turn.get("query", "")))
        session["updated"] = time.time()
        self.last_active = session_id
        self.save()

    def clear(self, session_id: str) -> None:
        session = self.get(session_id)
        if session is None:
            return
        session["turns"] = []
        session["title"] = DEFAULT_TITLE
        session["updated"] = time.time()
        self.save()

    def delete(self, session_id: str) -> str:
        """Delete a session; returns the id the UI should fall back to."""
        self.sessions = [s for s in self.sessions if s["id"] != session_id]
        if self.last_active == session_id:
            self.last_active = None
        if not self.sessions:
            return self.new_session()
        self.save()
        return self.ordered()[0]["id"]

    def set_theme(self, theme: str) -> None:
        if theme in THEMES and theme != self.theme:
            self.theme = theme
            self.save()
