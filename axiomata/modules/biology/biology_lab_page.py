"""Biology Laboratory page: genetics, population growth, predator-prey, selection."""
from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLineEdit, QPushButton,
    QDoubleSpinBox, QSpinBox, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from ...core.application import AppContext
from ...ui.panels.base_page import BasePage
from ...ui.widgets.chart_widget import ChartWidget
from ...ui.themes.theme import ACCENT, ACCENT_BLUE
from . import biology_engine as bio


class BiologyLabPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Biology Laboratory",
                         "Mendelian genetics, population models, ecosystems & selection.",
                         parent)
        self.ctx = ctx
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_genetics(), "Mendelian Genetics")
        self.tabs.addTab(self._build_population(), "Population Growth")
        self.tabs.addTab(self._build_predator_prey(), "Predator–Prey")
        self.tabs.addTab(self._build_selection(), "Natural Selection")
        self.add_body_widget(self.tabs, 1)

    def _build_genetics(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("Monohybrid cross (one gene)")
        fl = QFormLayout(box)
        self.p1 = QLineEdit("Aa")
        self.p2 = QLineEdit("Aa")
        fl.addRow("Parent 1", self.p1)
        fl.addRow("Parent 2", self.p2)
        btn = QPushButton("Cross")
        btn.setObjectName("Primary")
        btn.clicked.connect(self._genetics)
        fl.addRow(btn)
        lay.addWidget(box, 0)
        self.g_out = QTextEdit()
        self.g_out.setReadOnly(True)
        self.g_out.setStyleSheet("font-family: Consolas, monospace;")
        lay.addWidget(self.g_out, 1)
        self._genetics()
        return container

    def _genetics(self) -> None:
        try:
            res = bio.mendelian_cross(self.p1.text().strip(), self.p2.text().strip())
        except ValueError as exc:
            self.g_out.setPlainText(f"Error: {exc}")
            return
        lines = ["Punnett square:"]
        for row in res["grid"]:
            lines.append("  " + "  ".join(row))
        lines.append("")
        for g, c in res["genotypes"].items():
            lines.append(f"{g}: {c}/4")
        lines.append(f"Dominant phenotype: {res['dominant_phenotype']}/4")
        lines.append(f"Recessive phenotype: {res['recessive_phenotype']}/4")
        self.g_out.setPlainText("\n".join(lines))

    def _build_population(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("Population growth")
        fl = QFormLayout(box)
        self.pop_n0 = QDoubleSpinBox(); self.pop_n0.setRange(1, 1e9); self.pop_n0.setValue(10)
        self.pop_r = QDoubleSpinBox(); self.pop_r.setRange(-10, 10); self.pop_r.setValue(0.5)
        self.pop_k = QDoubleSpinBox(); self.pop_k.setRange(1, 1e9); self.pop_k.setValue(1000)
        fl.addRow("N0", self.pop_n0)
        fl.addRow("growth rate r", self.pop_r)
        fl.addRow("carrying capacity K", self.pop_k)
        btn_row = QHBoxLayout()
        exp_btn = QPushButton("Exponential")
        exp_btn.clicked.connect(self._pop_exp)
        log_btn = QPushButton("Logistic")
        log_btn.clicked.connect(self._pop_log)
        btn_row.addWidget(exp_btn); btn_row.addWidget(log_btn)
        fl.addRow(btn_row)
        lay.addWidget(box, 0)
        self.pop_chart = ChartWidget()
        lay.addWidget(self.pop_chart, 1)
        return container

    def _pop_exp(self) -> None:
        t = np.linspace(0, 50, 300)
        n = bio.exponential_growth(self.pop_n0.value(), self.pop_r.value(), t)
        self.pop_chart.plot_xy(t, n, "time", "N", "Exponential growth", ACCENT)

    def _pop_log(self) -> None:
        t = np.linspace(0, 50, 300)
        n = bio.logistic_growth(self.pop_n0.value(), self.pop_r.value(),
                                self.pop_k.value(), t)
        self.pop_chart.plot_xy(t, n, "time", "N", "Logistic growth", ACCENT_BLUE)

    def _build_predator_prey(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("Lotka–Volterra")
        fl = QFormLayout(box)
        self.pp_prey = QDoubleSpinBox(); self.pp_prey.setRange(0.1, 1e5); self.pp_prey.setValue(10)
        self.pp_pred = QDoubleSpinBox(); self.pp_pred.setRange(0.1, 1e5); self.pp_pred.setValue(5)
        self.pp_alpha = QDoubleSpinBox(); self.pp_alpha.setRange(0.001, 10); self.pp_alpha.setValue(0.1)
        self.pp_beta = QDoubleSpinBox(); self.pp_beta.setRange(0.0001, 10); self.pp_beta.setValue(0.02)
        self.pp_delta = QDoubleSpinBox(); self.pp_delta.setRange(0.0001, 10); self.pp_delta.setValue(0.01)
        self.pp_gamma = QDoubleSpinBox(); self.pp_gamma.setRange(0.001, 10); self.pp_gamma.setValue(0.1)
        fl.addRow("Prey N0", self.pp_prey)
        fl.addRow("Predator N0", self.pp_pred)
        fl.addRow("alpha (prey growth)", self.pp_alpha)
        fl.addRow("beta (predation rate)", self.pp_beta)
        fl.addRow("delta (conversion)", self.pp_delta)
        fl.addRow("gamma (predator death)", self.pp_gamma)
        btn = QPushButton("Simulate")
        btn.setObjectName("Primary")
        btn.clicked.connect(self._pp)
        fl.addRow(btn)
        lay.addWidget(box, 0)
        self.pp_chart = ChartWidget()
        lay.addWidget(self.pp_chart, 1)
        return container

    def _pp(self) -> None:
        t, prey, pred = bio.lotka_volterra_prey_predator(
            self.pp_prey.value(), self.pp_pred.value(), self.pp_alpha.value(),
            self.pp_beta.value(), self.pp_delta.value(), self.pp_gamma.value(),
            duration=50, steps=800)
        self.pp_chart.plot_series(
            [(t, prey, "Prey", ACCENT), (t, pred, "Predator", ACCENT_BLUE)],
            "time", "population", "Predator–Prey dynamics")

    def _build_selection(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("Viability selection (biallelic)")
        fl = QFormLayout(box)
        self.sel_p = QDoubleSpinBox(); self.sel_p.setRange(0, 1); self.sel_p.setDecimals(3); self.sel_p.setValue(0.5)
        self.sel_waa = QDoubleSpinBox(); self.sel_waa.setRange(0, 2); self.sel_waa.setDecimals(2); self.sel_waa.setValue(1.0)
        self.sel_wAa = QDoubleSpinBox(); self.sel_wAa.setRange(0, 2); self.sel_wAa.setDecimals(2); self.sel_wAa.setValue(0.8)
        self.sel_waa2 = QDoubleSpinBox(); self.sel_waa2.setRange(0, 2); self.sel_waa2.setDecimals(2); self.sel_waa2.setValue(0.5)
        self.sel_gens = QSpinBox(); self.sel_gens.setRange(1, 500); self.sel_gens.setValue(50)
        fl.addRow("Initial p", self.sel_p)
        fl.addRow("Fitness AA", self.sel_waa)
        fl.addRow("Fitness Aa", self.sel_wAa)
        fl.addRow("Fitness aa", self.sel_waa2)
        fl.addRow("Generations", self.sel_gens)
        btn = QPushButton("Evolve")
        btn.setObjectName("Primary")
        btn.clicked.connect(self._selection)
        fl.addRow(btn)
        lay.addWidget(box, 0)
        self.sel_chart = ChartWidget()
        lay.addWidget(self.sel_chart, 1)
        return container

    def _selection(self) -> None:
        gens, ps = bio.iterate_selection(
            self.sel_p.value(), self.sel_waa.value(), self.sel_wAa.value(),
            self.sel_waa2.value(), self.sel_gens.value())
        self.sel_chart.plot_xy(gens, ps, "generation", "allele freq p", "Allele frequency", ACCENT)