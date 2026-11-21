"""Lightweight Lucide-style SVG icon system for AXIOMATA.

Provides consistent, professional vector icons rendered as Qt ``QIcon`` via
``QSvgRenderer``. No emoji are used as primary interface icons. Icons are drawn
from a small embedded set of Lucide-derived paths (stroke-based, 24×24 viewBox)
so the application has zero external asset dependencies.

Usage::

    from .icons import icon
    btn.setIcon(icon("flask"))
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Lucide-derived stroke paths (24x24). These are simplified geometric icons
# consistent with the Lucide design language (rounded strokes, 24px grid).
_PATHS: dict[str, str] = {
    "home": '<path d="M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "flask": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/>',
    "atom": '<circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/><ellipse cx="12" cy="12" rx="10" ry="4.2"/><ellipse cx="12" cy="12" rx="10" ry="4.2" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.2" transform="rotate(120 12 12)"/>',
    "dna": '<path d="M4 4c6 0 10 4 10 10s4 6 6 6M20 4c-6 0-10 4-10 10s-4 6-6 6"/>',
    "telescope": '<path d="M4 14l9-9 3 3-9 9zM14 6l2-2 3 3-2 2M9 14l-3 6M12 11l-1 9"/>',
    "orbit": '<circle cx="12" cy="12" r="3"/><ellipse cx="12" cy="12" rx="10" ry="5" transform="rotate(-25 12 12)"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/>',
    "calculator": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 10h8M8 14h2M12 14h2M8 18h2M12 18h2"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "cube": '<path d="M12 2 3 7l9 5 9-5-9-5zM3 7v10l9 5 9-5V7M12 12v10"/>',
    "chart": '<path d="M4 3v18h17"/><path d="M8 15l3-4 3 2 4-6"/>',
    "book": '<path d="M4 4a2 2 0 0 1 2-2h13v18H6a2 2 0 0 0-2 2zM19 2v18"/>',
    "note": '<path d="M5 3h9l5 5v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM14 3v5h5M8 13h8M8 17h5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "chevron_left": '<path d="m15 18-6-6 6-6"/>',
    "chevron_right": '<path d="m9 18 6-6-6-6"/>',
    "chevron_down": '<path d="m6 9 6 6 6-6"/>',
    "bell": '<path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "activity": '<path d="M3 12h4l3 8 4-16 3 8h4"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.5 9a2.5 2.5 0 0 1 5 .5c0 1.5-2.5 2-2.5 3.5M12 17h.01"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "alert": '<path d="M12 3 2 21h20L12 3zM12 9v5M12 17h.01"/>',
    "play": '<path d="M6 4l14 8-14 8z" fill="currentColor" stroke="none"/>',
    "pause": '<rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/><rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/>',
    "stop": '<rect x="5" y="5" width="14" height="14" rx="2" fill="currentColor" stroke="none"/>',
    "reset": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5"/>',
    "save": '<path d="M5 3h11l3 3v15H5zM8 3v6h8M8 21v-7h8v7"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
    "upload": '<path d="M12 21V9M7 14l5-5 5 5M5 3h14"/>',
    "trash": '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v6M14 11v6"/>',
    "edit": '<path d="M4 20h4L19 9l-4-4L4 16zM14 6l4 4"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
    "archive": '<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v11h14V9M10 13h4"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5zM3 12l9 5 9-5M3 17l9 5 9-5"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/>',
    "hard_drive": '<path d="M3 13l3-8h12l3 8M3 13h18v6H3zM7 16h.01M11 16h.01"/>',
    "folder_open": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2M3 7v10a2 2 0 0 0 2 2h12l2-8H6z"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "arrow_right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/>',
}

_DEFAULT_COLOR = "#91A2B8"


def _full_svg(name: str, color: str, stroke_width: float = 1.8) -> Optional[str]:
    body = _PATHS.get(name)
    if body is None:
        return None
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


def _render_pixmap(name: str, color: str, size: int) -> QPixmap:
    svg = _full_svg(name, color)
    if svg is None:
        # Fallback: empty transparent pixmap.
        return QPixmap(size, size)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pixmap


def icon(name: str, color: str = _DEFAULT_COLOR, size: int = 20) -> QIcon:
    """Return a QIcon for the named glyph rendered in ``color``."""
    return QIcon(_render_pixmap(name, color, size))


def icon_pixmap(name: str, color: str = _DEFAULT_COLOR, size: int = 20) -> QPixmap:
    """Return a QPixmap for the named glyph (for direct painting)."""
    return _render_pixmap(name, color, size)


def has_icon(name: str) -> bool:
    return name in _PATHS


def set_icon_theme_color(color: str) -> None:
    """No-op hook retained for API symmetry; colors are passed per-icon."""
    _ = color