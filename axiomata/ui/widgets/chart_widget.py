"""A reusable matplotlib canvas widget embedded in the Qt UI.

Uses the QtAgg backend so plots render natively inside PySide6 widgets. The
figure reads the *active* palette at draw time, so switching between the
scientific dark theme and the lab light theme restyles every open chart
without recreating the widget.
"""
from __future__ import annotations

from typing import Optional, Sequence

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..themes.theme import palette


class ChartWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None, height: int = 300):
        super().__init__(parent)
        p = palette()
        self.figure = Figure(figsize=(6, 3.4), dpi=100, facecolor=p.CHART_BG)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setStyleSheet(f"background-color: {p.CHART_BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setMinimumHeight(height)
        self._style_axes()

    # -- styling -----------------------------------------------------------
    def _style_axes(self) -> None:
        p = palette()
        for ax in self.figure.axes:
            ax.set_facecolor(p.CHART_AX_BG)
            ax.tick_params(colors=p.TEXT_SECONDARY, labelsize=9)
            for spine in ax.spines.values():
                spine.set_color(p.BORDER)
            ax.grid(True, color=p.GRID_LINE, alpha=0.9, linewidth=0.6)
            ax.xaxis.label.set_color(p.TEXT_SECONDARY)
            ax.yaxis.label.set_color(p.TEXT_SECONDARY)
            ax.title.set_color(p.TEXT)
            ax.title.set_fontsize(10)
            ax.xaxis.label.set_fontsize(9)
            ax.yaxis.label.set_fontsize(9)

    def _refresh_colors(self) -> None:
        """Re-apply the active palette to the figure surface."""
        p = palette()
        self.figure.set_facecolor(p.CHART_BG)
        self.canvas.setStyleSheet(f"background-color: {p.CHART_BG};")

    def set_series_color(self, color: str) -> None:
        """Override the default series colour (used by callers with a theme)."""
        self._series_color = color

    # -- plotting ----------------------------------------------------------
    def plot_xy(
        self,
        x: Sequence[float],
        y: Sequence[float],
        xlabel: str = "x",
        ylabel: str = "y",
        title: str = "",
        color: str = "",
        clear: bool = True,
    ) -> None:
        p = palette()
        color = color or p.ACCENT
        if clear:
            self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(list(x), list(y), color=color, linewidth=1.7)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        self._refresh_colors()
        self._style_axes()
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def plot_series(
        self,
        series: list[tuple[Sequence[float], Sequence[float], str, str]],
        xlabel: str = "x",
        ylabel: str = "y",
        title: str = "",
    ) -> None:
        """Plot multiple (x, y, label, color) series on one axes."""
        p = palette()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for x, y, label, color in series:
            ax.plot(list(x), list(y), label=label, color=color, linewidth=1.7)
        if len(series) > 1:
            legend = ax.legend(fontsize=8, facecolor=p.CHART_AX_BG, edgecolor=p.BORDER)
            for text in legend.get_texts():
                text.set_color(p.TEXT_SECONDARY)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        self._refresh_colors()
        self._style_axes()
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def clear(self) -> None:
        self.figure.clear()
        self.canvas.draw_idle()

    def scatter(
        self,
        x: Sequence[float],
        y: Sequence[float],
        xlabel: str = "x",
        ylabel: str = "y",
        title: str = "",
        color: str = "",
        clear: bool = True,
    ) -> None:
        p = palette()
        color = color or p.ACCENT
        if clear:
            self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(list(x), list(y), color=color, s=14)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        self._refresh_colors()
        self._style_axes()
        self.figure.tight_layout()
        self.canvas.draw_idle()
