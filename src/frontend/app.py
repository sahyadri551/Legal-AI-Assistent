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
    ("feature_mode", "qa"),
    ("search_results", []),
    ("search_query", ""),
    ("document_file", None),
    ("document_result", None),
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
            '<div class="side-label">Workspaces</div>',
            unsafe_allow_html=True,
        )
        nav_items = [
            ("qa", ":material/chat_bubble_outline: Legal Research QA"),
            ("document", ":material/description: Document Analysis"),
            ("search", ":material/search: Case Law Search"),
        ]
        for mode, label in nav_items:
            active = st.session_state.feature_mode == mode
            if st.button(
                label,
                key=f"workspace_{mode}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.feature_mode = mode
                st.session_state.error = None
                st.session_state.search_results = []
                st.session_state.search_query = ""
                st.session_state.document_result = None
                st.rerun()
        st.markdown('<div class="side-label">Recent Sessions</div>', unsafe_allow_html=True)

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


# ------------------------------------------------------------- feature views
def render_search_workspace() -> None:
    st.markdown("### Case Law Search")
    st.caption("Search the indexed judgments and return ranked legal sources.")
    results = st.session_state.search_results
    if st.session_state.error:
        st.error(st.session_state.error)
    if not results and st.session_state.search_query and not st.session_state.error:
        st.info(f'No matching sources found for "{st.session_state.search_query}". Try different keywords.')
    if not results:
        st.markdown(
            '<div class="feature-empty">'
            '<div class="feature-empty-icon">⌕</div>'
            '<div><strong>Search indexed case law</strong>'
            '<p>Use the search box below to find relevant judgments and legal sources.</p></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return
    st.caption(f'{len(results)} ranked case-law sources for "{esc(st.session_state.search_query)}"')
    for index, result in enumerate(results, start=1):
        metadata = result.get("metadata") or {}
        title = source_label(str(result.get("chunk_id", "Unknown source")))
        filename = str(metadata.get("pdf_filename") or "")
        caption = first_line(metadata.get("caption_text"))
        score = float(result.get("score", 0.0))
        heading = f"{index}. {md_escape(title)}"
        if caption:
            heading += f" — {md_escape(caption[:90])}"
        with st.expander(heading, expanded=False):
            st.markdown(
                f'<div class="result-meta">{esc(filename) if filename else "Judgment"} · RRF {score:.4f}</div>'
                f'<div class="result-body">{esc(str(result.get("text") or ""))}</div>',
                unsafe_allow_html=True,
            )


def render_document_workspace() -> None:
    st.markdown("### Document Analysis")
    st.caption("Upload a PDF, then ask questions grounded only in that document.")
    if st.session_state.error:
        st.error(st.session_state.error)
    st.markdown('<div class="doc-upload-label">Upload a PDF document</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Choose PDF",
        type=["pdf"],
        key="document_upload",
        help="Maximum 15 MB. Text-based PDFs are supported.",
        label_visibility="collapsed",
    )
    if uploaded is not None:
        st.session_state.document_file = (uploaded.name, uploaded.getvalue())
    if st.session_state.document_file:
        name, content = st.session_state.document_file
        st.success(f"Ready: {name} · {len(content) / 1024:.0f} KB")
        if st.session_state.document_result:
            render_ai_message(0, st.session_state.document_result)


# ------------------------------------------------------------------- page
client = LegalQAClient(os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
try:
    backend_online = client.health()
except BackendError:
    backend_online = False

placeholders = {
    "qa": "Ask a legal question...",
    "document": "Ask a question about the uploaded PDF...",
    "search": "Search case law and legal sources...",
}
prompt = st.chat_input(placeholders[st.session_state.feature_mode], max_chars=2000)
prompt = prompt or st.session_state.pop("pending_query", None)

VOICE_JS = r"""
(function () {
  if (window.__lexVoiceV2) return;
  window.__lexVoiceV2 = true;

  var BTN = 'lexassist-voice';
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var rec = null, listening = false, baseText = '';

  function root() { return document.querySelector('[data-testid="stChatInput"]'); }
  function area() { var r = root(); return r && r.querySelector('textarea'); }
  function btn() { return document.getElementById(BTN); }

  function toast(msg) {
    var old = document.getElementById('lexassist-voice-toast');
    if (old) old.remove();
    var t = document.createElement('div');
    t.id = 'lexassist-voice-toast';
    t.textContent = msg;
    t.style.cssText = 'position:fixed;left:50%;bottom:110px;transform:translateX(-50%);' +
      'background:#0f172a;color:#fff;padding:10px 16px;border-radius:10px;font-size:13px;' +
      'z-index:999999;box-shadow:0 4px 18px rgba(0,0,0,.25);max-width:80vw;';
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 4500);
  }

  function setText(value) {
    var t = area();
    if (!t) return;
    var setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(t, value);
    t.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function paint(on, title) {
    var b = btn();
    if (!b) return;
    b.classList.toggle('is-listening', !!on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
    b.title = title || 'Voice input';
  }

  var ERRORS = {
    'not-allowed': 'Microphone access is blocked. Allow the microphone for this site (lock icon in the address bar) and try again.',
    'service-not-allowed': 'Speech recognition is blocked in this browser. Try Chrome or Edge.',
    'no-speech': 'No speech detected. Click the mic and speak again.',
    'audio-capture': 'No microphone found. Connect one and try again.',
    'network': 'Speech recognition needs an internet connection (Chrome/Edge send audio to a speech service).',
    'language-not-supported': 'This language is not supported for voice input.'
  };

  function start() {
    if (!SR) { toast('Voice input is not supported in this browser. Use Chrome or Edge.'); return; }
    rec = new SR();
    rec.lang = 'en-IN';
    rec.interimResults = true;
    rec.continuous = false;
    rec.maxAlternatives = 1;
    var t = area();
    baseText = t ? t.value.trim() : '';

    rec.onstart = function () { listening = true; paint(true, 'Listening... click to stop'); };
    rec.onend = function () { listening = false; paint(false); var a = area(); if (a) a.focus(); };
    rec.onerror = function (e) {
      listening = false; paint(false);
      toast(ERRORS[e.error] || ('Voice input error: ' + e.error));
    };
    rec.onresult = function (e) {
      var finalText = '', interim = '';
      for (var i = 0; i < e.results.length; i++) {
        var chunk = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += chunk; else interim += chunk;
      }
      setText((baseText + ' ' + finalText + interim).trim());
    };
    try { rec.start(); } catch (err) { toast('Could not start voice input: ' + err.message); }
  }

  // Delegated, capture-phase click handler: survives Streamlit re-rendering the button.
  document.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest('#' + BTN) : null;
    if (!b) return;
    ev.preventDefault();
    ev.stopPropagation();
    if (listening && rec) { try { rec.stop(); } catch (e) {} } else { start(); }
  }, true);

  function install() {
    var r = root();
    if (!r) return;
    var existing = btn();
    if (existing && r.contains(existing)) return;
    if (existing) existing.remove();

    var submit = r.querySelector('[data-testid="stChatInputSubmitButton"]');
    if (!submit) {
      var all = r.querySelectorAll('button');
      submit = all[all.length - 1];
    }
    if (!submit || !submit.parentElement) return;

    var b = document.createElement('button');
    b.id = BTN;
    b.type = 'button';
    b.setAttribute('aria-label', 'Voice input');
    b.title = SR ? 'Voice input' : 'Voice input is not supported in this browser';
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M12 14a3.5 3.5 0 0 0 3.5-3.5v-5a3.5 3.5 0 0 0-7 0v5A3.5 3.5 0 0 0 12 14Z"/>' +
      '<path d="M18 10.5a6 6 0 0 1-12 0M12 16.5V21M8.5 21h7"/></svg>';
    b.style.pointerEvents = 'auto';
    b.style.position = 'relative';
    b.style.zIndex = '5';
    submit.parentElement.insertBefore(b, submit);
    if (listening) paint(true, 'Listening... click to stop');
  }

  new MutationObserver(install).observe(document.body, { childList: true, subtree: true });
  install();
})();
"""


def install_voice_input() -> None:
    """Inject the mic button script into the host page once (not into a throw-away iframe)."""
    components.html(
        "<script>(function(){"
        "var d=window.parent.document;"
        "if(d.getElementById('lexassist-voice-script'))return;"
        "var s=d.createElement('script');s.id='lexassist-voice-script';"
        f"s.textContent={json.dumps(VOICE_JS)};"
        "d.head.appendChild(s);})();</script>",
        height=0,
    )


install_voice_input()


render_sidebar()
render_topbar(backend_online)

session = store.get(active_id) or {"turns": []}
turns: list[dict] = session["turns"]
latest = turns[-1] if turns else None
has_sources = bool(latest and latest.get("retrieved_chunks"))

with st.container(key="workspace"):
    mode = st.session_state.feature_mode

    if mode == "document":
        render_document_workspace()
    elif mode == "search":
        render_search_workspace()
    else:
        session = store.get(active_id) or {"turns": []}
        turns: list[dict] = session["turns"]
        latest = turns[-1] if turns else None
        has_sources = bool(latest and latest.get("retrieved_chunks"))

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

            if prompt and mode == "qa":
                query = prompt.strip()
                st.session_state.error = None
                render_user_message(query)
                if not backend_online:
                    st.error("The FastAPI backend is offline.")
                else:
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

    if mode == "search" and prompt:
        if not backend_online:
            st.session_state.error = "The FastAPI backend is offline. Start it on port 8000 and refresh."
            st.rerun()
        else:
            st.session_state.error = None
            try:
                with st.spinner("Searching indexed case law..."):
                    found = client.search(prompt)
                st.session_state.search_results = found
                st.session_state.search_query = prompt.strip()
            except (BackendError, ValueError) as exc:
                st.session_state.search_results = []
                st.session_state.search_query = ""
                st.session_state.error = str(exc)
            st.rerun()

    if mode == "document" and prompt:
        document = st.session_state.document_file
        if not document:
            st.error("Upload a PDF before asking a document-analysis question.")
        elif not backend_online:
            st.error("The FastAPI backend is offline.")
        else:
            name, content = document
            try:
                result = client.analyze_document(content, name, prompt)
                st.session_state.document_result = {
                    "query": prompt.strip(),
                    "answer": result.answer,
                    "citations": list(result.citations),
                    "retrieved_chunks": list(result.retrieved_chunks),
                    "model": result.model,
                }
                st.rerun()
            except (BackendError, ValueError) as exc:
                st.session_state.error = str(exc)
                st.rerun()

if st.session_state.scroll_pending:
    st.session_state.scroll_pending = False
    scroll_to_latest()