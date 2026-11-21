"""First-launch profession selection.

This is a personalisation step, not authentication. There is no login and no
account. The user picks a discipline; every discipline still has access to all
departments. The selection is stored locally in the settings store.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..core.professions import PROFESSIONS, Profession
from .themes.theme import ACCENT, BG_DEEP, TEXT_MUTED


class ProfessionCard(QFrame):
    def __init__(self, profession: Profession, on_pick: Callable[[Profession], None]):
        super().__init__()
        self.profession = profession
        self.setObjectName("Card")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(96)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        icon = QLabel(profession.icon)
        icon.setStyleSheet("font-size:26px;")
        lay.addWidget(icon)

        name = QLabel(profession.name)
        name.setStyleSheet("font-size:15px; font-weight:600;")
        lay.addWidget(name)

        desc = QLabel(profession.description)
        desc.setObjectName("MutedLabel")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
        lay.addWidget(desc)

        self.mouseReleaseEvent = lambda e: on_pick(profession)  # type: ignore[assignment]


class OnboardingDialog(QWidget):
    """Full-screen (within main window) profession picker."""

    selected = Signal(str)  # emits profession key

    def __init__(self, on_select: Callable[[str], None], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._on_select = on_select
        self.setObjectName("OnboardingRoot")

        root = QVBoxLayout(self)
        root.setContentsMargins(48, 48, 48, 48)
        root.setSpacing(8)

        title = QLabel("Welcome to AXIOMATA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:30px; font-weight:700; color:#e6edf7;")
        root.addWidget(title)

        tagline = QLabel("Explore. Experiment. Understand.")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(f"font-size:15px; color:{ACCENT};")
        root.addWidget(tagline)

        subtitle = QLabel("Select your scientific discipline to personalise your workspace.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("MutedLabel")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)
        root.addSpacing(10)

        # Scrollable grid of profession cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)

        cols = 3
        for idx, prof in enumerate(PROFESSIONS):
            r, c = divmod(idx, cols)
            grid.addWidget(ProfessionCard(prof, self._pick), r, c)

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        hint = QLabel(
            "This is not a login — you can change your profession any time in Settings "
            "without losing any projects. Every discipline has access to all laboratories."
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setObjectName("MutedLabel")
        hint.setWordWrap(True)
        root.addWidget(hint)

    def _pick(self, profession: Profession) -> None:
        self._on_select(profession.key)