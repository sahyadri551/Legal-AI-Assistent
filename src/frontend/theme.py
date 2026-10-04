"""Light and dark themes. Every colour in the stylesheet is a CSS variable."""
from __future__ import annotations

PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#f8fafc",
        "surface": "#ffffff",
        "surface2": "#f1f5f9",
        "border": "#e2e8f0",
        "border-strong": "#cbd5e1",
        "text": "#1e293b",
        "body": "#334155",
        "muted": "#64748b",
        "accent": "#2563eb",
        "accent-dark": "#1d4ed8",
        "accent-soft": "#dbeafe",
        "accent-ink": "#1d4ed8",
        "sidebar": "#0f172a",
        "sidebar-border": "rgba(51,65,85,.55)",
        "shadow": "rgba(15,23,42,.07)",
        "amber-bg": "#fef3c7",
        "amber-fg": "#b45309",
        "purple-bg": "#f3e8ff",
        "purple-fg": "#7e22ce",
        "green-bg": "#d1fae5",
        "green-fg": "#047857",
        "cited-bg": "#f3f8ff",
    },
    "dark": {
        "bg": "#0b1220",
        "surface": "#111c31",
        "surface2": "#1b2740",
        "border": "#26334d",
        "border-strong": "#3a4a6b",
        "text": "#e6edf7",
        "body": "#cbd5e1",
        "muted": "#94a3b8",
        "accent": "#3b82f6",
        "accent-dark": "#2563eb",
        "accent-soft": "rgba(59,130,246,.2)",
        "accent-ink": "#93c5fd",
        "sidebar": "#070d1a",
        "sidebar-border": "rgba(51,65,85,.7)",
        "shadow": "rgba(0,0,0,.4)",
        "amber-bg": "rgba(245,158,11,.16)",
        "amber-fg": "#fcd34d",
        "purple-bg": "rgba(168,85,247,.18)",
        "purple-fg": "#d8b4fe",
        "green-bg": "rgba(16,185,129,.16)",
        "green-fg": "#6ee7b7",
        "cited-bg": "rgba(59,130,246,.08)",
    },
}

_AVATAR_SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
    "fill='none' stroke='white' stroke-width='1.8' stroke-linecap='round' "
    "stroke-linejoin='round'%3E%3Cpath d='M12 3v18M7 21h10M5 7h14M5 7l-3 7a3 3 0 0 0 6 0L5 "
    "7zM19 7l-3 7a3 3 0 0 0 6 0l-3-7z'/%3E%3C/svg%3E"
)

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:wght@400;700&display=swap');
:root { __VARS__ }

/* ================= Base ================= */
.stApp, .stApp p, .stApp label, .stApp button, .stApp textarea, .stApp li,
.stApp [data-testid="stMarkdownContainer"] {
  font-family:'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp { background:var(--bg); color:var(--text); }
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li { color:var(--body); }
.stApp button [data-testid="stMarkdownContainer"] p { color:inherit !important; }
.icon { flex:none; }

/* Streamlit chrome fixes for sticky headers */
[data-testid="stHeader"] { background:transparent; height:0; min-height:0; pointer-events:none; }
[data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] { pointer-events:auto; }
[data-testid="stSidebarCollapsedControl"] button, [data-testid="stExpandSidebarButton"] {
  background:var(--sidebar); color:#fff; border-radius:8px;
}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stDeployButton"], .stDeployButton, #MainMenu, footer { display:none !important; }

/* MUST be visible for sticky headers to work */
[data-testid="stMainBlockContainer"], section.main .block-container {
  max-width:none !important; padding:0 !important; overflow: visible !important;
}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { 
  gap:0; overflow: visible !important; 
}

/* ================= Sidebar ================= */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background:var(--sidebar); }
[data-testid="stSidebar"] { border-right:1px solid var(--sidebar-border); }
[data-testid="stSidebarContent"] { padding:0 !important; }
[data-testid="stSidebarHeader"] {
  position:absolute; top:14px; right:6px; z-index:5; width:auto; height:auto;
  padding:0; margin:0; background:transparent;
}
[data-testid="stSidebarHeader"] button, [data-testid="stSidebarCollapseButton"] button { color:#94a3b8; }
[data-testid="stSidebarUserContent"] {
  padding:0 12px !important; height:100vh; overflow-y:auto; overflow-x:hidden;
}
[data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] { min-height:100%; gap:.15rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin:0; color:inherit !important; }

.brand {
  height:64px; display:flex; align-items:center; gap:12px; padding:0 18px;
  margin:0 -12px 18px; border-bottom:1px solid var(--sidebar-border);
}
.brand .icon { color:#60a5fa; }
.brand-name { color:#fff; font:600 18px 'Merriweather', Georgia, serif; letter-spacing:.02em; }
.side-label {
  color:#64748b; font-size:12px; font-weight:600; letter-spacing:.08em;
  text-transform:uppercase; margin:18px 10px 8px;
}
.nav-item {
  display:flex; align-items:center; gap:12px; padding:10px 12px; margin:2px 0;
  border-radius:8px; font-size:14px; font-weight:500; color:#94a3b8; cursor:default;
}
.nav-item.active { background:rgba(30,58,138,.42); color:#dbeafe; }
.nav-item.active .icon { color:#60a5fa; }

.st-key-newsession button {
  background:transparent; color:#cbd5e1; border:1px dashed rgba(148,163,184,.4);
  border-radius:8px; min-height:38px; font-size:13.5px; font-weight:500;
}
.st-key-newsession button:hover { background:rgba(59,130,246,.18); border-color:#3b82f6; color:#fff; }

[class*="st-key-sess_"] button {
  background:transparent; border:none; color:#94a3b8; border-radius:8px;
  min-height:36px; padding:6px 10px; font-size:14px; font-weight:400; justify-content:flex-start;
}
[class*="st-key-sess_"] button > div { width:100%; justify-content:flex-start; }
[class*="st-key-sess_"] button p {
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; text-align:left; max-width:100%;
}
[class*="st-key-sess_"] button:hover { background:rgba(255,255,255,.05); color:#e2e8f0; }
[class*="st-key-sess_active_"] button { background:rgba(30,58,138,.42); color:#dbeafe; }
[class*="st-key-srow_"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; gap:2px; }
[class*="st-key-srow_"] [data-testid="stColumn"] { min-width:0 !important; }
[class*="st-key-sessdel_"] button {
  background:transparent; border:none; color:#64748b; min-height:30px; padding:0;
  border-radius:6px; width:100%;
}
[class*="st-key-sessdel_"] button:hover { background:rgba(239,68,68,.18); color:#fca5a5; }
[class*="st-key-srow_"] [data-testid="stColumn"]:last-child { opacity:0; transition:opacity .12s; }
[class*="st-key-srow_"]:hover [data-testid="stColumn"]:last-child { opacity:1; }
@media (hover:none) { [class*="st-key-srow_"] [data-testid="stColumn"]:last-child { opacity:1; } }

.st-key-userbox {
  position:sticky; bottom:0; z-index:5;
  margin:auto -12px 0; padding:16px; border-top:1px solid var(--sidebar-border);
  background:var(--sidebar);
}
.userbox { display:flex; align-items:center; gap:12px; }
.userbox .avatar {
  width:32px; height:32px; border-radius:50%; background:#1d4ed8; color:#fff; flex:none;
  display:grid; place-items:center; font-size:13px; font-weight:700;
}
.userbox .name { color:#fff; font-size:14px; font-weight:500; line-height:1.3; }
.userbox .role { color:#94a3b8; font-size:12px; line-height:1.3; }

/* ================= Top bar ================= */
.st-key-topbar {
  position:sticky; top:0; z-index:999999; height:64px; padding:0 24px; gap:0;
  justify-content:center; background:var(--surface); border-bottom:1px solid var(--border);
  box-shadow:0 1px 3px var(--shadow);
}
.st-key-topbar [data-testid="stHorizontalBlock"] {
  flex-wrap:nowrap !important; gap:16px !important; align-items:center;
  width:100%; min-width:0;
}
.st-key-topbar [data-testid="stColumn"] { min-width:0 !important; }
.st-key-topbar [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { min-width:0 !important; }

/* Flex control: Title is compact, status pill fills the middle space to push right elements */
.st-key-topbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
  flex: 3.2 1 0 !important; min-width:0 !important; padding-right:0;
}
.st-key-topbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
  flex: 1.4 1 0 !important; min-width:0 !important;
}
.st-key-topbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) {
  flex: 2 1 0 !important; min-width:0 !important;
}
.st-key-topbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) {
  flex: .65 0 44px !important; min-width:44px !important;
}
.st-key-topbar [data-testid="stMarkdownContainer"] { margin:0; }
.stApp:has([data-testid="stSidebar"][aria-expanded="false"]) .st-key-topbar { padding-left:76px; }
.stApp:has([data-testid="stSidebarCollapsedControl"]) .st-key-topbar { padding-left:76px; }
.top-title {
  font-size:18px; font-weight:600; color:var(--text); line-height:1.25;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.top-sub {
  font-size:12px; color:var(--muted); margin-top:1px;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}

/* Align pill to left now */
.pill-wrap { display:flex; justify-content:flex-start; }
.status-pill {
  display:inline-flex; align-items:center; gap:8px; white-space:nowrap;
  background:var(--surface2); border:1px solid var(--border); border-radius:999px;
  padding:5px 12px; color:var(--body); font-size:12px; font-weight:500;
}
.status-dot { width:8px; height:8px; border-radius:50%; }

.st-key-topbar [data-testid="stCheckbox"] { display:flex; align-items:center; justify-content:flex-start; }
.st-key-topbar [data-testid="stCheckbox"] > label { width:auto; }
.st-key-topbar [data-testid="stCheckbox"] label {
  gap:6px; white-space:nowrap; font-size:12.5px; color:var(--muted);
}
.st-key-topbar [data-testid="stCheckbox"] label p { font-size:12.5px !important; color:var(--muted) !important; }

/* Popover & Action Buttons */
.st-key-topbar [data-testid="stPopover"] > button,
.st-key-topbar [data-testid="stPopover"] > button > div,
.st-key-topbar [data-testid="stPopover"] > button > div > div {
  background-color:var(--surface2) !important; border:1px solid var(--border) !important;
  color:var(--text) !important;
  width:44px; min-height:40px; padding:0; border-radius:10px; justify-content:center;
  box-shadow:none !important;
}
.st-key-topbar [data-testid="stPopover"] > button svg {
  color:var(--muted) !important; fill:var(--muted) !important;
}
.st-key-topbar [data-testid="stPopover"] > button p,
.st-key-topbar [data-testid="stPopover"] > button span { color:var(--text) !important; }
.st-key-topbar [data-testid="stPopover"] > button:hover {
  background:var(--accent-soft); border-color:var(--accent); color:var(--accent-ink);
}
.st-key-topbar [data-testid="stButton"] button:hover,
.st-key-topbar [data-testid="stDownloadButton"] button:hover {
  background:var(--accent-soft); color:var(--accent-ink);
}

/* Popover Menu Internal Styling */
[data-testid="stPopoverBody"],
[data-testid="stPopoverBody"] > div,
[data-testid="stPopoverBody"] [data-baseweb="popover"] {
  background:var(--surface) !important; color:var(--text) !important;
}
[data-testid="stPopoverBody"] { padding: 12px !important; border:1px solid var(--border) !important; border-radius:12px !important; box-shadow:0 12px 32px var(--shadow) !important; }
[data-testid="stPopoverBody"] [data-testid="stButton"] button,
[data-testid="stPopoverBody"] [data-testid="stDownloadButton"] button {
  width: 100% !important; min-height: 36px !important; padding: 6px 12px !important;
  justify-content: flex-start !important; border: 1px solid var(--border) !important;
  background: var(--surface) !important; color: var(--text) !important; border-radius: 8px !important;
  margin-bottom: 8px; font-size: 14px;
}
[data-testid="stPopoverBody"] [data-testid="stButton"] button:hover,
[data-testid="stPopoverBody"] [data-testid="stDownloadButton"] button:hover {
  background: var(--surface2) !important; border-color: var(--accent) !important;
}

/* ================= Workspace ================= */
.st-key-workspace {
  padding:28px 32px 190px;
  min-width:0 !important;
}

/* Let Streamlit's native columns control geometry. Only constrain their contents. */
.st-key-workspace [data-testid="stColumn"],
.st-key-workspace [data-testid="column"] {
  min-width:0 !important;
}
.st-key-workspace [data-testid="stHorizontalBlock"] {
  min-width:0 !important;
  width:100% !important;
  align-items:stretch !important;
}
.st-key-workspace [data-testid="stVerticalBlock"] {
  min-width:0 !important;
  max-width:100% !important;
}
.st-key-workspace [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
.st-key-workspace [data-testid="column"] > [data-testid="stVerticalBlock"] {
  min-width:0 !important;
  max-width:100% !important;
  width:100% !important;
}

[class*="st-key-chat"] {
  max-width:960px;
  min-width:0 !important;
  width:100% !important;
  margin:0 auto;
  gap:1.1rem;
}
.st-key-chat > [data-testid="stVerticalBlock"] {
  min-width:0 !important;
  max-width:100% !important;
  width:100% !important;
}
.st-key-chat_empty {
  min-height:calc(100vh - 270px);
  justify-content:center;
}
.st-key-chat_empty [data-testid="stHorizontalBlock"] {
  max-width:720px;
  margin:0 auto;
}
/* ================= Messages ================= */
.msg-user {
  display:flex;
  justify-content:flex-end;
  align-items:flex-start;
  gap:12px;
  min-width:0;
}
.msg-user .bubble {
  max-width:78%;
  min-width:0;
  background:var(--accent-dark);
  padding:13px 18px;
  border-radius:16px 4px 16px 16px;
  font-size:15px;
  line-height:1.6;
  overflow-wrap:anywhere !important;
  word-break:break-word !important;
  white-space:pre-wrap !important;
  box-shadow:0 1px 2px var(--shadow);
}
.msg-user .bubble, .msg-user .bubble * { color:#fff !important; }
.msg-user .avatar {
  width:32px; height:32px; border-radius:50%;
  background:#1d4ed8; color:#fff; flex:none;
  display:grid; place-items:center; font-size:12px; font-weight:700; margin-top:2px;
}

[class*="st-key-ai_"] {
  position:relative;
  margin-left:44px;
  width:auto !important;
  max-width:calc(100% - 44px) !important;
  min-width:0 !important;
  box-sizing:border-box;
  overflow:hidden !important;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:4px 16px 16px 16px;
  padding:16px 20px;
  gap:.7rem;
  box-shadow:0 1px 2px var(--shadow);
}
[class*="st-key-ai_"] > [data-testid="stVerticalBlock"],
[class*="st-key-ai_"] [data-testid="stVerticalBlock"] {
  min-width:0 !important;
  max-width:100% !important;
  width:100% !important;
  overflow:hidden !important;
}
[class*="st-key-ai_"] [data-testid="stMarkdown"],
[class*="st-key-ai_"] [data-testid="stMarkdownContainer"] {
  min-width:0 !important;
  max-width:100% !important;
  width:100% !important;
  overflow-wrap:anywhere !important;
  word-break:break-word !important;
}
[class*="st-key-ai_"] [data-testid="stMarkdownContainer"] p,
[class*="st-key-ai_"] [data-testid="stMarkdownContainer"] li {
  min-width:0 !important;
  max-width:100% !important;
  font-size:15px;
  line-height:1.75;
  color:var(--body);
  overflow-wrap:anywhere !important;
  word-break:break-word !important;
  white-space:pre-wrap !important;
}
[class*="st-key-ai_"]::before {
  content:"";
  position:absolute;
  left:-44px; top:2px;
  width:32px; height:32px;
  border-radius:50%;
  background:#1e293b url("__AVATAR__") center / 16px no-repeat;
  box-shadow:0 0 0 1px var(--border);
}
.ai-foot {
  min-width:0;
  border-top:1px solid var(--border);
  padding-top:10px;
  color:var(--muted);
  font-size:12px;
  overflow-wrap:anywhere;
}
.source-tag {
  display:inline-block;
  padding:1px 8px;
  margin:0 2px;
  border-radius:6px;
  white-space:normal;
  overflow-wrap:anywhere;
  background:var(--accent-soft);
  color:var(--accent-ink);
  font-size:12px;
  font-weight:600;
  line-height:1.6;
}
.typing { display:flex; align-items:center; gap:10px; color:var(--muted); font-size:13px; font-style:italic; }
.typing .dots span {
  display:inline-block; width:6px; height:6px; margin:0 2px; border-radius:50%;
  background:#94a3b8; animation:bounce 1.4s infinite ease-in-out both;
}
.typing .dots span:nth-child(1) { animation-delay:-.32s; }
.typing .dots span:nth-child(2) { animation-delay:-.16s; }
@keyframes bounce { 0%, 80%, 100% { transform:scale(0); } 40% { transform:scale(1); } }
[data-testid="stAlert"] {
  border-radius:12px; font-size:14px;
  background:rgba(239,68,68,.1);
  border:1px solid rgba(239,68,68,.35);
}
[data-testid="stAlert"] p { color:var(--text) !important; }
/* ================= Retrieval context ================= */
.st-key-context {
  position:sticky;
  top:76px;
  margin-top:10px;
  min-width:0 !important;
  max-width:100% !important;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:12px;
  overflow:hidden;
  gap:0;
  box-shadow:0 1px 2px var(--shadow);
}
.ctx-head {
  height:52px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:0 16px;
  background:var(--surface2);
  border-bottom:1px solid var(--border);
  font-size:14px;
  font-weight:600;
  color:var(--body);
}
.ctx-head .left { display:flex; align-items:center; gap:8px; }
.ctx-head .icon { color:var(--muted); }
.ctx-count {
  font-size:12px;
  font-weight:600;
  padding:2px 9px;
  border-radius:999px;
  background:var(--border);
  color:var(--body);
}
.st-key-context_scroll {
  padding:12px;
  min-width:0 !important;
  max-width:100% !important;
  overflow-x:hidden !important;
}

/* Retrieval buttons: force the active palette through BaseWeb's nested wrappers. */
[class*="st-key-src_"] {
  width:100% !important;
  min-width:0 !important;
  padding:0 !important;
  border:none !important;
  background:transparent !important;
  margin-bottom:8px;
}
[class*="st-key-src_"] [data-testid="stPopover"],
[class*="st-key-src_"] [data-testid="stPopover"] > button,
[class*="st-key-src_"] [data-testid="stPopover"] > button > div,
[class*="st-key-src_"] [data-testid="stPopover"] > button > div > div {
  width:100% !important;
  min-width:0 !important;
  box-sizing:border-box !important;
  border-radius:10px !important;
  background-color:var(--surface) !important;
  border:1px solid var(--border) !important;
  color:var(--text) !important;
  box-shadow:none !important;
}
[class*="st-key-src_"] [data-testid="stPopover"] > button {
  min-height:54px !important;
  padding:12px !important;
  justify-content:flex-start !important;
  text-align:left;
  font-weight:600;
  font-size:13px;
}
[class*="st-key-src_"] [data-testid="stPopover"] > button p,
[class*="st-key-src_"] [data-testid="stPopover"] > button span,
[class*="st-key-src_"] [data-testid="stPopover"] > button svg {
  color:var(--text) !important;
  fill:var(--text) !important;
}
[class*="st-key-src_"] [data-testid="stPopover"] > button:hover,
[class*="st-key-src_"] [data-testid="stPopover"] > button:hover > div,
[class*="st-key-src_"] [data-testid="stPopover"] > button:hover > div > div {
  background-color:var(--surface2) !important;
  border-color:var(--border-strong) !important;
}
[class*="st-key-src_cited_"] [data-testid="stPopover"] > button,
[class*="st-key-src_cited_"] [data-testid="stPopover"] > button > div,
[class*="st-key-src_cited_"] [data-testid="stPopover"] > button > div > div {
  background-color:var(--cited-bg) !important;
  border-color:var(--accent) !important;
  color:var(--accent-ink) !important;
}
[class*="st-key-src_cited_"] [data-testid="stPopover"] > button p,
[class*="st-key-src_cited_"] [data-testid="stPopover"] > button span,
[class*="st-key-src_cited_"] [data-testid="stPopover"] > button svg {
  color:var(--accent-ink) !important;
  fill:var(--accent-ink) !important;
}

.source-title { font-size:15px; font-weight:600; color:var(--text); line-height:1.4; overflow-wrap:anywhere; }
.source-sub { font-size:13px; color:var(--muted); margin-top:2px; overflow-wrap:anywhere; }
.source-text {
  font:italic 13px/1.65 'Merriweather', Georgia, serif;
  color:var(--body); margin-top:8px; overflow-wrap:anywhere;
}
.badges { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
.badge { padding:2px 9px; border-radius:999px; font-size:11px; font-weight:600; }
.badge.bm25 { background:var(--amber-bg); color:var(--amber-fg); }
.badge.dense { background:var(--purple-bg); color:var(--purple-fg); }
.badge.rrf { background:var(--green-bg); color:var(--green-fg); }
.badge.cited { background:var(--accent-soft); color:var(--accent-ink); }
.excerpt-full {
  max-width:100%;
  font:14px/1.7 'Merriweather', Georgia, serif;
  color:var(--body);
  white-space:pre-wrap;
  overflow-wrap:anywhere;
  word-break:break-word;
}
/* ================= Input area ================= */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div,
[data-testid="stBottomBlockContainer"] {
  background-color:var(--surface) !important;
}
[data-testid="stBottom"] {
  border-top:1px solid var(--border) !important;
}
[data-testid="stBottomBlockContainer"] {
  max-width:none;
  min-width:0 !important;
  padding:16px 32px 12px;
}
[data-testid="stBottomBlockContainer"]::after {
  content:"Powered by hybrid retrieval (RRF) & local LLMs.";
  display:block;
  margin-top:8px;
  padding-left:4px;
  font-size:12px;
  color:var(--muted);
}
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] {
  background-color:var(--surface) !important;
}
[data-testid="stChatInput"] {
  border:1px solid var(--border-strong) !important;
  border-radius:16px;
  box-shadow:0 1px 3px var(--shadow);
}
[data-testid="stChatInput"] textarea {
  background:transparent !important;
  border:none !important;
  font-size:15px;
  line-height:1.5;
  color:var(--text) !important;
  min-height:28px;
  max-height:140px;
}
[data-testid="stChatInput"] textarea::placeholder {
  color:var(--muted) !important;
  opacity:1;
}
[data-testid="stChatInput"]:focus-within {
  border-color:var(--accent);
  box-shadow:0 0 0 3px var(--accent-soft);
}
[data-testid="stChatInput"] button {
  background:var(--accent) !important;
  color:#fff !important;
  border-radius:10px;
}
[data-testid="stChatInput"] button:hover { background:var(--accent-dark) !important; }
[data-testid="stChatInput"] button:disabled { background:var(--border-strong) !important; }
/* ================= Responsive ================= */
@media (max-width:1100px) {
  .st-key-workspace { padding:20px 20px 180px; }
  .st-key-context { position:static; }
  .st-key-topbar { padding:0 16px; }
  [data-testid="stBottomBlockContainer"] { padding:12px 20px 12px; }
}
@media (max-width:700px) {
  .st-key-workspace { padding:14px 12px 170px; }
  .top-sub { display:none; }
  .st-key-topbar [data-testid="stCheckbox"] { display:none; }
  .msg-user .bubble { max-width:90%; }
  [class*="st-key-ai_"] { margin-left:0; max-width:100% !important; padding:14px; }
  [class*="st-key-ai_"]::before { display:none; }
  [data-testid="stBottomBlockContainer"] { padding:10px 12px 12px; }
  [data-testid="stBottomBlockContainer"]::after { display:none; }
}
"""

def build_css(theme: str = "light") -> str:
    """Return a ``<style>`` block for ``theme`` ("light" or "dark")."""
    palette = PALETTES.get(theme, PALETTES["light"])
    variables = " ".join(f"--{name}:{value};" for name, value in palette.items())
    css = BASE_CSS.replace("__VARS__", variables).replace("__AVATAR__", _AVATAR_SVG)
    return f"<style>{css}</style>"