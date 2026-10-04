import json
from pathlib import Path

from frontend.sessions import DEFAULT_TITLE, SessionStore, make_title


def turn(query="What is bail?"):
    return {"query": query, "answer": "A.", "citations": [], "retrieved_chunks": [], "model": "m"}


def test_make_title_collapses_and_truncates():
    assert make_title("  a \n b  ") == "a b"
    assert make_title("") == DEFAULT_TITLE
    assert len(make_title("x" * 200)) == 48


def test_new_session_reuses_empty_one(tmp_path: Path):
    store = SessionStore(tmp_path / "s.json")
    first = store.new_session()
    assert store.new_session() == first
    assert len(store.sessions) == 1


def test_add_turn_sets_title_and_persists(tmp_path: Path):
    path = tmp_path / "data" / "s.json"
    store = SessionStore(path)
    sid = store.new_session()
    store.add_turn(sid, turn("What is anticipatory bail?"))

    reloaded = SessionStore(path)
    session = reloaded.get(sid)
    assert session["title"] == "What is anticipatory bail?"
    assert len(session["turns"]) == 1
    assert reloaded.initial_active_id() == sid


def test_multiple_sessions_order_and_switch(tmp_path: Path):
    store = SessionStore(tmp_path / "s.json")
    a = store.new_session()
    store.add_turn(a, turn("first"))
    b = store.new_session()
    assert b != a
    store.add_turn(b, turn("second"))
    assert [s["id"] for s in store.ordered()] == [b, a]
    store.add_turn(a, turn("again"))
    assert store.ordered()[0]["id"] == a


def test_delete_returns_fallback_and_never_leaves_zero(tmp_path: Path):
    store = SessionStore(tmp_path / "s.json")
    a = store.new_session()
    store.add_turn(a, turn())
    b = store.new_session()
    store.add_turn(b, turn("two"))
    assert store.delete(b) == a
    fresh = store.delete(a)
    assert store.get(fresh) is not None and store.get(a) is None


def test_clear_resets_title(tmp_path: Path):
    store = SessionStore(tmp_path / "s.json")
    sid = store.new_session()
    store.add_turn(sid, turn())
    store.clear(sid)
    assert store.get(sid)["turns"] == [] and store.get(sid)["title"] == DEFAULT_TITLE


def test_theme_persists_and_rejects_unknown(tmp_path: Path):
    path = tmp_path / "s.json"
    store = SessionStore(path)
    store.set_theme("dark")
    store.set_theme("neon")
    assert SessionStore(path).theme == "dark"


def test_corrupt_file_is_backed_up_not_fatal(tmp_path: Path):
    path = tmp_path / "s.json"
    path.write_text("{not json", encoding="utf-8")
    store = SessionStore(path)
    assert store.sessions == [] and store.load_error
    assert (tmp_path / "s.json.bak").exists()
    assert store.initial_active_id()


def test_invalid_entries_are_skipped(tmp_path: Path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"sessions": [{"id": 1}, "x", {"id": "ok", "turns": []}]}), encoding="utf-8")
    assert [s["id"] for s in SessionStore(path).sessions] == ["ok"]


def test_export_text(tmp_path: Path):
    store = SessionStore(tmp_path / "s.json")
    sid = store.new_session()
    store.add_turn(sid, turn("Q1"))
    assert store.export_text(sid) == "Q: Q1\nA: A."
