"""Professional Streamlit UI for the Indian Legal Research Assistant."""
from __future__ import annotations

import os

import streamlit as st

from frontend.client import BackendError, LegalQAClient


st.set_page_config(
    page_title="Legal Research Assistant",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --navy: #0b1220;
        --navy-2: #111a2d;
        --panel: #121c2f;
        --panel-2: #17233a;
        --line: #263552;
        --text: #eef3fb;
        --muted: #91a0b8;
        --accent: #6d8cff;
        --accent-2: #8d6df7;
        --success: #35c98a;
        --danger: #ff6b78;
    }

    .stApp {
        background:
            radial-gradient(circle at 80% 0%, rgba(109, 140, 255, 0.12), transparent 32rem),
            radial-gradient(circle at 10% 25%, rgba(141, 109, 247, 0.08), transparent 28rem),
            var(--navy);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: #09101d;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.2rem;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2.4rem;
    }

    .brand-mark {
        width: 42px;
        height: 42px;
        display: grid;
        place-items: center;
        border-radius: 12px;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        color: white;
        font-size: 22px;
        box-shadow: 0 10px 30px rgba(109, 140, 255, 0.25);
    }

    .brand-name {
        color: var(--text);
        font-size: 17px;
        font-weight: 700;
        letter-spacing: -0.2px;
    }

    .brand-subtitle {
        color: var(--muted);
        font-size: 12px;
        margin-top: 2px;
    }

    .eyebrow {
        color: #9baeff;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.6px;
        text-transform: uppercase;
        margin-bottom: 0.7rem;
    }

    .hero-title {
        color: var(--text);
        font-size: clamp(2.2rem, 5vw, 4.2rem);
        line-height: 1.02;
        letter-spacing: -2.8px;
        font-weight: 800;
        max-width: 820px;
        margin: 0;
    }

    .hero-copy {
        color: var(--muted);
        font-size: 16px;
        line-height: 1.65;
        max-width: 700px;
        margin: 1rem 0 1.7rem;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid rgba(53, 201, 138, 0.25);
        background: rgba(53, 201, 138, 0.08);
        color: #8ee5be;
        border-radius: 999px;
        padding: 7px 11px;
        font-size: 12px;
        font-weight: 650;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--success);
        box-shadow: 0 0 0 4px rgba(53, 201, 138, 0.1);
    }

    .status-pill.offline {
        border-color: rgba(255, 107, 120, 0.25);
        background: rgba(255, 107, 120, 0.08);
        color: #ffadb5;
    }

    .status-pill.offline .status-dot {
        background: var(--danger);
        box-shadow: 0 0 0 4px rgba(255, 107, 120, 0.1);
    }

    .section-label {
        color: #c5d0e3;
        font-size: 13px;
        font-weight: 700;
        margin: 0 0 0.55rem;
    }

    .query-shell {
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(23, 35, 58, 0.96), rgba(18, 28, 47, 0.96));
        border-radius: 18px;
        padding: 1.2rem;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
    }

    .hint {
        color: var(--muted);
        font-size: 12px;
        margin-top: 0.65rem;
    }

    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 1rem;
        margin: 2.4rem 0 1rem;
    }

    .result-title {
        color: var(--text);
        font-size: 22px;
        font-weight: 750;
        letter-spacing: -0.5px;
        margin: 0;
    }

    .result-subtitle {
        color: var(--muted);
        font-size: 12px;
        margin-top: 4px;
    }

    .answer-card {
        border: 1px solid var(--line);
        background: rgba(18, 28, 47, 0.92);
        border-radius: 18px;
        padding: 1.4rem 1.5rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        border: 1px solid var(--line);
        background: rgba(18, 28, 47, 0.76);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        min-height: 84px;
    }

    .metric-label {
        color: var(--muted);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
    }

    .metric-value {
        color: var(--text);
        font-size: 18px;
        font-weight: 750;
        margin-top: 5px;
        overflow-wrap: anywhere;
    }

    .citation-pill {
        display: inline-block;
        border: 1px solid #304365;
        background: #16243c;
        color: #aebfff;
        border-radius: 999px;
        padding: 6px 10px;
        margin: 3px 5px 3px 0;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 11px;
    }

    .source-count {
        color: var(--muted);
        font-size: 12px;
    }

    div[data-testid="stTextArea"] textarea {
        background: #0d1627;
        color: var(--text);
        border: 1px solid #2a3a5b;
        border-radius: 13px;
        min-height: 118px;
        font-size: 15px;
        line-height: 1.55;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 1px var(--accent);
    }

    div.stButton > button {
        border-radius: 11px;
        min-height: 46px;
        font-weight: 700;
        border: 1px solid #32476e;
        background: #182743;
        color: #eaf0fb;
        transition: all 0.15s ease;
    }

    div.stButton > button:hover {
        border-color: #6d8cff;
        color: white;
        background: #203252;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #647fff, #8068ef);
        border: 0;
        color: white;
        box-shadow: 0 12px 28px rgba(109, 140, 255, 0.2);
    }

    div.stButton > button[kind="primary"]:hover {
        filter: brightness(1.08);
        box-shadow: 0 14px 34px rgba(109, 140, 255, 0.28);
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 13px;
        background: rgba(18, 28, 47, 0.62);
    }

    .sidebar-title {
        color: var(--text);
        font-size: 12px;
        font-weight: 750;
        letter-spacing: 1.1px;
        text-transform: uppercase;
        margin: 1.6rem 0 0.65rem;
    }

    .sidebar-copy {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.55;
    }

    .sidebar-feature {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        color: #c6d0e1;
        font-size: 12px;
        line-height: 1.45;
        margin: 0.75rem 0;
    }

    .sidebar-feature b {
        color: #eef3fb;
    }

    .footer {
        color: #62718a;
        border-top: 1px solid var(--line);
        margin-top: 3rem;
        padding-top: 1rem;
        font-size: 11px;
        text-align: center;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_metric(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if "query" not in st.session_state:
    st.session_state.query = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">⚖</div>
            <div>
                <div class="brand-name">Legal Research AI</div>
                <div class="brand-subtitle">Indian legal intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-title">Backend</div>', unsafe_allow_html=True)
    api_url = st.text_input(
        "Backend URL",
        value=os.getenv("BACKEND_URL", "http://127.0.0.1:8000"),
        label_visibility="collapsed",
    )
    client = LegalQAClient(api_url)

    try:
        backend_online = client.health()
    except BackendError:
        backend_online = False

    if backend_online:
        st.markdown(
            '<div class="status-pill"><span class="status-dot"></span>Backend connected</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-pill offline"><span class="status-dot"></span>Backend offline</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="sidebar-title">How it works</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sidebar-feature"><span>01</span><span><b>Retrieve</b><br>BM25 + dense semantic search.</span></div>
        <div class="sidebar-feature"><span>02</span><span><b>Fuse</b><br>Reciprocal Rank Fusion selects the strongest evidence.</span></div>
        <div class="sidebar-feature"><span>03</span><span><b>Ground</b><br>Ollama generates an answer from retrieved excerpts.</span></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-title">Important</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-copy">This is a research assistant, not a substitute for advice from a qualified legal professional.</div>',
        unsafe_allow_html=True,
    )


st.markdown('<div class="eyebrow">AI-powered legal research</div>', unsafe_allow_html=True)
st.markdown(
    '<h1 class="hero-title">Find the law.<br>Understand the evidence.</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero-copy">Ask questions about the Indian legal corpus and receive grounded answers backed by the retrieved source excerpts.</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="query-shell">', unsafe_allow_html=True)
st.markdown('<div class="section-label">What do you want to research?</div>', unsafe_allow_html=True)

quick_prompts = [
    "What is bail?",
    "What are the powers of the High Court regarding bail?",
    "What is the difference between regular and anticipatory bail?",
]

prompt_columns = st.columns(3)
for column, prompt in zip(prompt_columns, quick_prompts):
    with column:
        if st.button(prompt, use_container_width=True, key=f"prompt_{prompt}"):
            st.session_state.query = prompt

st.text_area(
    "Legal question",
    key="query",
    placeholder="Ask a focused legal question...",
    label_visibility="collapsed",
)
st.markdown(
    '<div class="hint">Tip: specific questions produce more focused retrieval and easier-to-audit citations.</div>',
    unsafe_allow_html=True,
)

ask = st.button("Search legal corpus  →", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if ask:
    if not st.session_state.query.strip():
        st.session_state.error = "Please enter a legal question."
        st.session_state.result = None
    elif not backend_online:
        st.session_state.error = "The FastAPI backend is offline. Start it before asking a question."
        st.session_state.result = None
    else:
        st.session_state.error = None
        with st.spinner("Searching the legal corpus and generating a grounded answer..."):
            try:
                st.session_state.result = client.ask(st.session_state.query)
            except (BackendError, ValueError) as exc:
                st.session_state.error = str(exc)
                st.session_state.result = None

if st.session_state.error:
    st.error(st.session_state.error)

result = st.session_state.result
if result:
    st.markdown(
        """
        <div class="result-header">
            <div>
                <div class="result-title">Research result</div>
                <div class="result-subtitle">Generated from the retrieved legal evidence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_columns = st.columns(3)
    with metric_columns[0]:
        render_metric("Generation model", result.model)
    with metric_columns[1]:
        render_metric("Citations", str(len(result.citations)))
    with metric_columns[2]:
        render_metric("Retrieved sources", str(len(result.retrieved_chunks)))

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="answer-card">', unsafe_allow_html=True)
    st.markdown("### Answer")
    st.markdown(result.answer)
    st.markdown("</div>", unsafe_allow_html=True)

    if result.citations:
        st.markdown("#### Evidence cited")
        citation_html = "".join(
            f'<span class="citation-pill">{citation}</span>'
            for citation in result.citations
        )
        st.markdown(citation_html, unsafe_allow_html=True)

    if result.retrieved_chunks:
        st.markdown(
            f"#### Retrieved evidence <span class='source-count'>· {len(result.retrieved_chunks)} sources</span>",
            unsafe_allow_html=True,
        )
        for index, chunk in enumerate(result.retrieved_chunks, start=1):
            chunk_id = chunk.get("chunk_id", "Unknown source")
            with st.expander(f"{index:02d}  ·  {chunk_id}"):
                st.markdown(chunk.get("text", ""))
                metadata = chunk.get("metadata") or {}
                if metadata:
                    st.caption("Source metadata")
                    st.json(metadata)

st.markdown(
    """
    <div class="footer">
        Indian Legal Research Assistant · Hybrid BM25 + dense retrieval · Grounded Ollama generation
    </div>
    """,
    unsafe_allow_html=True,
)
