"""Professional legal research workspace built with Streamlit."""
from __future__ import annotations

import os

import streamlit as st

from frontend.client import BackendError, LegalQAClient


st.set_page_config(
    page_title="LexAssist AI",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
  --navy:#0f172a; --navy2:#111c31; --blue:#2563eb; --blue2:#1d4ed8;
  --slate:#64748b; --border:#dbe2ea; --soft:#f8fafc; --white:#ffffff;
  --green:#16a34a; --purple:#7c3aed; --amber:#d97706;
}
.stApp { background:#f8fafc; color:#1e293b; }
[data-testid="stHeader"] { background:#ffffff; }
[data-testid="stDeployButton"],
div.stDeployButton,
.stDeployButton {
  display:none !important;
  visibility:hidden !important;
}
[data-testid="stToolbar"] {
  display:none !important;
  visibility:hidden !important;
}
[data-testid="stSidebar"] { background:var(--navy); border-right:1px solid #1e293b; }
[data-testid="stSidebar"] .block-container { padding:1.25rem .9rem; }
.block-container {
  max-width:1440px;
  margin:0 auto;
  padding:0 24px 110px;
}
section.main > div { padding-left:0; padding-right:0; }
[data-testid="stMainBlockContainer"] { max-width:1440px; margin:0 auto; }
[data-testid="stHorizontalBlock"] { align-items:stretch; }
#MainMenu, footer { visibility:hidden; }

.brand {
  display:flex; align-items:center; gap:10px; padding:.25rem .4rem 1.2rem;
  border-bottom:1px solid rgba(148,163,184,.18); margin-bottom:1rem;
}
.brand-mark {
  width:34px;height:34px;border-radius:9px;display:grid;place-items:center;
  background:#1d4ed8;color:#fff;font-size:17px;
}
.brand-name { color:#fff;font:700 17px Georgia,serif; letter-spacing:.2px; }
.brand-sub { color:#94a3b8;font-size:10px;margin-top:2px; }

.side-label {
  color:#64748b;font-size:10px;font-weight:700;letter-spacing:1.3px;
  text-transform:uppercase;margin:.9rem .5rem .35rem;
}
.side-item {
  color:#94a3b8;padding:.55rem .65rem;border-radius:8px;font-size:12px;margin:2px 0;
}
.side-item.active { background:rgba(37,99,235,.25);color:#dbeafe; }
.side-item .ico { display:inline-block;width:20px;color:#60a5fa; }
.side-note { color:#94a3b8;font-size:10px;line-height:1.5;padding:.4rem .5rem; }

.topbar {
  width:100%;
  max-width:1180px;
  height:64px;
  margin:0 auto;
  background:#fff;
  border-bottom:1px solid var(--border);
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:0 24px;
}
.top-title { font-size:17px;font-weight:700;color:#1e293b; }
.top-sub { font-size:10px;color:#64748b;margin-top:2px; }
.online {
  display:inline-flex;align-items:center;gap:7px;background:#f1f5f9;border:1px solid #e2e8f0;
  border-radius:999px;padding:5px 10px;color:#475569;font-size:10px;font-weight:600;
}
.dot { width:7px;height:7px;border-radius:50%;background:#22c55e; }

.workspace { display:grid;grid-template-columns:minmax(0,1fr) 340px;min-height:calc(100vh - 64px); }
.chat-pane { display:flex;flex-direction:column;min-width:0; }
.chat-scroll {
  width:100%;
  max-width:980px;
  margin:0 auto;
  padding:24px 20px 90px;
  box-sizing:border-box;
}
.empty {
  min-height:calc(100vh - 330px);
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  text-align:center;
  margin:0 auto;
  padding:0 16px;
}
.scale {
  width:62px;height:62px;border-radius:50%;display:grid;place-items:center;
  background:#dbeafe;color:#2563eb;font-size:25px;margin-bottom:14px;
}
.empty h2 { font:700 22px Georgia,serif;color:#1e293b;margin:0 0 8px; }
.empty p { max-width:520px;color:#64748b;font-size:12px;line-height:1.6;margin:0 0 20px; }

.suggestion {
  border:1px solid var(--border);background:#fff;border-radius:12px;padding:12px;
  text-align:left;color:#334155;font-size:12px;min-height:72px;
}
.suggestion:hover { border-color:#93c5fd;background:#eff6ff; }
[data-testid="stButton"] button {
  border-radius:11px;
  min-height:44px;
  border:1px solid var(--border);
  background:#fff;
  color:#334155;
  font-size:12px;
  font-weight:600;
}
[data-testid="stButton"] button:hover {
  border-color:#93c5fd;
  background:#eff6ff;
}
[class*="st-key-suggestion_"] button {
  min-height:72px;
  text-align:left;
  white-space:pre-line;
  line-height:1.45;
  padding:12px 16px;
}

.msg { display:flex;width:100%;margin-bottom:20px; }
.msg.user { justify-content:flex-end; }
.msg.ai { justify-content:flex-start; }
.bubble {
  max-width:82%;padding:14px 17px;border-radius:16px;font-size:13px;line-height:1.65;
  box-shadow:0 1px 2px rgba(15,23,42,.05);
}
.user .bubble { background:#2563eb;color:#fff;border-top-right-radius:4px; }
.ai .bubble { background:#fff;border:1px solid var(--border);color:#334155;border-top-left-radius:4px; }
.avatar {
  width:30px;height:30px;border-radius:8px;display:grid;place-items:center;
  flex:0 0 auto;margin-top:2px;font-size:12px;
}
.user .avatar { background:#1d4ed8;color:#fff;margin-left:9px; }
.ai .avatar { background:#0f172a;color:#fff;margin-right:9px; }
.ai-content p { margin:0 0 .7rem; }
.ai-content p:last-child { margin-bottom:0; }
.source-tag {
  display:inline-block;padding:2px 6px;border-radius:5px;background:#e2e8f0;color:#475569;
  font:600 10px ui-monospace,SFMono-Regular,Menlo,monospace;
}
.msg-actions { border-top:1px solid #eef2f7;margin-top:10px;padding-top:8px;display:flex;gap:12px; }
.msg-actions span { color:#94a3b8;font-size:10px; }

.composer-wrap { display:none; }
[data-testid="stChatInput"] {
  width:min(900px, calc(100vw - 48px));
  margin:0 auto;
}
[data-testid="stChatInput"] textarea {
  min-height:48px !important;
  max-height:48px !important;
  overflow:hidden !important;
  resize:none !important;
}
[data-testid="stChatInput"] > div {
  border-radius:16px;
  border:1px solid #cbd5e1;
  box-shadow:0 4px 18px rgba(15,23,42,.08);
  background:#fff;
}
[data-testid="stBottom"] {
  background:rgba(248,250,252,.96);
  backdrop-filter:blur(10px);
  border-top:1px solid var(--border);
  padding:10px 0 12px;
}
[data-testid="stBottom"] [data-testid="stHorizontalBlock"] {
  max-width:900px;
  margin:0 auto;
}

.context {
  background:#fff;
  border-left:1px solid var(--border);
  min-height:calc(100vh - 64px);
  display:flex;
  flex-direction:column;
}
.context-head { height:56px;border-bottom:1px solid #eef2f7;background:#f8fafc;padding:0 16px;display:flex;align-items:center; }
.context-title { font-size:12px;font-weight:700;color:#475569; }
.context-empty { color:#94a3b8;font-size:11px;text-align:center;padding:55px 22px;line-height:1.6; }
.source-card { background:#fff;border:1px solid var(--border);border-radius:9px;padding:10px;margin:10px 14px; }
.source-title { color:#334155;font-size:11px;font-weight:700;line-height:1.4; }
.source-text { color:#64748b;font:10px/1.55 Georgia,serif;margin-top:6px; }
.source-meta { display:flex;justify-content:space-between;border-top:1px solid #f1f5f9;margin-top:8px;padding-top:7px;color:#94a3b8;font-size:9px; }
.badge { padding:2px 6px;border-radius:5px;font-size:8px;font-weight:700; }
.badge-hybrid { background:#dcfce7;color:#15803d; }

.citations {
  margin-top:10px;padding:10px 12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:9px;
}
.citation { display:inline-block;margin:3px 4px 3px 0;padding:4px 7px;border-radius:5px;background:#e0ecff;color:#1d4ed8;font:9px ui-monospace,SFMono-Regular,Menlo,monospace; }

@media (max-width:1100px) {
  .context { border-left:0;border-top:1px solid var(--border); }
  .block-container { padding-left:16px; padding-right:16px; }
  .topbar { padding:0 8px; }
}
@media (max-width:700px) {
  .chat-scroll { padding-left:8px; padding-right:8px; }
  .bubble { max-width:92%; }
  .suggestion { min-height:58px; }
  [data-testid="stChatInput"] { width:calc(100vw - 24px); }
  .top-title { font-size:15px; }
  .top-sub { display:none; }
}
</style>
""",
    unsafe_allow_html=True,
)


def clear_session() -> None:
    st.session_state.history = []
    st.session_state.result = None
    st.session_state.error = None


def render_sidebar(backend_online: bool) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
              <div class="brand-mark">⚖</div>
              <div><div class="brand-name">LexAssist AI</div><div class="brand-sub">Indian legal intelligence</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="side-label">Workspaces</div>', unsafe_allow_html=True)
        st.markdown('<div class="side-item active"><span class="ico">◉</span> Legal Research QA</div>', unsafe_allow_html=True)
        st.markdown('<div class="side-item"><span class="ico">▣</span> Document Analysis</div>', unsafe_allow_html=True)
        st.markdown('<div class="side-item"><span class="ico">⌕</span> Case Law Search</div>', unsafe_allow_html=True)

        st.markdown('<div class="side-label">Recent Sessions</div>', unsafe_allow_html=True)
        history = st.session_state.get("history", [])
        if history:
            for item in history[-5:][::-1]:
                label = item["query"].replace("\n", " ")[:30]
                st.markdown(f'<div class="side-item">◌ {label}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="side-note">Your recent research questions will appear here.</div>', unsafe_allow_html=True)

        st.markdown('<div class="side-label">System</div>', unsafe_allow_html=True)
        status = "Online" if backend_online else "Offline"
        color = "#22c55e" if backend_online else "#ef4444"
        st.markdown(
            f'<div class="side-item"><span style="color:{color}">●</span> Backend {status}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="side-label">Session</div>', unsafe_allow_html=True)
        st.checkbox("Include citations", key="include_citations")
        export_text = "\n\n".join(
            f"Q: {item['query']}\nA: {item['answer']}" for item in history
        )
        if st.button("Clear context", use_container_width=True):
            clear_session()
            st.rerun()
        st.download_button(
            "Export session",
            data=export_text or "No research session yet.",
            file_name="legal_research_session.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.markdown('<div class="side-note">Research assistant only. Verify important legal conclusions against primary sources and qualified legal counsel.</div>', unsafe_allow_html=True)


def render_topbar(backend_online: bool) -> None:
    status = "System Online" if backend_online else "System Offline"
    dot = "#22c55e" if backend_online else "#ef4444"
    st.markdown(
        f"""
        <div class="topbar">
          <div>
            <div class="top-title">Legal Research QA</div>
            <div class="top-sub">Pipeline: Hybrid Retrieval (BM25 + Dense via RRF)</div>
          </div>
          <div class="online"><span class="dot" style="background:{dot}"></span>{status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_user_message(query: str) -> None:
    st.markdown(
        f"""
        <div class="msg user">
          <div class="bubble">{query.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</div>
          <div class="avatar">You</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_message(answer: str, citations: list[str]) -> None:
    st.markdown('<div class="msg ai"><div class="avatar">⚖</div><div class="bubble"><div class="ai-content">', unsafe_allow_html=True)
    st.markdown(answer)
    if citations:
        tags = "".join(f'<span class="source-tag">{c}</span> ' for c in citations)
        st.markdown(f'<div style="margin-top:10px">{tags}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="msg-actions"><span>▣ Copy answer</span><span>↗ Evidence</span></div></div></div>',
        unsafe_allow_html=True,
    )


def render_context(result) -> None:
    with st.expander("▤  Retrieval Context", expanded=True):
        if not result:
            st.markdown(
                '<div class="context-empty">Sources used for generation will appear here.</div>',
                unsafe_allow_html=True,
            )
            return

        for index, chunk in enumerate(result.retrieved_chunks, start=1):
            chunk_id = chunk.get("chunk_id", "Unknown source")
            text = chunk.get("text", "")
            metadata = chunk.get("metadata") or {}
            score = metadata.get("score", metadata.get("rrf_score", "—"))

            st.markdown(
                f'''
                <div class="source-card">
                  <div class="source-title">
                    <span style="color:#94a3b8">{index:02d}</span> &nbsp;{chunk_id}
                  </div>
                  <div style="margin-top:5px">
                    <span class="badge badge-hybrid">RRF</span>
                  </div>
                  <div class="source-text">
                    "{text[:360]}{"..." if len(text) > 360 else ""}"
                  </div>
                  <div class="source-meta">
                    <span>Relevance: {score}</span>
                    <span>Hybrid retrieval</span>
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

            with st.expander(f"View source {index:02d}", expanded=False):
                st.write(text)
                if metadata:
                    st.json(metadata)


if "history" not in st.session_state:
    st.session_state.history = []
if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "include_citations" not in st.session_state:
    st.session_state.include_citations = True

api_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
client = LegalQAClient(api_url)

try:
    backend_online = client.health()
except BackendError:
    backend_online = False

render_sidebar(backend_online)
render_topbar(backend_online)

left, right = st.columns([1, 0.34], gap="medium", vertical_alignment="top")

with left:
    if not st.session_state.history:
        st.markdown(
            """
            <div class="empty">
              <div class="scale">⚖</div>
              <h2>How can I assist your research today?</h2>
              <p>Ask legal questions against your ingested Indian legal corpus. Hybrid BM25 + dense retrieval is used to surface evidence before generation.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        suggestions = [
            ("What is bail?", "Definition and core bail provisions"),
            ("What are the powers of the High Court regarding bail?", "Relevant statutory and case-law evidence"),
            ("What is the difference between regular and anticipatory bail?", "Compare the two bail mechanisms"),
            ("Explain the retrieved provisions in simple terms.", "Evidence-grounded explanation"),
        ]
        cols = st.columns(2, gap="small")
        for idx, (title, subtitle) in enumerate(suggestions):
            with cols[idx % 2]:
                if st.button(f"{title}\n{subtitle}", key=f"suggestion_{idx}", use_container_width=True):
                    st.session_state.pending_query = title
                    st.rerun()
    else:
        st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
        for item in st.session_state.history:
            render_user_message(item["query"])
            render_ai_message(item["answer"], item.get("citations", []))
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.error:
        st.error(st.session_state.error)

with right:
    render_context(st.session_state.result)

prompt = st.chat_input(
    "Ask a legal question or request document analysis...",
    max_chars=2000,
)
pending_query = st.session_state.pop("pending_query", None)
prompt = prompt or pending_query

if prompt:
    query = prompt.strip()
    if not query:
        st.session_state.error = "Please enter a legal question."
        st.rerun()
    if not backend_online:
        st.session_state.error = "The FastAPI backend is offline. Start it before asking a question."
        st.rerun()

    st.session_state.error = None
    with st.spinner("Retrieving evidence and generating answer..."):
        try:
            result = client.ask(query)
        except (BackendError, ValueError) as exc:
            st.session_state.error = str(exc)
            st.rerun()

    citations = result.citations if st.session_state.include_citations else []
    st.session_state.history.append(
        {
            "query": query,
            "answer": result.answer,
            "citations": citations,
            "retrieved_chunks": result.retrieved_chunks,
            "model": result.model,
        }
    )
    st.session_state.result = result
    st.rerun()

st.markdown(
    '<div style="text-align:center;color:#94a3b8;font-size:9px;padding:8px">LexAssist AI · Indian Legal Research Assistant · Hybrid BM25 + Dense Retrieval · Grounded Generation</div>',
    unsafe_allow_html=True,
)
