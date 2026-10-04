from frontend.formatting import (
    first_line,
    prepare_answer,
    shorten,
    source_badges,
    source_label,
    user_text,
)


def test_source_label_is_readable():
    assert source_label("judgment:12:3") == "Judgment 12 · chunk 3"
    assert source_label("statute:BNS:5") == "BNS · chunk 5"
    assert source_label("c1") == "c1"


def test_prepare_answer_turns_markers_into_tags():
    out = prepare_answer("Bail is covered. [SOURCE: judgment:1:0]")
    assert '<span class="source-tag">Judgment 1 · chunk 0</span>' in out
    assert "[SOURCE" not in out


def test_prepare_answer_splits_multiple_ids():
    out = prepare_answer("See [SOURCE: statute:BNS:1, judgment:2:4].")
    assert out.count('class="source-tag"') == 2


def test_prepare_answer_escapes_model_html():
    out = prepare_answer("<script>alert(1)</script> a < b & c")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_prepare_answer_can_hide_citations():
    out = prepare_answer("Claim [SOURCE: c1] stands.", show_citations=False)
    assert "SOURCE" not in out and "source-tag" not in out
    assert out == "Claim stands."


def test_user_text_escapes_and_keeps_newlines():
    assert user_text("a <b>\nc") == "a &lt;b&gt;<br>c"


def test_first_line_and_shorten():
    assert first_line("\n\n  REPORTABLE  \nnext") == "REPORTABLE"
    assert first_line(None) == ""
    assert len(first_line("x" * 300, limit=50)) == 50
    assert shorten("a   b\n c", 100) == "a b c"
    assert shorten("word " * 100, 20).endswith("…")


def test_source_badges():
    chunk = {"bm25_rank": 2, "dense_rank": None, "score": 0.0328}
    out = source_badges(chunk, cited=True)
    assert "BM25 #2" in out and "Cited in answer" in out and "RRF 0.0328" in out
    assert "Dense" not in out