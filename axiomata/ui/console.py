"""Bottom panel: scientific console, results, and an interactive command line.

The console is the app's transcript — every calculation, export and system
message is timestamped and colour-coded by severity, exactly as a log pane
in a laboratory application.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .themes.theme import palette

_TAGS = {"info": "INFO", "success": "OK", "warn": "WARN", "error": "ERR"}


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _level_colors() -> dict[str, str]:
    p = palette()
    return {
        "info": p.ACCENT,
        "success": p.SUCCESS,
        "warn": p.WARNING,
        "error": p.ERROR,
        "plain": p.TEXT,
    }


class ScientificConsole(QWidget):
    """Tabbed bottom panel: Console (colorised logs) + Results + command input."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ConsolePanel")
        self._command_handler: Optional[Callable[[str], None]] = None
        self._history: list[str] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header strip
        header = QFrame()
        header.setObjectName("PanelHeader")
        header.setFixedHeight(26)
        hrow = QHBoxLayout(header)
        hrow.setContentsMargins(12, 0, 12, 0)
        hrow.setSpacing(8)
        cap = QLabel("CONSOLE")
        cap.setObjectName("PanelTitle")
        hrow.addWidget(cap)
        hrow.addStretch(1)
        self.status_label = QLabel("idle")
        self.status_label.setObjectName("PanelHint")
        hrow.addWidget(self.status_label)
        root.addWidget(header)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("ConsoleTabs")

        # Console tab
        console_tab = QWidget()
        ctab = QVBoxLayout(console_tab)
        ctab.setContentsMargins(8, 6, 8, 6)
        ctab.setSpacing(4)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(5000)
        self.output.setStyleSheet("background: transparent; border: none;")
        ctab.addWidget(self.output)

        input_row = QWidget()
        il = QHBoxLayout(input_row)
        il.setContentsMargins(0, 2, 0, 0)
        il.setSpacing(6)
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Console command (type 'help')…")
        self.prompt.returnPressed.connect(self._on_command)
        send = QPushButton("Run")
        send.setObjectName("Ghost")
        send.clicked.connect(self._on_command)
        il.addWidget(self.prompt)
        il.addWidget(send)
        ctab.addWidget(input_row)

        self._tabs.addTab(console_tab, "Console")

        # Results tab
        self.results = QPlainTextEdit()
        self.results.setReadOnly(True)
        self.results.setStyleSheet("background: transparent; border: none;")
        self._tabs.addTab(self.results, "Results")

        root.addWidget(self._tabs, 1)
        self.info("AXIOMATA console ready. Type 'help' for commands.")

    # -- logging API -------------------------------------------------------
    def log(self, message: str, level: str = "info") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        colors = _level_colors()
        color = colors.get(level, colors["plain"])
        tag = _TAGS.get(level)
        p = palette()
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        if not self.output.document().isEmpty():
            cursor.insertText("\n")
        cursor.insertHtml(f'<span style="color:{p.TEXT_DIM};">[{ts}]</span> ')
        if tag:
            cursor.insertHtml(f'<span style="color:{color};">{tag}</span> ')
        cursor.insertHtml(f'<span style="color:{color};">{_escape(message)}</span>')
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def info(self, message: str) -> None:
        self.log(message, "info")

    def success(self, message: str) -> None:
        self.log(message, "success")

    def warn(self, message: str) -> None:
        self.log(message, "warn")

    def error(self, message: str) -> None:
        self.log(message, "error")

    def result(self, message: str) -> None:
        self.results.appendPlainText(message)

    def clear(self) -> None:
        self.output.clear()

    # -- command handling --------------------------------------------------
    def set_command_handler(self, handler: Callable[[str], None]) -> None:
        self._command_handler = handler

    def _on_command(self) -> None:
        text = self.prompt.text().strip()
        if not text:
            return
        self.prompt.clear()
        self._history.append(text)
        self.info(f"> {text}")
        if self._command_handler is not None:
            try:
                self._command_handler(text)
            except Exception as exc:  # noqa: BLE001
                self.error(f"Command failed: {exc}")
        else:
            self.warn("No command handler registered.")
