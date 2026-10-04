"""Small inline SVG icon set (Feather-style). No network or icon font needed."""
from __future__ import annotations

_PATHS = {
    "scale": (
        '<path d="M12 3v18M7 21h10M5 7h14M5 7l-3 7a3 3 0 0 0 6 0L5 7z'
        'M19 7l-3 7a3 3 0 0 0 6 0l-3-7z"/>'
    ),
    "comments": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "file": (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>'
    ),
    "search": '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>',
    "layers": '<path d="M12 2l10 5-10 5L2 7z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>',
}


def icon(name: str, size: int = 18) -> str:
    return (
        f'<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{_PATHS[name]}</svg>'
    )
