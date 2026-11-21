"""Chemistry Laboratory page.

Tabs:
  * Periodic Table - interactive 18-column grid; click an element for details.
  * Molar Mass - parse a formula, show molar mass and composition.
  * Equation Balancer - balance a chemical equation algebraically.
  * Stoichiometry - compute product mass from reactant mass.

All results are calculations, clearly labelled as such, never laboratory
measurements. Reaction visualisation in this phase is illustrative only.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core.application import AppContext
from ...ui.panels.base_page import BasePage
from ...ui.themes.theme import ACCENT, TEXT_MUTED
from . import calculations as calc
from .periodic_table import CATEGORY_COLORS, ELEMENTS, get_element_by_number, get_element_by_symbol


class ChemistryLabPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Chemistry Laboratory",
                         "Periodic table, molecular calculations & equation balancing — "
                         "theoretical/illustrative, not laboratory predictions.", parent)
        self.ctx = ctx
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_periodic_table(), "Periodic Table")
        self.tabs.addTab(self._build_molar_mass(), "Molar Mass")
        self.tabs.addTab(self._build_balancer(), "Balance Equations")
        self.tabs.addTab(self._build_stoich(), "Stoichiometry")
        self.add_body_widget(self.tabs, 1)

    # -- Periodic table ---------------------------------------------------
    def _build_periodic_table(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Left: the table in a scroll area (18 columns x 9 rows incl. f-block).
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        table_widget = QWidget()
        grid = QGridLayout(table_widget)
        grid.setSpacing(3)
        self.element_buttons: dict[int, QPushButton] = {}

        # Place main-group elements by (period, group).
        for num, el in ELEMENTS.items():
            if el.group == 0:
                continue  # f-block placed separately
            btn = QPushButton(f"{el.symbol}\n{el.number}", )
            btn.setFixedSize(56, 56)
            btn.setToolTip(f"{el.name} ({el.symbol}) — {el.atomic_mass} u")
            color = CATEGORY_COLORS.get(el.category, "#334155")
            btn.setStyleSheet(
                f"QPushButton{{background:{color}; color:#0b1220; border:none;"
                f"border-radius:6px; font-size:11px; font-weight:600;}}"
                f"QPushButton:hover{{border:2px solid #e6edf7;}}"
            )
            btn.clicked.connect(lambda _=False, n=num: self._show_element(n))
            grid.addWidget(btn, el.period - 1, el.group - 1)
            self.element_buttons[num] = btn

        # f-block: lanthanides row 9, actinides row 10 (visual rows 9/10).
        lanthanides = [e for e in ELEMENTS.values() if e.category == "lanthanide"]
        actinides = [e for e in ELEMENTS.values() if e.category == "actinide"]
        lanthanides.sort(key=lambda e: e.number)
        actinides.sort(key=lambda e: e.number)
        for i, el in enumerate(lanthanides):
            btn = self._make_element_button(el)
            grid.addWidget(btn, 8, i + 2)
            self.element_buttons[el.number] = btn
        for i, el in enumerate(actinides):
            btn = self._make_element_button(el)
            grid.addWidget(btn, 9, i + 2)
            self.element_buttons[el.number] = btn

        scroll.setWidget(table_widget)
        lay.addWidget(scroll, 1)

        # Right: element detail panel.
        detail = QGroupBox("Element details")
        detail.setMinimumWidth(240)
        dl = QVBoxLayout(detail)
        self.elem_title = QLabel("Select an element")
        self.elem_title.setObjectName("H2")
        self.elem_detail = QTextEdit()
        self.elem_detail.setReadOnly(True)
        dl.addWidget(self.elem_title)
        dl.addWidget(self.elem_detail)
        lay.addWidget(detail, 0)
        return container

    def _make_element_button(self, el) -> QPushButton:
        btn = QPushButton(f"{el.symbol}\n{el.number}")
        btn.setFixedSize(56, 56)
        btn.setToolTip(f"{el.name} ({el.symbol}) — {el.atomic_mass} u")
        color = CATEGORY_COLORS.get(el.category, "#334155")
        btn.setStyleSheet(
            f"QPushButton{{background:{color}; color:#0b1220; border:none;"
            f"border-radius:6px; font-size:11px; font-weight:600;}}"
            f"QPushButton:hover{{border:2px solid #e6edf7;}}"
        )
        btn.clicked.connect(lambda _=False, n=el.number: self._show_element(n))
        return btn

    def _show_element(self, number: int) -> None:
        el = get_element_by_number(number)
        if not el:
            return
        self.elem_title.setText(f"{el.name}  ·  {el.symbol}")
        self.elem_detail.setPlainText(
            f"Atomic number: {el.number}\n"
            f"Symbol:        {el.symbol}\n"
            f"Atomic mass:   {el.atomic_mass} u\n"
            f"Group:         {el.group if el.group else 'f-block'}\n"
            f"Period:        {el.period}\n"
            f"Category:      {el.category}\n"
            f"Configuration: {el.electron_config}\n\n"
            "Molar mass values are standard conventional atomic weights."
        )

    # -- Molar mass -------------------------------------------------------
    def _build_molar_mass(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        form_box = QGroupBox("Formula")
        fl = QFormLayout(form_box)
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("e.g. Ca(OH)2, H2SO4, C6H12O6")
        self.formula_input.returnPressed.connect(self._calc_molar_mass)
        fl.addRow("Chemical formula", self.formula_input)
        calc_btn = QPushButton("Calculate molar mass")
        calc_btn.setObjectName("Primary")
        calc_btn.clicked.connect(self._calc_molar_mass)
        fl.addRow(calc_btn)

        # SMILES (RDKit) sub-section
        smiles_box = QGroupBox("SMILES (RDKit molecular weight)")
        sl = QFormLayout(smiles_box)
        self.smiles_input = QLineEdit()
        self.smiles_input.setPlaceholderText("e.g. CCO (ethanol)")
        self.smiles_input.returnPressed.connect(self._calc_smiles)
        sl.addRow("SMILES", self.smiles_input)
        smiles_btn = QPushButton("Calculate from SMILES")
        smiles_btn.setObjectName("Primary")
        smiles_btn.clicked.connect(self._calc_smiles)
        sl.addRow(smiles_btn)

        left = QVBoxLayout()
        left.addWidget(form_box)
        left.addWidget(smiles_box)
        left.addStretch(1)
        lay.addLayout(left, 0)

        self.molar_table = QTableWidget(0, 4)
        self.molar_table.setHorizontalHeaderLabels(
            ["Element", "Count", "Atomic mass", "Subtotal (g/mol)"]
        )
        self.molar_table.verticalHeader().setVisible(False)
        self.molar_result = QLabel("")
        self.molar_result.setObjectName("H2")
        right = QVBoxLayout()
        right.addWidget(self.molar_table, 1)
        right.addWidget(self.molar_result)
        lay.addLayout(right, 1)
        return container

    def _calc_molar_mass(self) -> None:
        formula = self.formula_input.text().strip()
        if not formula:
            return
        try:
            res = calc.molar_mass(formula)
        except ValueError as exc:
            self.molar_result.setText(f"Error: {exc}")
            self.molar_result.setStyleSheet("color:#ef4444;")
            self.molar_table.setRowCount(0)
            return
        self.molar_result.setStyleSheet("")
        self.molar_table.setRowCount(0)
        for sym, count, atomic, subtotal in res["composition"]:
            row = self.molar_table.rowCount()
            self.molar_table.insertRow(row)
            self.molar_table.setItem(row, 0, QTableWidgetItem(sym))
            self.molar_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.molar_table.setItem(row, 2, QTableWidgetItem(f"{atomic:.4f}"))
            self.molar_table.setItem(row, 3, QTableWidgetItem(f"{subtotal:.4f}"))
        self.molar_result.setText(
            f"Molar mass of {formula}: {res['molar_mass']:.4f} g/mol"
        )

    def _calc_smiles(self) -> None:
        smiles = self.smiles_input.text().strip()
        if not smiles:
            return
        res = calc.molecular_weight_smiles(smiles)
        if res is None:
            self.molar_result.setText("Invalid SMILES or RDKit unavailable.")
            self.molar_result.setStyleSheet("color:#ef4444;")
            return
        self.molar_result.setStyleSheet("")
        self.molar_table.setRowCount(0)
        self.molar_result.setText(
            f"{res['formula']}: MW = {res['molecular_weight']:.4f} g/mol  "
            f"(exact mass {res['exact_mass']:.4f}, {res['num_atoms']} atoms)"
        )

    # -- Equation balancing ----------------------------------------------
    def _build_balancer(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        form = QFormLayout()
        self.eq_input = QLineEdit()
        self.eq_input.setPlaceholderText("e.g. Fe + O2 -> Fe2O3")
        self.eq_input.returnPressed.connect(self._balance)
        form.addRow("Unbalanced equation", self.eq_input)
        bal_btn = QPushButton("Balance")
        bal_btn.setObjectName("Primary")
        bal_btn.clicked.connect(self._balance)
        form.addRow(bal_btn)
        lay.addLayout(form)

        self.balance_output = QTextEdit()
        self.balance_output.setReadOnly(True)
        self.balance_output.setStyleSheet(
            "font-family: Consolas, monospace; font-size:15px;"
        )
        lay.addWidget(self.balance_output, 1)

        note = QLabel(
            "Uses an algebraic (null-space) method over element conservation. "
            "If a reaction cannot be balanced, the tool reports it rather than guessing."
        )
        note.setObjectName("MutedLabel")
        note.setWordWrap(True)
        lay.addWidget(note)
        return container

    def _balance(self) -> None:
        eq = self.eq_input.text().strip()
        if not eq:
            return
        try:
            res = calc.balance_equation(eq)
        except ValueError as exc:
            self.balance_output.setPlainText(f"Error: {exc}")
            return
        if res["status"] == "balanced":
            self.balance_output.setPlainText(
                f"Balanced: {res['balanced']}\n\nCoefficients: {res['coefficients']}"
            )
        else:
            self.balance_output.setPlainText(f"{res['status']}: {res['message']}")

    # -- Stoichiometry ----------------------------------------------------
    def _build_stoich(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        form = QGroupBox("Inputs")
        fl = QFormLayout(form)
        from PySide6.QtWidgets import QDoubleSpinBox
        self.s_grams = QDoubleSpinBox(); self.s_grams.setRange(0, 1e9); self.s_grams.setValue(4.0)
        self.s_mm_react = QDoubleSpinBox(); self.s_mm_react.setRange(0.0001, 1e6); self.s_mm_react.setValue(2.016)
        self.s_ratio = QDoubleSpinBox(); self.s_ratio.setRange(0.0001, 1e6); self.s_ratio.setValue(1.0)
        self.s_mm_prod = QDoubleSpinBox(); self.s_mm_prod.setRange(0.0001, 1e6); self.s_mm_prod.setValue(18.015)
        fl.addRow("Reactant mass (g)", self.s_grams)
        fl.addRow("Reactant molar mass (g/mol)", self.s_mm_react)
        fl.addRow("Mole ratio (reactant→product)", self.s_ratio)
        fl.addRow("Product molar mass (g/mol)", self.s_mm_prod)
        calc_btn = QPushButton("Calculate")
        calc_btn.setObjectName("Primary")
        calc_btn.clicked.connect(self._stoich)
        fl.addRow(calc_btn)
        lay.addWidget(form, 0)

        self.stoich_output = QTextEdit()
        self.stoich_output.setReadOnly(True)
        self.stoich_output.setStyleSheet("font-family: Consolas, monospace;")
        lay.addWidget(self.stoich_output, 1)
        return container

    def _stoich(self) -> None:
        res = calc.stoichiometry(
            self.s_grams.value(),
            self.s_mm_react.value(),
            self.s_ratio.value(),
            self.s_mm_prod.value(),
        )
        self.stoich_output.setPlainText(
            f"Moles of reactant: {res['moles_reactant']:.6f} mol\n"
            f"Moles of product:  {res['moles_product']:.6f} mol\n"
            f"Product mass:      {res['grams_product']:.6f} g"
        )