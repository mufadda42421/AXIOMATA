"""Collapsible left navigation sidebar (premium redesign).

A clean rail with grouped, icon-led navigation buttons. Supports collapsing to
an icon-only rail with tooltips, active-state highlighting, and a footer showing
storage status plus settings/help shortcuts.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from .icons import icon
from .navigation import GROUP_ORDER, GROUP_TITLES, NAV_ITEMS, NavItem
from .themes.theme import ACCENT, TEXT_DIM, TEXT_SECONDARY

_EXPANDED_WIDTH = 232
_COLLAPSED_WIDTH = 52


class _NavButton(QPushButton):
    """A navigation button with an icon + label that adapts to collapse."""

    def __init__(self, item: NavItem, on_click):
        super().__init__()
        self.item = item
        self.setObjectName("NavButton")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clicked.connect(lambda: on_click(item.key))
        self.setToolTip(item.label)
        self._collapsed = False
        self._apply()

    def _apply(self) -> None:
        if self._collapsed:
            self.setText("")
            self.setIcon(icon(self.item.icon, color=TEXT_SECONDARY, size=19))
            self.setIconSize(self.iconSize())
            self.setToolTip(self.item.label)
        else:
            self.setText(f"   {self.item.label}")
            self.setIcon(icon(self.item.icon, color=TEXT_SECONDARY, size=18))
            self.setIconSize(self.iconSize())

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._apply()


class Sidebar(QWidget):
    """Navigation rail with grouped, checkable icon buttons.

    Emits ``navigate(key)`` when a destination is chosen.
    """

    navigate = Signal(str)
    collapse_toggled = Signal(bool)
    settings_requested = Signal()
    help_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(_EXPANDED_WIDTH)
        self._collapsed = False
        self._shortcut_keys: Optional[list[str]] = None
        self._buttons: dict[str, _NavButton] = {}
        self._active_key: Optional[str] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Brand header
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hrow = QHBoxLayout(header)
        hrow.setContentsMargins(18, 18, 12, 14)
        hrow.setSpacing(10)
        self.brand_icon = QLabel()
        self.brand_icon.setPixmap(icon("atom", color=ACCENT, size=22).pixmap(22, 22))
        hrow.addWidget(self.brand_icon)
        self.brand_text = QLabel("AXIOMATA")
        self.brand_text.setObjectName("BrandMark")
        hrow.addWidget(self.brand_text, 1)
        self.collapse_btn = QPushButton()
        self.collapse_btn.setObjectName("CollapseButton")
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.setToolTip("Collapse sidebar")
        self._update_collapse_icon()
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        hrow.addWidget(self.collapse_btn)
        root.addWidget(header)

        # Scrollable nav area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        self._nav_container = QWidget()
        self._nav_container.setStyleSheet("background: transparent;")
        self._nav_layout = QVBoxLayout(self._nav_container)
        self._nav_layout.setContentsMargins(10, 4, 10, 8)
        self._nav_layout.setSpacing(2)
        scroll.setWidget(self._nav_container)
        root.addWidget(scroll, 1)

        # Footer: storage + settings + help
        footer = QFrame()
        footer.setObjectName("SidebarFooter")
        footer.setFixedHeight(52)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(14, 8, 14, 8)
        fl.setSpacing(4)
        self.storage_dot = QLabel()
        self.storage_dot.setObjectName("Dot")
        self.storage_dot.setFixedSize(7, 7)
        self.storage_dot.setStyleSheet(f"background-color: {ACCENT}; border-radius: 3px;")
        self.storage_label = QLabel("Local storage")
        self.storage_label.setObjectName("StorageLabel")
        fl.addWidget(self.storage_dot)
        fl.addWidget(self.storage_label, 1)
        self.help_btn = QPushButton()
        self.help_btn.setObjectName("CollapseButton")
        self.help_btn.setIcon(icon("help", color=TEXT_SECONDARY, size=17))
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setToolTip("Help & Documentation")
        self.help_btn.clicked.connect(self.help_requested.emit)
        fl.addWidget(self.help_btn)
        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("CollapseButton")
        self.settings_btn.setIcon(icon("settings", color=TEXT_SECONDARY, size=17))
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        fl.addWidget(self.settings_btn)
        root.addWidget(footer)

        self._group_buttons = QButtonGroup(self)
        self._group_buttons.setExclusive(True)
        self._build_nav()

    def _build_nav(self) -> None:
        while self._nav_layout.count():
            item = self._nav_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        self._buttons.clear()

        fav = {k: i for i, k in enumerate(self._shortcut_keys or [])}
        for group in GROUP_ORDER:
            items = [it for it in NAV_ITEMS if it.group == group]
            if not items:
                continue
            # Stable-sort favourites first within group.
            items.sort(key=lambda it: fav.get(it.key, 999))
            header = QLabel(GROUP_TITLES.get(group, ""))
            header.setObjectName("NavSection")
            header.setProperty("groupHeader", True)
            self._nav_layout.addWidget(header)
            for item in items:
                btn = _NavButton(item, self.navigate.emit)
                btn.set_collapsed(self._collapsed)
                self._group_buttons.addButton(btn)
                self._nav_layout.addWidget(btn)
                self._buttons[item.key] = btn

        self._nav_layout.addStretch(1)
        self._restore_active()
        self._apply_collapse_visibility()

    def _ordered_items(self) -> list[NavItem]:
        fav = {k: i for i, k in enumerate(self._shortcut_keys or [])}
        items = list(NAV_ITEMS)
        items.sort(key=lambda it: (GROUP_ORDER.index(it.group) if it.group in GROUP_ORDER else 99,
                                   fav.get(it.key, 999)))
        return items

    def set_shortcuts(self, shortcut_keys: Optional[list[str]]) -> None:
        self._shortcut_keys = shortcut_keys
        self._build_nav()

    def set_active(self, key: str) -> None:
        self._active_key = key
        self._restore_active()

    def _restore_active(self) -> None:
        for k, btn in self._buttons.items():
            btn.setChecked(k == self._active_key)

    # -- collapse ----------------------------------------------------------
    def toggle_collapse(self) -> None:
        self.set_collapsed(not self._collapsed)

    def _update_collapse_icon(self) -> None:
        name = "chevron_right" if not self._collapsed else "chevron_left"
        # When expanded, show a "collapse to rail" (left chevron); when collapsed,
        # show a "expand" (right chevron).
        name = "chevron_left" if not self._collapsed else "chevron_right"
        self.collapse_btn.setIcon(icon(name, color=TEXT_SECONDARY, size=16))

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self.setFixedWidth(_COLLAPSED_WIDTH if collapsed else _EXPANDED_WIDTH)
        self.brand_text.setVisible(not collapsed)
        self.storage_label.setVisible(not collapsed)
        self._update_collapse_icon()
        for btn in self._buttons.values():
            btn.set_collapsed(collapsed)
        self._apply_collapse_visibility()
        self.collapse_toggled.emit(collapsed)

    def _apply_collapse_visibility(self) -> None:
        for i in range(self._nav_layout.count()):
            w = self._nav_layout.itemAt(i).widget()
            if w is not None and w.property("groupHeader"):
                w.setVisible(not self._collapsed)

    # -- storage footer ----------------------------------------------------
    def set_storage_status(self, used_bytes: int) -> None:
        from .themes.theme import TEXT_DIM as _dim
        mb = used_bytes / (1024 * 1024)
        if mb < 1024:
            self.storage_label.setText(f"Local · {mb:.1f} MB")
        else:
            self.storage_label.setText(f"Local · {mb/1024:.2f} GB")