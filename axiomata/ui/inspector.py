"""Right inspector panel: contextual properties of the active workspace.

The inspector is a property sheet for whatever is currently open: the
workspace name, the active project, unit system and precision. Values are
shown in a monospace face so they line up like an instrument readout.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class Inspector(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Inspector")
        self.setMinimumWidth(240)
        self.setMaximumWidth(400)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header strip
        header = QFrame()
        header.setObjectName("PanelHeader")
        header.setFixedHeight(30)
        hrow = QVBoxLayout(header)
        hrow.setContentsMargins(12, 0, 12, 0)
        hrow.setSpacing(0)
        title = QLabel("INSPECTOR")
        title.setObjectName("PanelTitle")
        hrow.addWidget(title)
        hrow.addStretch(1)
        root.addWidget(header)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 11, 12, 12)
        body_layout.setSpacing(10)

        self.header_label = QLabel("No selection")
        self.header_label.setObjectName("H2")
        self.header_label.setWordWrap(True)
        body_layout.addWidget(self.header_label)

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("MutedLabel")
        self.subtitle.setWordWrap(True)
        body_layout.addWidget(self.subtitle)

        line = QFrame()
        line.setObjectName("Separator")
        line.setFixedHeight(1)
        body_layout.addWidget(line)

        # Scrollable properties grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._props_container = QWidget()
        self._grid = QGridLayout(self._props_container)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(10)
        self._grid.setVerticalSpacing(5)
        self._grid.setColumnStretch(1, 1)
        scroll.setWidget(self._props_container)
        body_layout.addWidget(scroll, 1)

        root.addWidget(body, 1)

        self._clear_grid()

    def _clear_grid(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def set_context(self, title: str, subtitle: str = "") -> None:
        self.header_label.setText(title)
        self.subtitle.setText(subtitle)
        self.subtitle.setVisible(bool(subtitle))

    def set_properties(self, props: list[tuple[str, str]]) -> None:
        self._clear_grid()
        for row, (key, value) in enumerate(props):
            k = QLabel(str(key))
            k.setObjectName("CaptionLabel")
            v = QLabel(str(value))
            v.setObjectName("Mono")
            v.setWordWrap(True)
            v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._grid.addWidget(k, row, 0)
            self._grid.addWidget(v, row, 1)
        if not props:
            hint = QLabel("Select an item or tool to inspect its properties.")
            hint.setObjectName("MutedLabel")
            hint.setWordWrap(True)
            self._grid.addWidget(hint, 0, 0, 1, 2)

    def clear(self) -> None:
        self.set_context("No selection")
        self.subtitle.setText("")
        self.set_properties([])
