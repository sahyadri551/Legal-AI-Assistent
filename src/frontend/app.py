"""LexAssist AI: legal research workspace (Streamlit)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from frontend.client import BackendError, LegalQAClient
from frontend.formatting import (
    esc,
    first_line,
    initials,
    md_escape,
    prepare_answer,
    source_badges,
    source_label,
    user_text,
)
from frontend.icons import icon
from frontend.sessions import THEMES, SessionStore
from frontend.theme import build_css

st.set_page_config(
    page_title="LexAssist AI",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded",
)

STORE_PATH = Path(os.getenv("SESSIONS_PATH", "data/sessions.json"))
USER_NAME = os.getenv("LEXASSIST_USER", "Legal Researcher")
USER_ROLE = os.getenv("LEXASSIST_ROLE", "Local workspace")
MAX_SIDEBAR_SESSIONS = 12
LS_THEME_KEY = "lexassist_theme"
LS_SESSION_KEY = "lexassist_active_id"

SUGGESTIONS = [
    ("What is bail?", "Definition and core bail provisions"),
    (
        "What are the powers of the High Court regarding bail?",
        "Relevant statutory and case-law evidence",
    ),
    (
        "What is the difference between regular and anticipatory bail?",
        "Compare the two bail mechanisms",
    ),
    ("Explain the retrieved provisions in simple terms.", "Evidence-grounded explanation"),
]


# ---------------------------------------------------------- backend cache
@st.cache_resource(show_spinner=False)
def _get_store(path: Path) -> SessionStore:
    """Load the session store once per server process and reuse it."""
    return SessionStore(path)


# ------------------------------------------------------- client-side cache
def _bootstrap_from_local_storage() -> None:
    """Load session from local storage to prevent default theme flash."""
    if st.session_state.get("_ls_bootstrapped"):
        return
    st.session_state._ls_bootstrapped = True

    if st.query_params.get("theme") or st.query_params.get("sid"):
        return

    components.html(
        f"""
        <script>
        (function() {{
            try {{
                const theme = localStorage.getItem({json.dumps(LS_THEME_KEY)});
                const sid = localStorage.getItem({json.dumps(LS_SESSION_KEY)});
                if (!theme && !sid) {{ return; }}
                const url = new URL(window.parent.location.href);
                if (theme) url.searchParams.set("theme", theme);
                if (sid) url.searchParams.set("sid", sid);
                window.parent.location.replace(url.toString());
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
    )


def _sync_client_cache(theme: str, active_id: str) -> None:
    """Mirror the active theme/session into the URL and localStorage."""
    st.query_params["theme"] = theme
    st.query_params["sid"] = active_id
    components.html(
        f"""
        <script>
        try {{
            localStorage.setItem({json.dumps(LS_THEME_KEY)}, {json.dumps(theme)});
            localStorage.setItem({json.dumps(LS_SESSION_KEY)}, {json.dumps(active_id)});
        }} catch (e) {{}}
        </script>
        """,
        height=0,
    )


# ------------------------------------------------------------------ state
store = _get_store(STORE_PATH)
_bootstrap_from_local_storage()

for key, default in (
    ("error", None),
    ("pending_query", None),
    ("include_citations", True),
    ("scroll_pending", False),
):
    if key not in st.session_state:
        st.session_state[key] = default

if "theme" not in st.session_state:
    qp_theme = st.query_params.get("theme")
    st.session_state.theme = qp_theme if qp_theme in THEMES else store.theme

if store.get(st.session_state.get("active_id")) is None:
    qp_sid = st.query_params.get("sid")
    if qp_sid and store.get(qp_sid) is not None:
        st.session_state.active_id = qp_sid
    else:
        st.session_state.active_id = store.initial_active_id()

active_id: str = st.session_state.active_id
_sync_client_cache(st.session_state.theme, active_id)
st.markdown(build_css(st.session_state.theme), unsafe_allow_html=True)


# --------------------------------------------------------------- sidebar
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f'<div class="brand">{icon("scale", 22)}<span class="brand-name">LexAssist AI</span></div>'
            '<div class="side-label">Workspaces</div>'
            f'<div class="nav-item active">{icon("comments")}<span>Legal Research QA</span></div>'
            f'<div class="nav-item" title="Coming soon">{icon("file")}<span>Document Analysis</span></div>'
            f'<div class="nav-item" title="Coming soon">{icon("search")}<span>Case Law Search</span></div>'
            '<div class="side-label">Recent Sessions</div>',
            unsafe_allow_html=True,
        )

        with st.container(key="newsession"):
            if st.button(":material/add: New session", key="new_session", use_container_width=True):
                st.session_state.active_id = store.new_session()
                st.session_state.error = None
                st.rerun()

        for session in store.ordered()[:MAX_SIDEBAR_SESSIONS]:
            sid = session["id"]
            is_active = sid == active_id
            with st.container(key=f"srow_{sid}"):
                open_col, delete_col = st.columns([8, 1.4], gap="small", vertical_alignment="center")
                with open_col:
                    if st.button(
                        f":material/chat_bubble_outline: {md_escape(session['title'])}",
                        key=f"sess_active_{sid}" if is_active else f"sess_{sid}",
                        use_container_width=True,
                        help=session["title"],
                    ):
                        st.session_state.active_id = sid
                        st.session_state.error = None
                        store.remember_active(sid)
                        st.rerun()
                with delete_col:
                    if st.button(":material/close:", key=f"sessdel_{sid}", help="Delete this session"):
                        fallback = store.delete(sid)
                        if is_active:
                            st.session_state.active_id = fallback
                            st.session_state.error = None
                        st.rerun()

        with st.container(key="userbox"):
            st.markdown(
                f'<div class="userbox"><div class="avatar">{esc(initials(USER_NAME))}</div>'
                f'<div><div class="name">{esc(USER_NAME)}</div>'
                f'<div class="role">{esc(USER_ROLE)}</div></div></div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------- top bar
def render_topbar(backend_online: bool) -> None:
    color = "#22c55e" if backend_online else "#ef4444"
    status = "System Online" if backend_online else "Backend offline"
    dark = st.session_state.theme == "dark"

    with st.container(key="topbar"):
        # The CSS overrides Streamlit's default flexbox spacing so it respects content widths
        title_col, status_col, cite_col, menu_col = st.columns(
            [3.2, 1.4, 2.0, 0.65], gap="small", vertical_alignment="center"
        )
        title_col.markdown(
            '<div class="top-title">Legal Research QA</div>'
            '<div class="top-sub">Pipeline: Hybrid Retrieval (BM25 + Dense via RRF)</div>',
            unsafe_allow_html=True,
        )
        status_col.markdown(
            '<div class="pill-wrap"><span class="status-pill">'
            f'<span class="status-dot" style="background:{color}"></span>{status}</span></div>',
            unsafe_allow_html=True,
        )
        with cite_col:
            st.checkbox(
                "Include Citations",
                key="include_citations",
                help="Show [SOURCE: ...] citation tags inline in answers",
            )
        with menu_col:
            with st.popover("⋮", help="More actions"):
                if st.button(
                    ":material/dark_mode: Toggle theme" if dark else ":material/light_mode: Toggle theme",
                    key="hdr_theme",
                    use_container_width=True,
                ):
                    st.session_state.theme = "light" if dark else "dark"
                    store.set_theme(st.session_state.theme)
                    st.query_params["theme"] = st.session_state.theme
                    st.rerun()
                
                if st.button(":material/delete_sweep: Clear chat", key="hdr_clear", use_container_width=True):
                    store.clear(active_id)
                    st.session_state.error = None
                    st.rerun()
                    
                st.download_button(
                    ":material/download: Export session",
                    data=store.export_text(active_id) or "No research session yet.",
                    file_name="legal_research_session.txt",
                    mime="text/plain",
                    key="hdr_export",
                    help="Export this session",
                    use_container_width=True
                )


# --------------------------------------------------------------- messages
def render_user_message(query: str) -> None:
    st.markdown(
        f'<div class="msg-user"><div class="bubble">{user_text(query)}</div>'
        f'<div class="avatar">{esc(initials(USER_NAME))}</div></div>',
        unsafe_allow_html=True,
    )


def render_ai_message(index: int, turn: dict) -> None:
    show = st.session_state.include_citations
    summary = f"{esc(turn.get('model', ''))} · {len(turn.get('retrieved_chunks', []))} sources retrieved"
    if show:
        summary += f" · {len(turn.get('citations', []))} cited"
    with st.container(key=f"ai_{index}"):
        st.markdown(prepare_answer(turn["answer"], show), unsafe_allow_html=True)
        st.markdown(f'<div class="ai-foot">{summary}</div>', unsafe_allow_html=True)


def render_empty_state() -> None:
    st.markdown(
        f'<div class="empty"><div class="scale">{icon("scale", 28)}</div>'
        "<h2>How can I assist your research today?</h2>"
        "<p>Ask legal questions about the judgments and statutes you have ingested. "
        "Hybrid retrieval (BM25 + dense embeddings) finds the evidence before the answer is written.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2, gap="small")
    for idx, (title, subtitle) in enumerate(SUGGESTIONS):
        with cols[idx % 2], st.container(key=f"sugg_{idx}"):
            st.markdown(
                f'<div class="sugg-card"><p class="sugg-title">{esc(title)}</p>'
                f'<p class="sugg-sub">{esc(subtitle)}</p></div>',
                unsafe_allow_html=True,
            )
            if st.button(title, key=f"suggbtn_{idx}"):
                st.session_state.pending_query = title
                st.rerun()


# ------------------------------------------------------- retrieval context
def render_source(index: int, chunk: dict, cited: bool) -> None:
    metadata = chunk.get("metadata") or {}
    chunk_id = str(chunk.get("chunk_id", "Unknown source"))
    text = str(chunk.get("text", ""))
    caption = first_line(metadata.get("caption_text"))
    kind = str(metadata.get("doc_type") or "").title()
    sub = esc(" · ".join(str(p) for p in (kind, metadata.get("pdf_filename")) if p))
    label = esc(source_label(chunk_id))
    
    # Detailed text is now exclusively locked within the pop-up modal
    caption_html = f'<div class="source-sub" style="margin-bottom: 12px;">{esc(caption)}</div>' if caption else ""

    with st.container(key=f"src_cited_{index}" if cited else f"src_{index}"):
        with st.popover(f"{index}. {label}", use_container_width=True):
            st.markdown(
                f'<div class="source-title">{index}. {label}</div>'
                f'<div class="source-sub">{sub}</div>{caption_html}'
                f'<div class="badges" style="margin-bottom: 16px;">{source_badges(chunk, cited)}</div>'
                f'<div class="excerpt-full">{esc(text)}</div>',
                unsafe_allow_html=True,
            )


def render_context(turn: dict) -> None:
    chunks = turn.get("retrieved_chunks", [])
    cited_ids = set(turn.get("citations", []))
    with st.container(key="context"):
        st.markdown(
            f'<div class="ctx-head"><span class="left">{icon("layers", 16)}Retrieval Context</span>'
            f'<span class="ctx-count">{len(chunks)}</span></div>',
            unsafe_allow_html=True,
        )
        with st.container(height=520, border=False, key="context_scroll"):
            for index, chunk in enumerate(chunks, start=1):
                render_source(index, chunk, str(chunk.get("chunk_id")) in cited_ids)


def scroll_to_latest() -> None:
    components.html(
        """<script>
        const doc = window.parent.document;
        const main = doc.querySelector('[data-testid="stMain"]') || doc.querySelector('section.main');
        if (main) setTimeout(() => main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}), 200);
        </script>""",
        height=0,
    )


# ------------------------------------------------------------------- page
client = LegalQAClient(os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
try:
    backend_online = client.health()
except BackendError:
    backend_online = False

prompt = st.chat_input("Ask a legal question or request document analysis...", max_chars=2000)
prompt = prompt or st.session_state.pop("pending_query", None)

render_sidebar()
render_topbar(backend_online)

session = store.get(active_id) or {"turns": []}
turns: list[dict] = session["turns"]
latest = turns[-1] if turns else None
has_sources = bool(latest and latest.get("retrieved_chunks"))

with st.container(key="workspace"):
    if has_sources:
        chat_area, context_area = st.columns([1, 0.34], gap="medium")
    else:
        chat_area, context_area = st.container(), None

    with chat_area, st.container(key="chat_empty" if not turns and not prompt else "chat"):
        if not turns and not prompt:
            render_empty_state()

        for index, turn in enumerate(turns):
            render_user_message(turn["query"])
            render_ai_message(index, turn)

        if prompt:
            query = prompt.strip()
            st.session_state.error = None
            render_user_message(query)

            if not backend_online:
                st.session_state.error = (
                    "The FastAPI backend is offline. Start it with "
                    "`uvicorn backend.app:app --port 8000`, then ask again."
                )
                st.rerun()

            pending = st.empty()
            with pending.container(key="ai_pending"):
                st.markdown(
                    '<div class="typing"><span class="dots"><span></span><span></span><span></span></span>'
                    "Analyzing context...</div>",
                    unsafe_allow_html=True,
                )
            try:
                result = client.ask(query)
            except (BackendError, ValueError) as exc:
                st.session_state.error = str(exc)
                st.rerun()

            store.add_turn(
                active_id,
                {
                    "query": query,
                    "answer": result.answer,
                    "citations": list(result.citations),
                    "retrieved_chunks": list(result.retrieved_chunks),
                    "model": result.model,
                },
            )
            st.session_state.scroll_pending = True
            st.rerun()

        if st.session_state.error:
            st.error(st.session_state.error)
        if store.save_error:
            st.warning(f"Sessions are not being saved: {store.save_error}")

    if context_area is not None and latest is not None:
        with context_area:
            render_context(latest)

if st.session_state.scroll_pending:
    st.session_state.scroll_pending = False
    scroll_to_latest()