"""Numeric formatting helpers shared by the scientific workspaces.

The application exposes a *precision* setting (significant figures) in the
View menu and the status bar. Results tables use these helpers so that a
figure printed in a lab notebook and a figure on screen agree.
"""
from __future__ import annotations

import math
from typing import Any

DEFAULT_PRECISION = 6


def format_number(value: Any, digits: int = DEFAULT_PRECISION) -> str:
    """Format ``value`` with ``digits`` significant figures.

    Non-numeric values are returned unchanged, and non-finite values are
    rendered as ``inf`` / ``nan`` rather than raising.
    """
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:d}"
    if isinstance(value, str):
        return value
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(v):
        return "nan"
    if math.isinf(v):
        return "inf" if v > 0 else "-inf"
    if v == 0.0:
        return "0"
    return f"{v:.{max(1, int(digits))}g}"


def format_with_unit(value: Any, unit: str = "", digits: int = DEFAULT_PRECISION) -> str:
    """Format ``value`` and append ``unit`` (separated by a space)."""
    text = format_number(value, digits)
    return f"{text} {unit}".strip()
