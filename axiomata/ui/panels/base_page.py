"""Base page widget for all central-workspace destinations.

Provides a consistent, dense header (title + subtitle + optional toolbar) and
a body area, matching the working rhythm of laboratory software. Concrete
pages (Dashboard, labs, sandbox, etc.) subclass this.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..icons import icon
from ..themes.theme import ACCENT


class BasePage(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon_name: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Page")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 14)
        root.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        if icon_name:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon(icon_name, color=ACCENT, size=22).pixmap(22, 22))
            header_row.addWidget(icon_lbl)

        titles = QVBoxLayout()
        titles.setSpacing(1)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("H1")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("MutedLabel")
        self.subtitle_label.setWordWrap(True)
        titles.addWidget(self.title_label)
        if subtitle:
            titles.addWidget(self.subtitle_label)
        header_row.addLayout(titles, 1)

        self.toolbar = QHBoxLayout()
        self.toolbar.setSpacing(6)
        self.toolbar.addStretch(1)
        header_row.addLayout(self.toolbar)

        self.header_widget = QWidget()
        self.header_widget.setLayout(header_row)
        if title:
            root.addWidget(self.header_widget)

            line = QFrame()
            line.setObjectName("Separator")
            line.setFixedHeight(1)
            root.addWidget(line)
        else:
            self.header_widget.setVisible(False)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(10)
        root.addWidget(self.body, 1)

    def set_title(self, title: str, subtitle: str = "") -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))

    def add_toolbar_widget(self, widget: QWidget, stretch: int = 0) -> None:
        self.toolbar.insertWidget(max(0, self.toolbar.count() - 1), widget, stretch)

    def add_body_widget(self, widget: QWidget, stretch: int = 0) -> None:
        self.body_layout.addWidget(widget, stretch)
