"""Scientific Library page: offline reference for constants, units, formulas."""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

from ..core.application import AppContext
from ..ui.panels.base_page import BasePage
from ..scientific_library.reference_data import (
    FORMULAS, PHYSICAL_CONSTANTS, SI_BASE_UNITS, SI_DERIVED_UNITS,
    UNIT_CONVERSIONS, convert_temperature,
)


class LibraryPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Scientific Library",
                         "Offline reference: physical constants, SI units, formulas & conversions.",
                         parent)
        self.ctx = ctx
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_constants(), "Physical Constants")
        self.tabs.addTab(self._build_formulas(), "Formulas")
        self.tabs.addTab(self._build_units(), "SI Units")
        self.tabs.addTab(self._build_converter(), "Unit Converter")
        self.add_body_widget(self.tabs, 1)

    def _build_constants(self) -> QWidget:
        table = QTableWidget(len(PHYSICAL_CONSTANTS), 4)
        table.setHorizontalHeaderLabels(["Name", "Symbol", "Value", "Unit"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        for r, c in enumerate(PHYSICAL_CONSTANTS):
            table.setItem(r, 0, QTableWidgetItem(c.name))
            table.setItem(r, 1, QTableWidgetItem(c.symbol))
            table.setItem(r, 2, QTableWidgetItem(f"{c.value:.6e}"))
            table.setItem(r, 3, QTableWidgetItem(c.unit))
        table.setColumnWidth(0, 240)
        table.setColumnWidth(1, 60)
        table.setColumnWidth(2, 160)
        note = QLabel(
            "Values use SI/CODATA definitions where available. Sources are noted "
            "in the constants module. These are reference values, not measurements."
        )
        note.setObjectName("MutedLabel")
        note.setWordWrap(True)
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(table, 1)
        lay.addWidget(note)
        return w

    def _build_formulas(self) -> QWidget:
        # Group formulas by category with a combo filter.
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        top = QHBoxLayout()
        top.addWidget(QLabel("Category:"))
        self.formula_filter = QComboBox()
        self.formula_filter.addItem("All", "all")
        categories = sorted({f.category for f in FORMULAS})
        for cat in categories:
            self.formula_filter.addItem(cat, cat)
        self.formula_filter.currentIndexChanged.connect(self._filter_formulas)
        top.addWidget(self.formula_filter)
        top.addStretch(1)
        lay.addLayout(top)
        self.formula_list = QTextEdit()
        self.formula_list.setReadOnly(True)
        self.formula_list.setStyleSheet("font-family: Consolas, monospace; font-size:13px;")
        lay.addWidget(self.formula_list, 1)
        self._filter_formulas()
        return container

    def _filter_formulas(self) -> None:
        cat = self.formula_filter.currentData()
        lines = []
        current = None
        for f in FORMULAS:
            if cat != "all" and f.category != cat:
                continue
            if f.category != current:
                current = f.category
                lines.append(f"\n━━━ {current} ━━━")
            lines.append(f"  {f.name}")
            lines.append(f"     {f.expression}")
            lines.append(f"     {f.description}")
        self.formula_list.setPlainText("\n".join(lines))

    def _build_units(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        base = QTableWidget(len(SI_BASE_UNITS), 3)
        base.setHorizontalHeaderLabels(["Quantity", "Unit", "Symbol"])
        base.verticalHeader().setVisible(False)
        base.setEditTriggers(QTableWidget.NoEditTriggers)
        for r, (q, name, sym) in enumerate(SI_BASE_UNITS):
            base.setItem(r, 0, QTableWidgetItem(q))
            base.setItem(r, 1, QTableWidgetItem(name))
            base.setItem(r, 2, QTableWidgetItem(sym))
        lay.addWidget(QLabel("SI Base Units"))
        lay.addWidget(base, 1)
        derived = QTableWidget(len(SI_DERIVED_UNITS), 4)
        derived.setHorizontalHeaderLabels(["Quantity", "Unit", "Symbol", "In base units"])
        derived.verticalHeader().setVisible(False)
        derived.setEditTriggers(QTableWidget.NoEditTriggers)
        for r, (q, name, sym, base_u) in enumerate(SI_DERIVED_UNITS):
            derived.setItem(r, 0, QTableWidgetItem(q))
            derived.setItem(r, 1, QTableWidgetItem(name))
            derived.setItem(r, 2, QTableWidgetItem(sym))
            derived.setItem(r, 3, QTableWidgetItem(base_u))
        lay.addWidget(QLabel("SI Derived Units"))
        lay.addWidget(derived, 2)
        return container

    def _build_converter(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        form = QFormLayout()
        self.conv_cat = QComboBox()
        cats = ["Length", "Mass", "Time", "Energy", "Pressure", "Power", "Angle"]
        self.conv_cat.addItems(cats)
        self.conv_cat.currentIndexChanged.connect(self._reload_conversions)
        form.addRow("Category", self.conv_cat)

        self.conv_from = QComboBox()
        self.conv_to = QComboBox()
        form.addRow("From", self.conv_from)
        form.addRow("To", self.conv_to)

        self.conv_value = QDoubleSpinBox()
        self.conv_value.setRange(-1e18, 1e18)
        self.conv_value.setDecimals(6)
        self.conv_value.setValue(1.0)
        self.conv_value.valueChanged.connect(self._convert)
        form.addRow("Value", self.conv_value)

        # Temperature special-case row
        self.temp_cat = QComboBox()
        self.temp_cat.addItem("Temperature", "temp")
        # We'll add a separate temperature mini-form below.
        lay.addLayout(form)

        # Temperature converter
        tbox = QWidget()
        tl = QFormLayout(tbox)
        self.t_from = QComboBox(); self.t_from.addItems(["C", "F", "K"])
        self.t_to = QComboBox(); self.t_to.addItems(["C", "F", "K"]); self.t_to.setCurrentIndex(2)
        self.t_value = QDoubleSpinBox(); self.t_value.setRange(-1e6, 1e6); self.t_value.setDecimals(3); self.t_value.setValue(0)
        self.t_value.valueChanged.connect(self._convert_temp)
        tl.addRow("Temperature from", self.t_from)
        tl.addRow("to", self.t_to)
        tl.addRow("Value", self.t_value)
        lay.addWidget(QLabel("Temperature (C / F / K)"))
        lay.addWidget(tbox)

        self.conv_result = QLabel("Result: —")
        self.conv_result.setObjectName("H2")
        lay.addWidget(self.conv_result)
        lay.addStretch(1)
        self._reload_conversions()
        return container

    def _reload_conversions(self) -> None:
        cat = self.conv_cat.currentText()
        self.conv_from.clear()
        self.conv_to.clear()
        convs = [u for u in UNIT_CONVERSIONS if u.category == cat]
        for u in convs:
            self.conv_from.addItem(f"{u.from_unit} → {u.to_unit}", (u.factor, u.from_unit, u.to_unit))
        # Populate "to" with all units seen in this category.
        units = sorted({u.from_unit for u in convs} | {u.to_unit for u in convs})
        for unit in units:
            self.conv_to.addItem(unit, unit)
        self._convert()

    def _convert(self) -> None:
        data = self.conv_from.currentData()
        to_unit = self.conv_to.currentData()
        if not data or not to_unit:
            self.conv_result.setText("Result: —")
            return
        factor, from_unit, _default_to = data
        value = self.conv_value.value()
        # Convert value in from_unit to to_unit.
        # First convert to base by dividing by factor (factor converts from->to),
        # but we need a common base. Simpler: build a unit->SI map.
        result = self._convert_via_base(value, from_unit, to_unit, self.conv_cat.currentText())
        self.conv_result.setText(
            f"{value:.6g} {from_unit} = {result:.6g} {to_unit}"
        )

    def _convert_via_base(self, value: float, from_unit: str, to_unit: str, category: str) -> float:
        # Build conversion factors to a base unit per category.
        base_map = {
            "Length": "m", "Mass": "kg", "Time": "s", "Energy": "J",
            "Pressure": "Pa", "Power": "W", "Angle": "rad",
        }
        base = base_map.get(category, "")
        if not base:
            return value
        # Gather all factors for this category; each maps X -> base with factor.
        factors_to_base: dict[str, float] = {}
        for u in UNIT_CONVERSIONS:
            if u.category != category:
                continue
            # u: from_unit -> to_unit with factor. Store both directions where
            # one side is the base unit.
            if u.to_unit == base:
                factors_to_base[u.from_unit] = u.factor
            elif u.from_unit == base:
                # base -> to_unit: value_in_base / factor = value_in_to
                factors_to_base[u.to_unit] = 1.0 / u.factor
        if from_unit == base:
            base_val = value
        elif from_unit in factors_to_base:
            base_val = value * factors_to_base[from_unit]
        else:
            return value
        if to_unit == base:
            return base_val
        if to_unit in factors_to_base:
            return base_val / factors_to_base[to_unit]
        return value

    def _convert_temp(self) -> None:
        val = self.t_value.value()
        res = convert_temperature(val, self.t_from.currentText(), self.t_to.currentText())
        self.conv_result.setText(
            f"{val:.4g} {self.t_from.currentText()} = {res:.4g} {self.t_to.currentText()}"
        )