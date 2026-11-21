"""Reusable UI components shared across AXIOMATA pages.

Two families live here:

**Shell components** — ``SectionHeader``, ``StatusIndicator``,
``ActionButton``, ``EmptyState``, ``ToastNotification`` and ``Panel``.

**Scientific components** — the widgets that make a page read like laboratory
software rather than a web dashboard:

``ResultTable``
    A Quantity / Value / Unit / Notes table. Values are monospace and
    right-aligned so digits line up down the column.
``EquationBlock``
    A framed, monospace display of the governing equations, with an accent
    rule down the left edge.
``ParamForm``
    A grid-aligned parameter editor: symbol + description on the left,
    the editable value with its unit suffix on the right.
``DockPanel``
    A titled panel with a header strip, used to frame each region of a page.
``StatTile``
    A compact metric readout for dashboards.
``ReadoutRow``
    A single monospace key/value pair for instrument-style status strips.
"""
from __future__ import annotations

from typing import Optional, Sequence

from PySide6.QtCore import QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .icons import icon, icon_pixmap
from .themes.theme import (
    ACCENT, ACCENT_2, BORDER_SOFT, ERROR, PANEL, PANEL_ELEVATED, SUCCESS,
    TEXT, TEXT_DIM, TEXT_SECONDARY, WARNING,
)


# ==========================================================================
# Shell components
# ==========================================================================
class Panel(QFrame):
    """A surface container with the standard panel styling."""

    def __init__(self, parent: Optional[QWidget] = None, elevated: bool = False):
        super().__init__(parent)
        self.setObjectName("PanelAlt" if elevated else "Panel")


class SectionHeader(QWidget):
    """A small section title with an optional action link on the right."""

    action_clicked = Signal()

    def __init__(self, title: str, action_text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.title = QLabel(title.upper())
        self.title.setObjectName("SectionTitle")
        lay.addWidget(self.title)
        lay.addStretch(1)
        self.action_btn: Optional[QPushButton] = None
        if action_text:
            self.action_btn = QPushButton(action_text)
            self.action_btn.setObjectName("HeaderButton")
            self.action_btn.setCursor(Qt.PointingHandCursor)
            self.action_btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(self.action_btn)


class StatusIndicator(QWidget):
    """A coloured dot + label used for status rows (e.g. database status)."""

    def __init__(self, label: str, color: str = SUCCESS, parent: Optional[QWidget] = None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(7)
        self.dot = QLabel()
        self.dot.setObjectName("Dot")
        self.dot.setFixedSize(7, 7)
        self.dot.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
        self.text = QLabel(label)
        self.text.setObjectName("MutedLabel")
        lay.addWidget(self.dot)
        lay.addWidget(self.text)
        lay.addStretch(1)

    def set_state(self, label: str, color: str) -> None:
        self.text.setText(label)
        self.dot.setStyleSheet(f"background-color: {color}; border-radius: 3px;")


class ActionButton(QPushButton):
    """A primary-styled call-to-action button with an optional leading icon."""

    def __init__(self, text: str, icon_name: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("Primary")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(28)
        if icon_name:
            self.setIcon(icon(icon_name, color="#06121A", size=15))


class EmptyState(QWidget):
    """An empty-state placeholder with an icon, message, and optional action."""

    action_clicked = Signal()

    def __init__(
        self,
        message: str,
        submessage: str = "",
        icon_name: str = "layers",
        action_text: str = "",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 24, 16, 24)
        lay.setSpacing(7)
        lay.addStretch(1)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon_pixmap(icon_name, color=TEXT_DIM, size=34))
        icon_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon_lbl)

        title = QLabel(message)
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("MutedLabel")
        lay.addWidget(title)

        if submessage:
            sub = QLabel(submessage)
            sub.setAlignment(Qt.AlignCenter)
            sub.setObjectName("CaptionLabel")
            sub.setWordWrap(True)
            lay.addWidget(sub)

        if action_text:
            btn = QPushButton(action_text)
            btn.setObjectName("Primary")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedWidth(170)
            btn.clicked.connect(self.action_clicked.emit)
            row = QHBoxLayout()
            row.addStretch(1)
            row.addWidget(btn)
            row.addStretch(1)
            lay.addLayout(row)

        lay.addStretch(1)


class ToastNotification(QFrame):
    """A transient toast that slides/fades in at a corner of its parent."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setFixedWidth(330)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(13, 10, 13, 10)
        lay.setSpacing(9)

        self.icon_lbl = QLabel()
        lay.addWidget(self.icon_lbl)

        self.msg = QLabel()
        self.msg.setWordWrap(True)
        lay.addWidget(self.msg, 1)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._hide)

        self._effect.setOpacity(0.0)
        self.hide()

    def show_message(self, text: str, level: str = "info", duration_ms: int = 3000) -> None:
        colors = {"info": ACCENT, "success": SUCCESS, "warn": WARNING, "error": ERROR}
        icon_names = {"info": "bell", "success": "check", "warn": "alert", "error": "alert"}
        color = colors.get(level, ACCENT)
        self.icon_lbl.setPixmap(icon_pixmap(icon_names.get(level, "bell"), color=color, size=17))
        self.msg.setText(text)

        self.adjustSize()
        parent = self.parentWidget()
        if parent is not None:
            pw, ph = parent.width(), parent.height()
            self.move(pw - self.width() - 18, 14)

        self.show()
        self.raise_()
        self._effect.setOpacity(0.0)
        self._fade = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade.setDuration(160)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()
        self._timer.start(duration_ms)

    def _hide(self) -> None:
        self._fade = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade.setDuration(200)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self.hide)
        self._fade.start()


# ==========================================================================
# Scientific components
# ==========================================================================
class ResultTable(QTableWidget):
    """A Quantity / Value / Unit / Notes results table.

    Numeric values are rendered in a monospace face and right-aligned so that
    significant figures line up vertically, as they do in a lab notebook.
    """

    HEADERS = ("Quantity", "Value", "Unit", "Notes")

    def __init__(
        self,
        headers: Sequence[str] = HEADERS,
        parent: Optional[QWidget] = None,
        min_height: int = 120,
    ):
        super().__init__(parent)
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(list(headers))
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setShowGrid(True)
        self.setWordWrap(False)
        self.setMinimumHeight(min_height)

        vh = self.verticalHeader()
        vh.setDefaultSectionSize(24)
        vh.setSectionResizeMode(QHeaderView.Fixed)

        hh = self.horizontalHeader()
        hh.setHighlightSections(False)
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, self.columnCount()):
            hh.setSectionResizeMode(col, QHeaderView.ResizeToContents)

    # -- population --------------------------------------------------------
    def set_rows(self, rows: Sequence[tuple]) -> None:
        """Replace the table contents.

        Each row is a tuple of ``(quantity, value, unit, notes)``; any element
        may be omitted, in which case it is left blank.
        """
        self.setRowCount(0)
        for row in rows:
            padded = tuple(list(row) + [""] * (4 - len(row)))[:4]
            r = self.rowCount()
            self.insertRow(r)
            for c, text in enumerate(padded):
                item = QTableWidgetItem("" if text is None else str(text))
                if c == 1:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    f = item.font()
                    f.setFamily("Consolas")
                    f.setStyleHint(QFont.Monospace)
                    item.setFont(f)
                elif c == 2:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.setItem(r, c, item)
        self.resizeRowsToContents()

    def set_result(self, quantity: str, value: str, unit: str = "", notes: str = "") -> None:
        """Update (or append) a single quantity row."""
        for r in range(self.rowCount()):
            item = self.item(r, 0)
            if item and item.text() == quantity:
                for c, text in enumerate((quantity, value, unit, notes)):
                    if c == 0:
                        continue
                    cell = self.item(r, c) or QTableWidgetItem()
                    cell.setText(str(text))
                    if c == 1:
                        cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    elif c == 2:
                        cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.setItem(r, c, cell)
                return
        self.set_rows(list(self.current_rows()) + [(quantity, value, unit, notes)])

    def current_rows(self) -> list[tuple[str, str, str, str]]:
        rows: list[tuple[str, str, str, str]] = []
        for r in range(self.rowCount()):
            cells = []
            for c in range(self.columnCount()):
                it = self.item(r, c)
                cells.append(it.text() if it else "")
            rows.append((cells[0], cells[1], cells[2], cells[3]))
        return rows


class EquationBlock(QFrame):
    """A framed display of the governing equations for a calculation."""

    def __init__(self, equations: str = "", title: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("EquationBlock")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(11, 8, 11, 8)
        lay.setSpacing(4)

        if title:
            cap = QLabel(title.upper())
            cap.setObjectName("PanelTitle")
            lay.addWidget(cap)

        self.label = QLabel(equations)
        self.label.setObjectName("Equation")
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.label)

    def set_equations(self, equations: str) -> None:
        self.label.setText(equations)

    def set_title(self, title: str) -> None:
        if title:
            cap = QLabel(title.upper())
            cap.setObjectName("PanelTitle")
            self.layout().insertWidget(0, cap)


class ParamForm(QWidget):
    """A grid-aligned parameter editor.

    Rows are laid out as ``symbol + description`` on the left and the
    editable value on the right, with the unit attached to the field. Values
    are numeric spin boxes so a scientist can type an exact figure or step
    through it with the arrow keys.
    """

    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._title = title
        self._fields: dict[str, QDoubleSpinBox] = {}
        self._texts: dict[str, QLineEdit] = {}
        self._choices: dict[str, QComboBox] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        if title:
            head = QLabel(title.upper())
            head.setObjectName("PanelTitle")
            outer.addWidget(head)

        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(6)
        self._grid.setColumnMinimumWidth(1, 110)
        self._grid.setColumnStretch(0, 1)
        self._grid.setColumnStretch(1, 0)
        outer.addLayout(self._grid)

    # -- rows --------------------------------------------------------------
    def add(
        self,
        name: str,
        value: float,
        minimum: float = -1e12,
        maximum: float = 1e12,
        unit: str = "",
        decimals: int = 4,
        step: float = 0.1,
    ) -> QDoubleSpinBox:
        """Add a numeric parameter row and return its spin box."""
        sb = QDoubleSpinBox()
        sb.setRange(minimum, maximum)
        sb.setDecimals(decimals)
        sb.setSingleStep(step)
        sb.setValue(value)
        if unit:
            sb.setSuffix(f" {unit}")
        sb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sb.setKeyboardTracking(False)
        self._grid.addWidget(self._label_for(name), self._grid.rowCount(), 0)
        self._grid.addWidget(sb, self._grid.rowCount() - 1, 1)
        self._fields[name] = sb
        return sb

    def add_text(self, name: str, text: str = "", placeholder: str = "") -> QLineEdit:
        """Add a free-text parameter row and return its line edit."""
        edit = QLineEdit(text)
        edit.setPlaceholderText(placeholder)
        self._grid.addWidget(self._label_for(name), self._grid.rowCount(), 0)
        self._grid.addWidget(edit, self._grid.rowCount() - 1, 1)
        self._texts[name] = edit
        return edit

    def add_choice(self, name: str, options: Sequence[str], current: int = 0) -> QComboBox:
        """Add a drop-down parameter row and return its combo box."""
        combo = QComboBox()
        for opt in options:
            combo.addItem(opt)
        if 0 <= current < combo.count():
            combo.setCurrentIndex(current)
        self._grid.addWidget(self._label_for(name), self._grid.rowCount(), 0)
        self._grid.addWidget(combo, self._grid.rowCount() - 1, 1)
        self._choices[name] = combo
        return combo

    @staticmethod
    def _label_for(name: str) -> QLabel:
        lbl = QLabel(name)
        lbl.setObjectName("MutedLabel")
        lbl.setToolTip(name)
        return lbl

    # -- access ------------------------------------------------------------
    def get(self, name: str, default: float = 0.0) -> float:
        sb = self._fields.get(name)
        return sb.value() if sb is not None else default

    def text(self, name: str, default: str = "") -> str:
        edit = self._texts.get(name)
        return edit.text() if edit is not None else default

    def choice(self, name: str, default: int = 0) -> int:
        combo = self._choices.get(name)
        return combo.currentIndex() if combo is not None else default

    def values(self) -> dict[str, float]:
        return {k: sb.value() for k, sb in self._fields.items()}


class DockPanel(QFrame):
    """A titled panel with a header strip — the framing unit of a lab page."""

    def __init__(
        self,
        title: str,
        hint: str = "",
        parent: Optional[QWidget] = None,
        margins: tuple[int, int, int, int] = (12, 10, 12, 12),
    ):
        super().__init__(parent)
        self.setObjectName("Panel")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.header = QFrame()
        self.header.setObjectName("PanelHeader")
        self.header.setFixedHeight(28)
        hrow = QHBoxLayout(self.header)
        hrow.setContentsMargins(11, 0, 11, 0)
        hrow.setSpacing(8)
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("PanelTitle")
        hrow.addWidget(self.title_label)
        hrow.addStretch(1)
        self.hint_label = QLabel(hint)
        self.hint_label.setObjectName("PanelHint")
        hrow.addWidget(self.hint_label)
        outer.addWidget(self.header)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(*margins)
        self.body_layout.setSpacing(9)
        outer.addWidget(self.body, 1)

    def set_hint(self, text: str) -> None:
        self.hint_label.setText(text)

    def set_title(self, text: str) -> None:
        self.title_label.setText(text.upper())

    def add(self, widget: QWidget, stretch: int = 0) -> None:
        self.body_layout.addWidget(widget, stretch)


class StatTile(QFrame):
    """A compact metric readout used on dashboards."""

    def __init__(
        self,
        label: str,
        value: str = "—",
        unit: str = "",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setMinimumWidth(140)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 11)
        lay.setSpacing(2)

        self.label = QLabel(label.upper())
        self.label.setObjectName("MetricLabel")
        lay.addWidget(self.label)

        row = QHBoxLayout()
        row.setSpacing(5)
        self.value = QLabel(value)
        self.value.setObjectName("MetricValue")
        row.addWidget(self.value)
        self.unit = QLabel(unit)
        self.unit.setObjectName("CaptionLabel")
        row.addWidget(self.unit, 0, Qt.AlignBottom)
        row.addStretch(1)
        lay.addLayout(row)

    def set_value(self, value: str, unit: str = "") -> None:
        self.value.setText(value)
        if unit:
            self.unit.setText(unit)


class ReadoutRow(QWidget):
    """A single monospace key/value pair for instrument-style status strips."""

    def __init__(
        self,
        key: str,
        value: str = "—",
        parent: Optional[QWidget] = None,
        value_color: str = "",
    ):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.key = QLabel(key)
        self.key.setObjectName("ReadoutKey")
        lay.addWidget(self.key)

        self.value = QLabel(value)
        self.value.setObjectName("Readout")
        if value_color:
            self.value.setStyleSheet(f"color: {value_color};")
        lay.addWidget(self.value)
        lay.addStretch(1)

    def set_value(self, value: str, color: str = "") -> None:
        self.value.setText(value)
        if color:
            self.value.setStyleSheet(f"color: {color};")


class ToolbarButton(QPushButton):
    """A compact toolbar action with an icon and a short label."""

    def __init__(
        self,
        text: str,
        icon_name: str = "",
        tooltip: str = "",
        parent: Optional[QWidget] = None,
        checkable: bool = False,
    ):
        super().__init__(text, parent)
        self.setObjectName("ToolbarButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(checkable)
        if icon_name:
            self.setIcon(icon(icon_name, color=TEXT_SECONDARY, size=16))
            self.setIconSize(self.iconSize())
        if tooltip:
            self.setToolTip(tooltip)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
