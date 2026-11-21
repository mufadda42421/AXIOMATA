"""AXIOMATA theme: scientific-instrument design system.

A single source of truth for the palette and the application-wide stylesheet.

The design language targets professional scientific software (MATLAB,
Origin, Igor, COMSOL) rather than consumer apps:

* **Density over comfort** — a 12 px base face, tight 1 px hairlines and
  3 px corner radii so that tables of numbers fit on screen.
* **Instrument neutrality** — graphite surfaces instead of tinted "product"
  blues, letting the data and the single accent colour carry the meaning.
* **Numeric typography** — monospace faces for every readout, quantity, and
  equation so digits align in columns.
* **Persistent chrome** — a menu bar, a tool bar, a tabbed workspace and a
  status bar, matching the working rhythm of laboratory software.

Two palettes ship: ``dark`` (the default instrument console) and ``light``
(a high-legibility "lab paper" palette used for printing and projectors).

Usage::

    from .themes.theme import build_stylesheet, palette

    app.setStyleSheet(build_stylesheet("dark"))
    accent = palette().ACCENT
"""
from __future__ import annotations

from dataclasses import dataclass, replace

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Palette:
    """A complete set of colour tokens for one theme."""

    name: str
    BG: str                 # application background
    BG_SECONDARY: str       # chrome background (menu bar, tool bar, status bar)
    SIDEBAR_BG: str         # navigation rail
    PANEL: str              # panel / card surface
    PANEL_ELEVATED: str     # raised surface (inputs on panels, hovered rows)
    BORDER: str             # visible border
    BORDER_SOFT: str        # hairline / grid border
    INPUT_BG: str           # editable field background
    ACCENT: str             # primary accent
    ACCENT_2: str           # secondary accent
    ACCENT_DIM: str         # accent, low emphasis
    ACCENT_SOFT: str        # accent wash (selected row)
    ACCENT_TEXT: str        # text drawn on top of ACCENT
    TEXT: str               # primary text
    TEXT_SECONDARY: str     # secondary text
    TEXT_DIM: str           # tertiary / disabled text
    SUCCESS: str
    WARNING: str
    ERROR: str
    HIGHLIGHT: str          # active row / selection fill
    GRID_LINE: str          # table grid line
    HEADER_BG: str          # table header band
    SELECTION: str          # selection fill in tables and lists
    CHART_BG: str           # matplotlib figure background
    CHART_AX_BG: str        # matplotlib axes background

    # Legacy aliases preserved for modules that imported the old names.
    @property
    def TEXT_MUTED(self) -> str:  # noqa: N802 - legacy alias
        return self.TEXT_DIM

    @property
    def BG_DEEP(self) -> str:  # noqa: N802 - legacy alias
        return self.BG

    @property
    def BG_PANEL(self) -> str:  # noqa: N802 - legacy alias
        return self.PANEL

    @property
    def BG_PANEL_ALT(self) -> str:  # noqa: N802 - legacy alias
        return self.PANEL_ELEVATED

    @property
    def BG_INPUT(self) -> str:  # noqa: N802 - legacy alias
        return self.INPUT_BG

    @property
    def DANGER(self) -> str:  # noqa: N802 - legacy alias
        return self.ERROR

    @property
    def ACCENT_BLUE(self) -> str:  # noqa: N802 - legacy alias
        return self.ACCENT_2


DARK = Palette(
    name="dark",
    BG="#0E1116",
    BG_SECONDARY="#14181F",
    SIDEBAR_BG="#10141A",
    PANEL="#171C24",
    PANEL_ELEVATED="#1E242E",
    BORDER="#2C343F",
    BORDER_SOFT="#222932",
    INPUT_BG="#0A0D12",
    ACCENT="#35C9E8",
    ACCENT_2="#7C9CFF",
    ACCENT_DIM="#1C6C7D",
    ACCENT_SOFT="#10333E",
    ACCENT_TEXT="#06121A",
    TEXT="#DDE6F2",
    TEXT_SECONDARY="#94A3B5",
    TEXT_DIM="#5E6B7C",
    SUCCESS="#4ECB9C",
    WARNING="#E5B45C",
    ERROR="#EF6F76",
    HIGHLIGHT="#17303F",
    GRID_LINE="#212832",
    HEADER_BG="#1B212B",
    SELECTION="#1D3D4E",
    CHART_BG="#171C24",
    CHART_AX_BG="#0E1218",
)

LIGHT = Palette(
    name="light",
    BG="#EFF2F6",
    BG_SECONDARY="#FFFFFF",
    SIDEBAR_BG="#E6EAF0",
    PANEL="#FFFFFF",
    PANEL_ELEVATED="#F4F7FA",
    BORDER="#C3CCD8",
    BORDER_SOFT="#DCE2EA",
    INPUT_BG="#FFFFFF",
    ACCENT="#0E86A8",
    ACCENT_2="#4A63C8",
    ACCENT_DIM="#8FCEDD",
    ACCENT_SOFT="#D8EEF5",
    ACCENT_TEXT="#FFFFFF",
    TEXT="#16202B",
    TEXT_SECONDARY="#4C5966",
    TEXT_DIM="#7B8896",
    SUCCESS="#1F9D6B",
    WARNING="#A9741A",
    ERROR="#C4373D",
    HIGHLIGHT="#D5E8F1",
    GRID_LINE="#E1E7EE",
    HEADER_BG="#E9EDF3",
    SELECTION="#CFE6EF",
    CHART_BG="#FFFFFF",
    CHART_AX_BG="#F7F9FB",
)

PALETTES: dict[str, Palette] = {"dark": DARK, "light": LIGHT}

_ACTIVE: Palette = DARK


def palette() -> Palette:
    """Return the palette currently in effect."""
    return _ACTIVE


def set_theme(name: str) -> Palette:
    """Activate a palette by name and return it.

    Unknown names fall back to ``dark`` rather than raising, so a corrupt
    settings file can never prevent the application from starting.
    """
    global _ACTIVE
    _ACTIVE = PALETTES.get(name, DARK)
    return _ACTIVE


def with_palette(name: str) -> Palette:
    """Return a palette without activating it (for previews/print output)."""
    return PALETTES.get(name, DARK)


# --------------------------------------------------------------------------
# Module-level convenience constants (bound to the active palette)
# --------------------------------------------------------------------------
# These are kept for the many modules that do ``from .themes.theme import ACCENT``.
# They are refreshed by ``refresh_globals()`` whenever the active theme changes.

BG = DARK.BG
BG_SECONDARY = DARK.BG_SECONDARY
SIDEBAR_BG = DARK.SIDEBAR_BG
PANEL = DARK.PANEL
PANEL_ELEVATED = DARK.PANEL_ELEVATED
BORDER = DARK.BORDER
BORDER_SOFT = DARK.BORDER_SOFT
BG_INPUT = DARK.INPUT_BG
INPUT_BG = DARK.INPUT_BG
ACCENT = DARK.ACCENT
ACCENT_2 = DARK.ACCENT_2
ACCENT_DIM = DARK.ACCENT_DIM
ACCENT_SOFT = DARK.ACCENT_SOFT
ACCENT_TEXT = DARK.ACCENT_TEXT
TEXT = DARK.TEXT
TEXT_SECONDARY = DARK.TEXT_SECONDARY
TEXT_DIM = DARK.TEXT_DIM
TEXT_MUTED = DARK.TEXT_DIM
SUCCESS = DARK.SUCCESS
WARNING = DARK.WARNING
ERROR = DARK.ERROR
DANGER = DARK.ERROR
HIGHLIGHT = DARK.HIGHLIGHT
GRID_LINE = DARK.GRID_LINE
HEADER_BG = DARK.HEADER_BG
SELECTION = DARK.SELECTION
CHART_BG = DARK.CHART_BG
CHART_AX_BG = DARK.CHART_AX_BG
ACCENT_BLUE = DARK.ACCENT_2
BG_DEEP = DARK.BG
BG_PANEL = DARK.PANEL
BG_PANEL_ALT = DARK.PANEL_ELEVATED
LIGHT_HOVER = "rgba(53,201,232,0.12)"
LIGHT_BACKGROUND = "rgba(255,255,255,0.03)"

# Type stacks
FONT_STACK = '"Inter", "Segoe UI Variable Text", "Segoe UI", system-ui, sans-serif'
MONO_STACK = '"Cascadia Mono", "JetBrains Mono", "Consolas", "DejaVu Sans Mono", monospace'

# Density metrics (kept as constants so every panel measures identically)
BASE_FONT_PX = 12
SMALL_FONT_PX = 11
RADIUS = 4
ROW_HEIGHT = 26


def refresh_globals() -> Palette:
    """Re-bind the module-level colour constants to the active palette."""
    global BG, BG_SECONDARY, SIDEBAR_BG, PANEL, PANEL_ELEVATED, BORDER
    global BORDER_SOFT, BG_INPUT, INPUT_BG, ACCENT, ACCENT_2, ACCENT_DIM
    global ACCENT_SOFT, ACCENT_TEXT, TEXT, TEXT_SECONDARY, TEXT_DIM
    global TEXT_MUTED, SUCCESS, WARNING, ERROR, DANGER, HIGHLIGHT
    global GRID_LINE, HEADER_BG, SELECTION, CHART_BG, CHART_AX_BG, ACCENT_BLUE
    global BG_DEEP, BG_PANEL, BG_PANEL_ALT

    p = _ACTIVE
    BG, BG_SECONDARY, SIDEBAR_BG = p.BG, p.BG_SECONDARY, p.SIDEBAR_BG
    PANEL, PANEL_ELEVATED = p.PANEL, p.PANEL_ELEVATED
    BORDER, BORDER_SOFT = p.BORDER, p.BORDER_SOFT
    BG_INPUT = INPUT_BG = p.INPUT_BG
    ACCENT, ACCENT_2 = p.ACCENT, p.ACCENT_2
    ACCENT_DIM, ACCENT_SOFT, ACCENT_TEXT = p.ACCENT_DIM, p.ACCENT_SOFT, p.ACCENT_TEXT
    TEXT, TEXT_SECONDARY, TEXT_DIM = p.TEXT, p.TEXT_SECONDARY, p.TEXT_DIM
    TEXT_MUTED = p.TEXT_DIM
    SUCCESS, WARNING, ERROR, DANGER = p.SUCCESS, p.WARNING, p.ERROR, p.ERROR
    HIGHLIGHT, GRID_LINE = p.HIGHLIGHT, p.GRID_LINE
    HEADER_BG, SELECTION = p.HEADER_BG, p.SELECTION
    CHART_BG, CHART_AX_BG = p.CHART_BG, p.CHART_AX_BG
    ACCENT_BLUE = p.ACCENT_2
    BG_DEEP, BG_PANEL, BG_PANEL_ALT = p.BG, p.PANEL, p.PANEL_ELEVATED
    return p


# --------------------------------------------------------------------------
# Stylesheet
# --------------------------------------------------------------------------

_QSS_TEMPLATE = """
/* ============================================================
   AXIOMATA — scientific instrument theme ({theme_name})
   ============================================================ */
* {{
    font-family: {font_stack};
    font-size: {base_font}px;
    color: {text};
}}
QMainWindow, QWidget#RootWidget {{
    background-color: {bg};
}}
QWidget {{
    color: {text};
    background-color: transparent;
}}
QDialog {{
    background-color: {bg};
}}

/* ---------- Typography ---------- */
QLabel {{
    color: {text};
    background: transparent;
}}
QLabel#MutedLabel {{
    color: {text_secondary};
}}
QLabel#CaptionLabel {{
    color: {text_dim};
    font-size: {small_font}px;
}}
QLabel#H1 {{
    font-size: 17px;
    font-weight: 650;
    letter-spacing: -0.2px;
}}
QLabel#H2 {{
    font-size: 13px;
    font-weight: 650;
}}
QLabel#SectionTitle {{
    font-size: {small_font}px;
    font-weight: 700;
    color: {text_secondary};
    letter-spacing: 1.0px;
}}
QLabel#Accent {{
    color: {accent};
}}
QLabel#Mono {{
    font-family: {mono_stack};
    font-size: {base_font}px;
}}
QLabel#Readout {{
    font-family: {mono_stack};
    font-size: {base_font}px;
    color: {accent};
}}
QLabel#ReadoutKey {{
    font-family: {mono_stack};
    font-size: {base_font}px;
    color: {text_secondary};
}}
QLabel#MetricValue {{
    font-family: {mono_stack};
    font-size: 21px;
    font-weight: 600;
    color: {text};
}}
QLabel#MetricLabel {{
    font-size: {small_font}px;
    color: {text_dim};
    letter-spacing: 0.5px;
}}
QLabel#Equation {{
    font-family: {mono_stack};
    font-size: {base_font}px;
    color: {text_secondary};
    background: transparent;
}}

/* ---------- Panels, cards, docks ---------- */
QFrame#Panel, QFrame#Card {{
    background-color: {panel};
    border: 1px solid {border_soft};
    border-radius: {radius}px;
}}
QFrame#PanelAlt {{
    background-color: {panel_elevated};
    border: 1px solid {border_soft};
    border-radius: {radius}px;
}}
QFrame#PanelHeader {{
    background-color: {header_bg};
    border: none;
    border-bottom: 1px solid {border_soft};
}}
QLabel#PanelTitle {{
    font-size: {small_font}px;
    font-weight: 700;
    letter-spacing: 1.0px;
    color: {text_secondary};
    padding: 0px;
}}
QLabel#PanelHint {{
    font-size: {small_font}px;
    color: {text_dim};
}}
QFrame#Separator, QFrame#Divider {{
    background-color: {border_soft};
    max-height: 1px;
    border: none;
}}
QFrame#EquationBlock {{
    background-color: {input_bg};
    border: 1px solid {border_soft};
    border-left: 2px solid {accent_dim};
    border-radius: {radius}px;
}}
QFrame#Toast {{
    background-color: {panel_elevated};
    border: 1px solid {border};
    border-left: 3px solid {accent};
    border-radius: {radius}px;
}}

/* ---------- Menu bar ---------- */
QMenuBar {{
    background-color: {bg_secondary};
    border-bottom: 1px solid {border_soft};
    padding: 2px 4px;
    font-size: {base_font}px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 5px 11px;
    border-radius: {radius}px;
    color: {text_secondary};
}}
QMenuBar::item:selected {{
    background-color: {panel_elevated};
    color: {text};
}}
QMenuBar::item:pressed {{
    background-color: {accent_soft};
    color: {accent};
}}

/* ---------- Tool bar ---------- */
QToolBar {{
    background-color: {bg_secondary};
    border: none;
    border-bottom: 1px solid {border_soft};
    padding: 3px 6px;
    spacing: 2px;
}}
QToolBar::separator {{
    background-color: {border};
    width: 1px;
    margin: 4px 7px;
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: {radius}px;
    padding: 4px;
    color: {text_secondary};
}}
QToolButton:hover {{
    background-color: {panel_elevated};
    border-color: {border};
    color: {text};
}}
QToolButton:pressed, QToolButton:checked {{
    background-color: {accent_soft};
    border-color: {accent_dim};
    color: {accent};
}}
QToolButton::menu-indicator {{
    image: none;
    width: 0px;
}}

/* ---------- Top bar ---------- */
QFrame#TopBar {{
    background-color: {bg_secondary};
    border-bottom: 1px solid {border_soft};
}}
QLabel#Brand {{
    font-size: 14px;
    font-weight: 700;
    color: {accent};
    letter-spacing: 2.2px;
}}
QLabel#WorkspaceName {{
    color: {text_secondary};
    font-size: {base_font}px;
    letter-spacing: 0.2px;
}}
QPushButton#HeaderButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: {radius}px;
    padding: 4px 8px;
    color: {text_secondary};
    font-size: {base_font}px;
}}
QPushButton#HeaderButton:hover {{
    background-color: {panel_elevated};
    border-color: {border};
    color: {text};
}}

/* ---------- Sidebar ---------- */
QFrame#Sidebar {{
    background-color: {sidebar_bg};
    border-right: 1px solid {border_soft};
}}
QLabel#BrandMark {{
    font-size: 13px;
    font-weight: 700;
    color: {accent};
    letter-spacing: 1.8px;
}}
QPushButton#NavButton {{
    text-align: left;
    padding: 6px 10px;
    border: none;
    border-left: 2px solid transparent;
    border-radius: 0px;
    background: transparent;
    color: {text_secondary};
    font-size: {base_font}px;
}}
QPushButton#NavButton:hover {{
    background-color: {panel};
    color: {text};
}}
QPushButton#NavButton:checked {{
    background-color: {highlight};
    border-left: 2px solid {accent};
    color: {accent};
    font-weight: 600;
}}
QLabel#NavSection {{
    color: {text_dim};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.0px;
    padding: 11px 10px 3px 10px;
}}
QPushButton#CollapseButton {{
    background: transparent;
    border: none;
    color: {text_secondary};
    border-radius: {radius}px;
    padding: 4px;
    font-size: {base_font}px;
}}
QPushButton#CollapseButton:hover {{
    background-color: {panel_elevated};
    color: {accent};
}}
QFrame#SidebarFooter {{
    background-color: {bg_secondary};
    border-top: 1px solid {border_soft};
}}
QLabel#StorageLabel {{
    color: {text_secondary};
    font-family: {mono_stack};
    font-size: {small_font}px;
}}
QLabel#Dot {{
    background-color: {accent};
    border-radius: 3px;
    min-width: 6px;
    max-width: 6px;
    min-height: 6px;
    max-height: 6px;
}}

/* ---------- Buttons ---------- */
QPushButton {{
    background-color: {panel_elevated};
    border: 1px solid {border};
    border-radius: {radius}px;
    padding: 5px 12px;
    color: {text};
    font-weight: 500;
    min-height: 17px;
}}
QPushButton:hover {{
    border-color: {accent_dim};
    background-color: {panel};
}}
QPushButton:pressed {{
    background-color: {accent_soft};
}}
QPushButton:disabled {{
    color: {text_dim};
    border-color: {border_soft};
    background-color: {panel};
}}
QPushButton#Primary {{
    background-color: {accent};
    color: {accent_text};
    border: 1px solid {accent};
    font-weight: 650;
}}
QPushButton#Primary:hover {{
    background-color: {accent};
    border-color: {text};
}}
QPushButton#Primary:pressed {{
    background-color: {accent_dim};
    border-color: {accent_dim};
}}
QPushButton#Primary:disabled {{
    background-color: {panel_elevated};
    color: {text_dim};
    border-color: {border_soft};
}}
QPushButton#Ghost {{
    background: transparent;
    border: 1px solid {border};
    color: {text_secondary};
}}
QPushButton#Ghost:hover {{
    background-color: {panel_elevated};
    border-color: {accent_dim};
    color: {text};
}}
QPushButton#Danger {{
    background: transparent;
    border: 1px solid {error};
    color: {error};
}}
QPushButton#Danger:hover {{
    background-color: rgba(239,111,118,0.12);
}}
QPushButton#ToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: {radius}px;
    padding: 4px;
}}
QPushButton#ToolButton:hover {{
    background-color: {panel_elevated};
    border-color: {border};
}}
QPushButton#ToolbarButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: {radius}px;
    padding: 4px 8px;
    color: {text_secondary};
    font-size: {base_font}px;
}}
QPushButton#ToolbarButton:hover {{
    background-color: {panel_elevated};
    border-color: {border};
    color: {text};
}}

/* ---------- Inputs ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
    background-color: {input_bg};
    border: 1px solid {border};
    border-radius: {radius}px;
    padding: 4px 8px;
    color: {text};
    selection-background-color: {accent_soft};
    selection-color: {text};
    min-height: 17px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {accent};
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {text_dim};
    background-color: {panel};
}}
QLineEdit#SearchInput {{
    border-radius: 12px;
    padding: 4px 10px 4px 26px;
    background-color: {input_bg};
}}
QTextEdit, QPlainTextEdit {{
    font-family: {mono_stack};
    font-size: {base_font}px;
}}
QComboBox::drop-down {{
    border: none;
    width: 18px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid {text_dim};
    width: 0px;
    height: 0px;
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {panel_elevated};
    border: 1px solid {border};
    selection-background-color: {selection};
    selection-color: {accent};
    outline: none;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: {panel_elevated};
    border: none;
    border-left: 1px solid {border_soft};
    width: 15px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {accent_soft};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: none;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-bottom: 4px solid {text_secondary};
    width: 0px;
    height: 0px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: none;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid {text_secondary};
    width: 0px;
    height: 0px;
}}
QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {{
    border-bottom-color: {accent};
}}

/* ---------- Tables & lists ---------- */
QTableWidget, QTableView, QListWidget, QTreeWidget, QTreeView {{
    background-color: {input_bg};
    border: 1px solid {border_soft};
    border-radius: {radius}px;
    gridline-color: {grid_line};
    color: {text};
    outline: none;
    alternate-background-color: {panel};
    font-size: {base_font}px;
}}
QTableWidget::item, QTableView::item, QListWidget::item {{
    padding: 3px 6px;
    border: none;
}}
QTableWidget::item:selected, QTableView::item:selected,
QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {selection};
    color: {text};
}}
QTableWidget::item:hover, QTableView::item:hover, QListWidget::item:hover {{
    background-color: {panel_elevated};
}}
QHeaderView {{
    background-color: {header_bg};
}}
QHeaderView::section {{
    background-color: {header_bg};
    color: {text_secondary};
    padding: 5px 6px;
    border: none;
    border-right: 1px solid {grid_line};
    border-bottom: 1px solid {border_soft};
    font-size: {small_font}px;
    font-weight: 650;
    letter-spacing: 0.4px;
}}
QHeaderView::section:hover {{
    color: {text};
}}
QTableCornerButton::section {{
    background-color: {header_bg};
    border: none;
    border-right: 1px solid {border_soft};
    border-bottom: 1px solid {border_soft};
}}
QTableView QTableCellIndicator {{
    background-color: {accent};
}}

/* ---------- Tabs (workspace) ---------- */
QTabWidget::pane {{
    border: 1px solid {border_soft};
    border-top: none;
    background: {bg};
}}
QTabBar::tab {{
    background: transparent;
    color: {text_secondary};
    padding: 6px 14px;
    border: none;
    border-right: 1px solid {border_soft};
    font-size: {base_font}px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    background: {panel};
    color: {accent};
    border-bottom: 2px solid {accent};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background: {panel_elevated};
    color: {text};
}}
QTabBar::close-button {{
    image: none;
    subcontrol-position: right;
}}
QTabBar::tab:selected QTabBar::close-button {{
    image: none;
}}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 1px;
}}
QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 4px;
    min-height: 26px;
}}
QScrollBar::handle:vertical:hover {{
    background: {accent_dim};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 1px;
}}
QScrollBar::handle:horizontal {{
    background: {border};
    border-radius: 4px;
    min-width: 26px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {accent_dim};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}

/* ---------- Status bar ---------- */
QStatusBar {{
    background-color: {bg_secondary};
    color: {text_secondary};
    border-top: 1px solid {border_soft};
    font-size: {small_font}px;
}}
QStatusBar::item {{
    border: none;
}}
QStatusBar QLabel {{
    color: {text_secondary};
    font-family: {mono_stack};
    font-size: {small_font}px;
    padding: 0px 8px;
}}
QStatusBar::separator {{
    background-color: {border_soft};
    width: 1px;
    margin: 3px 4px;
}}

/* ---------- Tooltips & menus ---------- */
QToolTip {{
    background-color: {panel_elevated};
    color: {text};
    border: 1px solid {accent_dim};
    padding: 4px 7px;
    border-radius: {radius}px;
    font-size: {small_font}px;
}}
QMenu {{
    background-color: {panel_elevated};
    color: {text};
    border: 1px solid {border};
    border-radius: {radius}px;
    padding: 4px;
}}
QMenu::item {{
    padding: 5px 26px 5px 22px;
    border-radius: 3px;
}}
QMenu::item:selected {{
    background-color: {selection};
    color: {accent};
}}
QMenu::item:disabled {{
    color: {text_dim};
}}
QMenu::separator {{
    height: 1px;
    background: {border_soft};
    margin: 4px 8px;
}}

/* ---------- Group boxes ---------- */
QGroupBox {{
    border: 1px solid {border_soft};
    border-radius: {radius}px;
    margin-top: 9px;
    padding-top: 8px;
    padding-bottom: 8px;
    font-weight: 650;
    font-size: {base_font}px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 9px;
    color: {text_secondary};
    padding: 0px 4px;
    font-size: {small_font}px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

/* ---------- Progress bar ---------- */
QProgressBar {{
    background-color: {input_bg};
    border: 1px solid {border_soft};
    border-radius: 3px;
    text-align: center;
    color: {text_secondary};
    font-size: {small_font}px;
    height: 6px;
}}
QProgressBar::chunk {{
    background-color: {accent};
    border-radius: 3px;
}}

/* ---------- Check / radio ---------- */
QCheckBox, QRadioButton {{
    spacing: 6px;
    font-size: {base_font}px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 13px;
    height: 13px;
}}
QCheckBox::indicator {{
    border: 1px solid {border};
    border-radius: 3px;
    background: {input_bg};
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {accent_dim};
}}
QCheckBox::indicator:checked {{
    border-color: {accent};
    background-color: {accent};
    image: none;
}}
QRadioButton::indicator {{
    border: 1px solid {border};
    border-radius: 7px;
    background: {input_bg};
}}
QRadioButton::indicator:checked {{
    border: 4px solid {accent};
    background: {input_bg};
}}

/* ---------- Splitter ---------- */
QSplitter::handle {{
    background-color: transparent;
}}
QSplitter::handle:horizontal {{
    width: 4px;
}}
QSplitter::handle:vertical {{
    height: 4px;
}}
QSplitter::handle:hover {{
    background-color: {accent_dim};
}}

/* ---------- Notebook (markdown) ---------- */
QTextEdit#MarkdownEditor {{
    font-family: {mono_stack};
    font-size: {base_font}px;
    line-height: 150%;
}}
"""


def build_stylesheet(theme: str | None = None) -> str:
    """Return the full application stylesheet for ``theme``.

    ``theme`` accepts ``"dark"`` (default) or ``"light"``. When omitted the
    currently active palette is used.
    """
    p = PALETTES.get(theme, _ACTIVE) if theme else _ACTIVE
    return _QSS_TEMPLATE.format(
        theme_name=p.name,
        font_stack=FONT_STACK,
        mono_stack=MONO_STACK,
        base_font=BASE_FONT_PX,
        small_font=SMALL_FONT_PX,
        radius=RADIUS,
        bg=p.BG,
        bg_secondary=p.BG_SECONDARY,
        sidebar_bg=p.SIDEBAR_BG,
        panel=p.PANEL,
        panel_elevated=p.PANEL_ELEVATED,
        header_bg=p.HEADER_BG,
        input_bg=p.INPUT_BG,
        border=p.BORDER,
        border_soft=p.BORDER_SOFT,
        grid_line=p.GRID_LINE,
        accent=p.ACCENT,
        accent_2=p.ACCENT_2,
        accent_dim=p.ACCENT_DIM,
        accent_soft=p.ACCENT_SOFT,
        accent_text=p.ACCENT_TEXT,
        text=p.TEXT,
        text_secondary=p.TEXT_SECONDARY,
        text_dim=p.TEXT_DIM,
        success=p.SUCCESS,
        warning=p.WARNING,
        error=p.ERROR,
        highlight=p.HIGHLIGHT,
        selection=p.SELECTION,
    )
