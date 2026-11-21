"""Mathematics Laboratory page.

A scientific calculator workspace: enter an expression in x, then simplify,
differentiate, integrate, solve, or plot. Includes matrix operations and a
function plotter. Powered by SymPy (symbolic) and NumPy/SciPy (numeric).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core.application import AppContext
from ...ui.panels.base_page import BasePage
from ...ui.widgets.chart_widget import ChartWidget
from ...ui.themes.theme import ACCENT
from . import math_engine as m


class MathematicsLabPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Mathematics Laboratory",
                         "Symbolic algebra, calculus, matrices, complex numbers & plotting.",
                         parent)
        self.ctx = ctx
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_calculator(), "Calculator")
        self.tabs.addTab(self._build_plotter(), "Plot Function")
        self.tabs.addTab(self._build_matrix(), "Matrices & Vectors")
        self.tabs.addTab(self._build_numeric(), "Numerical Methods")
        self.add_body_widget(self.tabs, 1)

    # -- Calculator -------------------------------------------------------
    def _build_calculator(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        box = QGroupBox("Expression (variable x)")
        bl = QVBoxLayout(box)
        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText("e.g. x**2 + 2*x + 1, sin(x), exp(x)")
        self.expr_input.returnPressed.connect(lambda: self._calc("simplify"))
        bl.addWidget(self.expr_input)

        buttons = QGroupBox("Operations")
        grid = QFormLayout(buttons)
        ops = [
            ("Simplify", "simplify"), ("Differentiate", "differentiate"),
            ("Integrate", "integrate"), ("Solve (= 0)", "solve"),
            ("Evaluate at x =", "evaluate"),
        ]
        for label, op in ops:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=False, o=op: self._calc(o))
            grid.addRow(btn)
        # Order of differentiation input.
        self.diff_order = QSpinBox()
        self.diff_order.setRange(1, 10)
        self.diff_order.setValue(1)
        grid.addRow("Derivative order", self.diff_order)
        bl.addWidget(buttons)

        # Evaluation inputs
        eval_box = QGroupBox("Evaluate")
        ef = QFormLayout(eval_box)
        self.eval_x = QDoubleSpinBox()
        self.eval_x.setRange(-1e6, 1e6)
        self.eval_x.setDecimals(4)
        self.eval_x.setValue(1.0)
        ef.addRow("x =", self.eval_x)
        eval_btn = QPushButton("Evaluate expression")
        eval_btn.clicked.connect(lambda: self._calc("evaluate"))
        ef.addRow(eval_btn)
        bl.addWidget(eval_box)
        bl.addStretch(1)
        lay.addWidget(box, 0)

        self.calc_output = QTextEdit()
        self.calc_output.setReadOnly(True)
        self.calc_output.setStyleSheet("font-family: Consolas, monospace;")
        lay.addWidget(self.calc_output, 1)
        return container

    def _calc(self, op: str) -> None:
        expr = self.expr_input.text().strip()
        if not expr:
            return
        try:
            if op == "simplify":
                result = m.simplify(expr)
            elif op == "differentiate":
                result = m.differentiate(expr, self.diff_order.value())
            elif op == "integrate":
                result = m.integrate(expr)
            elif op == "solve":
                sols = m.solve_equation(expr)
                result = "x = " + ", ".join(sols) if sols else "No solution"
            elif op == "evaluate":
                val = m.evaluate_numeric(expr, self.eval_x.value())
                result = f"f({self.eval_x.value()}) = {val:.6g}"
            else:
                result = "Unknown operation"
        except (ValueError, ZeroDivisionError) as exc:
            result = f"Error: {exc}"
        self.calc_output.append(f"[{op}] {result}")

    # -- Plotter ----------------------------------------------------------
    def _build_plotter(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        box = QGroupBox("Function")
        fl = QFormLayout(box)
        self.plot_expr = QLineEdit()
        self.plot_expr.setPlaceholderText("e.g. sin(x), x**2 - 4")
        self.plot_expr.returnPressed.connect(self._plot)
        fl.addRow("f(x) =", self.plot_expr)
        self.plot_xmin = QDoubleSpinBox(); self.plot_xmin.setRange(-1e6, 1e6); self.plot_xmin.setValue(-10)
        self.plot_xmax = QDoubleSpinBox(); self.plot_xmax.setRange(-1e6, 1e6); self.plot_xmax.setValue(10)
        fl.addRow("x min", self.plot_xmin)
        fl.addRow("x max", self.plot_xmax)
        plot_btn = QPushButton("Plot")
        plot_btn.setObjectName("Primary")
        plot_btn.clicked.connect(self._plot)
        fl.addRow(plot_btn)
        lay.addWidget(box, 0)

        self.plot_chart = ChartWidget()
        lay.addWidget(self.plot_chart, 1)
        return container

    def _plot(self) -> None:
        expr = self.plot_expr.text().strip()
        if not expr:
            return
        try:
            x, y = m.plot_function_samples(expr, self.plot_xmin.value(), self.plot_xmax.value())
            self.plot_chart.plot_xy(x, y, "x", "f(x)", f"f(x) = {expr}", ACCENT)
        except (ValueError, ZeroDivisionError) as exc:
            self.plot_chart.clear()
            self.plot_chart.figure.text(0.5, 0.5, f"Error: {exc}", ha="center",
                                        color="#ef4444", transform=self.plot_chart.figure.transFigure)
            self.plot_chart.canvas.draw_idle()

    # -- Matrices & vectors ----------------------------------------------
    def _build_matrix(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        form = QFormLayout()
        self.mat_a = QLineEdit()
        self.mat_a.setPlaceholderText("Matrix A rows, e.g. 1,2;3,4")
        self.mat_b = QLineEdit()
        self.mat_b.setPlaceholderText("Matrix B (optional)")
        form.addRow("Matrix A", self.mat_a)
        form.addRow("Matrix B", self.mat_b)
        lay.addLayout(form)

        btn_row = QHBoxLayout()
        for label, op in [("A + B", "add"), ("A - B", "subtract"),
                          ("A × B", "multiply"), ("transpose A", "transpose"),
                          ("det(A)", "determinant"), ("inverse(A)", "inverse")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=False, o=op: self._matrix(op))
            btn_row.addWidget(btn)
        lay.addLayout(btn_row)

        self.mat_output = QTextEdit()
        self.mat_output.setReadOnly(True)
        self.mat_output.setStyleSheet("font-family: Consolas, monospace;")
        lay.addWidget(self.mat_output, 1)

        # Vectors
        vec_box = QGroupBox("Vectors")
        vf = QFormLayout(vec_box)
        self.vec_a = QLineEdit(); self.vec_a.setPlaceholderText("e.g. 1,2,3")
        self.vec_b = QLineEdit(); self.vec_b.setPlaceholderText("e.g. 4,5,6")
        vf.addRow("Vector a", self.vec_a)
        vf.addRow("Vector b", self.vec_b)
        vbtn_row = QHBoxLayout()
        for label, op in [("dot", "dot"), ("cross", "cross"), ("|a|", "norm")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=False, o=op: self._vector(o))
            vbtn_row.addWidget(btn)
        vf.addRow(vbtn_row)
        lay.addWidget(vec_box, 0)
        return container

    def _parse_matrix(self, text: str) -> list[list[float]]:
        text = text.strip()
        if not text:
            return []
        rows = []
        for row in text.split(";"):
            rows.append([float(x) for x in row.split(",")])
        return rows

    def _matrix(self, op: str) -> None:
        try:
            A = self._parse_matrix(self.mat_a.text())
            if not A:
                return
            if op == "transpose":
                res = m.matrix_operations(A, op="transpose")
            elif op == "determinant":
                res = [f"det(A) = {m.matrix_determinant(A)}"]
                self.mat_output.append(res[0]); return
            elif op == "inverse":
                res = m.matrix_inverse(A)
                res = "\n".join(str(r) for r in res)
                self.mat_output.append(f"inverse(A):\n{res}"); return
            else:
                B = self._parse_matrix(self.mat_b.text())
                if not B:
                    self.mat_output.append("Need matrix B for this operation.")
                    return
                res = m.matrix_operations(A, B, op)
            self.mat_output.append(f"{op}(A[,B]) =\n" + "\n".join(str(r) for r in res))
        except (ValueError, ZeroDivisionError) as exc:
            self.mat_output.append(f"Error: {exc}")

    def _vector(self, op: str) -> None:
        try:
            a = [float(x) for x in self.vec_a.text().split(",")] if self.vec_a.text().strip() else []
            b = [float(x) for x in self.vec_b.text().split(",")] if self.vec_b.text().strip() else []
            if op == "norm":
                res = m.vector_norm(a)
            elif op == "dot":
                res = m.vector_dot(a, b)
            elif op == "cross":
                res = m.vector_cross(a, b)
            else:
                return
            self.mat_output.append(f"{op} = {res}")
        except ValueError as exc:
            self.mat_output.append(f"Error: {exc}")

    # -- Numerical methods -----------------------------------------------
    def _build_numeric(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        box = QGroupBox("Find a root (bisection) and integrate")
        fl = QFormLayout(box)
        self.num_expr = QLineEdit()
        self.num_expr.setPlaceholderText("e.g. x**2 - 2, cos(x) - x")
        fl.addRow("f(x) =", self.num_expr)
        self.num_a = QDoubleSpinBox(); self.num_a.setRange(-1e6, 1e6); self.num_a.setValue(0)
        self.num_b = QDoubleSpinBox(); self.num_b.setRange(-1e6, 1e6); self.num_b.setValue(2)
        fl.addRow("Bracket a", self.num_a)
        fl.addRow("Bracket b", self.num_b)
        root_btn = QPushButton("Find root (bisection)")
        root_btn.clicked.connect(self._root)
        fl.addRow(root_btn)
        self.int_a = QDoubleSpinBox(); self.int_a.setRange(-1e6, 1e6); self.int_a.setValue(0)
        self.int_b = QDoubleSpinBox(); self.int_b.setRange(-1e6, 1e6); self.int_b.setValue(1)
        fl.addRow("Integral from", self.int_a)
        fl.addRow("Integral to", self.int_b)
        int_btn = QPushButton("Integrate (Simpson)")
        int_btn.clicked.connect(self._integral)
        fl.addRow(int_btn)
        lay.addWidget(box, 0)

        self.num_output = QTextEdit()
        self.num_output.setReadOnly(True)
        self.num_output.setStyleSheet("font-family: Consolas, monospace;")
        lay.addWidget(self.num_output, 1)
        return container

    def _root(self) -> None:
        expr = self.num_expr.text().strip()
        if not expr:
            return
        try:
            res = m.bisection_root(expr, self.num_a.value(), self.num_b.value())
            self.num_output.append(
                f"Root: x ≈ {res['root']:.10f}  "
                f"(converged in {res['iterations']} iterations: {res['converged']})"
            )
        except ValueError as exc:
            self.num_output.append(f"Error: {exc}")

    def _integral(self) -> None:
        expr = self.num_expr.text().strip()
        if not expr:
            return
        try:
            res = m.numerical_integral(expr, self.int_a.value(), self.int_b.value())
            self.num_output.append(
                f"∫[{self.int_a.value()}, {self.int_b.value()}] {expr} dx ≈ {res:.8f}"
            )
        except ValueError as exc:
            self.num_output.append(f"Error: {exc}")