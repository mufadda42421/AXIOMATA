"""Generic destination placeholder used until a department page is implemented.

Keeps navigation functional and clearly communicates the module's status without
pretending to be complete. Replaced by real pages in later phases.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .panels.base_page import BasePage


class ComingSoonPage(BasePage):
    def __init__(
        self,
        title: str,
        description: str,
        status_note: str = "This module is being built in a later development phase.",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(title, description, parent)
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(0, 24, 0, 0)
        icon = QLabel("🚧")
        icon.setStyleSheet("font-size:48px;")
        icon.setAlignment(icon.alignment())
        note = QLabel(status_note)
        note.setObjectName("H2")
        detail = QLabel(
            "AXIOMATA is under active development. This destination will provide a "
            "fully functional scientific workspace."
        )
        detail.setObjectName("MutedLabel")
        detail.setWordWrap(True)
        lay.addWidget(icon)
        lay.addWidget(note)
        lay.addWidget(detail)
        lay.addStretch(1)
        self.add_body_widget(body, 1)