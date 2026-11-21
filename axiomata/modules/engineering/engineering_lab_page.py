"""Engineering Laboratory page: mechanical, electrical, civil (structural)."""
from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QDoubleSpinBox, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from ...core.application import AppContext
from ...ui.panels.base_page import BasePage
from ...ui.widgets.chart_widget import ChartWidget
from ...ui.themes.theme import ACCENT, WARNING
from . import engineering_engine as eng


class EngineeringLabPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Engineering Laboratory",
                         "Mechanical, electrical & civil engineering calculations.",
                         parent)
        self.ctx = ctx
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_mechanical(), "Mechanical")
        self.tabs.addTab(self._build_electrical(), "Electrical")
        self.tabs.addTab(self._build_civil(), "Civil / Structural")
        self.add_body_widget(self.tabs, 1)

    def _warn(self) -> QLabel:
        lbl = QLabel(
            "⚠ Simplified engineering models for education and exploration only — "
            "not certified for real-world safety-critical design."
        )
        lbl.setStyleSheet(f"color:{WARNING}; font-size:12px;")
        lbl.setWordWrap(True)
        return lbl

    # -- Mechanical -------------------------------------------------------
    def _build_mechanical(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("Rotational dynamics / spring")
        fl = QFormLayout(box)
        self.m_torque = QDoubleSpinBox(); self.m_torque.setRange(-1e6, 1e6); self.m_torque.setValue(10)
        self.m_inertia = QDoubleSpinBox(); self.m_inertia.setRange(0.001, 1e6); self.m_inertia.setValue(2)
        self.m_time = QDoubleSpinBox(); self.m_time.setRange(0, 1e6); self.m_time.setValue(3)
        self.m_mass = QDoubleSpinBox(); self.m_mass.setRange(0.001, 1e6); self.m_mass.setValue(1)
        self.m_k = QDoubleSpinBox(); self.m_k.setRange(0.001, 1e6); self.m_k.setValue(4)
        fl.addRow("Torque (N·m)", self.m_torque)
        fl.addRow("Moment of inertia (kg·m²)", self.m_inertia)
        fl.addRow("Time (s)", self.m_time)
        fl.addRow("Spring mass (kg)", self.m_mass)
        fl.addRow("Spring constant k (N/m)", self.m_k)
        rot_btn = QPushButton("Rotational motion")
        rot_btn.clicked.connect(self._rotation)
        spring_btn = QPushButton("Spring period")
        spring_btn.clicked.connect(self._spring)
        fl.addRow(rot_btn)
        fl.addRow(spring_btn)
        self.m_out = QTextEdit()
        self.m_out.setReadOnly(True)
        fl.addRow(self.m_out)
        lay.addWidget(box, 0)
        self.m_chart = ChartWidget()
        lay.addWidget(self.m_chart, 1)
        lay2 = QVBoxLayout()
        lay2.addWidget(self._warn())
        # place warning under chart
        warn_holder = QWidget()
        warn_holder.setLayout(lay2)
        lay.addWidget(warn_holder, 0)
        return container

    def _rotation(self) -> None:
        try:
            res = eng.rotational_dynamics(self.m_torque.value(), self.m_inertia.value(), self.m_time.value())
            t = np.linspace(0, self.m_time.value(), 100)
            theta = 0.5 * res["alpha"] * t**2
            self.m_chart.plot_xy(t, theta, "time (s)", "angle (rad)", "Rotational motion", ACCENT)
            self.m_out.setPlainText(
                f"Angular accel: {res['alpha']:.4f} rad/s²\n"
                f"Angular velocity: {res['omega']:.4f} rad/s\n"
                f"Angle: {res['theta']:.4f} rad"
            )
        except ValueError as exc:
            self.m_out.setPlainText(f"Error: {exc}")

    def _spring(self) -> None:
        try:
            res = eng.spring_period(self.m_mass.value(), self.m_k.value())
            t, x = eng.simple_harmonic_oscillator(self.m_mass.value(), self.m_k.value(), 1.0)
            self.m_chart.plot_xy(t, x, "time (s)", "x (m)", "Mass-spring SHM", ACCENT)
            self.m_out.setPlainText(
                f"Angular frequency: {res['omega']:.4f} rad/s\n"
                f"Period: {res['period']:.4f} s\n"
                f"Frequency: {res['frequency']:.4f} Hz"
            )
        except ValueError as exc:
            self.m_out.setPlainText(f"Error: {exc}")

    # -- Electrical -------------------------------------------------------
    def _build_electrical(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("DC circuits")
        fl = QFormLayout(box)
        self.e_v = QDoubleSpinBox(); self.e_v.setRange(0, 1e6); self.e_v.setValue(12)
        self.e_r1 = QDoubleSpinBox(); self.e_r1.setRange(0.001, 1e9); self.e_r1.setValue(1000)
        self.e_r2 = QDoubleSpinBox(); self.e_r2.setRange(0.001, 1e9); self.e_r2.setValue(2000)
        fl.addRow("Voltage (V)", self.e_v)
        fl.addRow("R1 (ohm)", self.e_r1)
        fl.addRow("R2 (ohm)", self.e_r2)
        series_btn = QPushButton("Series resistance + current")
        series_btn.clicked.connect(self._series)
        parallel_btn = QPushButton("Parallel resistance + current")
        parallel_btn.clicked.connect(self._parallel)
        divider_btn = QPushButton("Voltage divider (out across R2)")
        divider_btn.clicked.connect(self._divider)
        fl.addRow(series_btn)
        fl.addRow(parallel_btn)
        fl.addRow(divider_btn)
        self.e_out = QTextEdit()
        self.e_out.setReadOnly(True)
        fl.addRow(self.e_out)
        lay.addWidget(box, 0)
        chart_holder = QVBoxLayout()
        self.e_chart = ChartWidget()
        chart_holder.addWidget(self.e_chart, 1)
        holder = QWidget()
        holder.setLayout(chart_holder)
        lay.addWidget(holder, 1)
        lay2 = QVBoxLayout()
        lay2.addWidget(self._warn())
        wh = QWidget(); wh.setLayout(lay2)
        lay.addWidget(wh, 0)
        return container

    def _series(self) -> None:
        rs = eng.series_resistance(self.e_r1.value(), self.e_r2.value())
        i = self.e_v.value() / rs
        self.e_out.setPlainText(
            f"Series R = {rs:.2f} ohm\nCurrent = {i:.6f} A"
        )
        self._draw_resistor_chart("series")

    def _parallel(self) -> None:
        rp = eng.parallel_resistance(self.e_r1.value(), self.e_r2.value())
        i = self.e_v.value() / rp
        self.e_out.setPlainText(
            f"Parallel R = {rp:.2f} ohm\nCurrent = {i:.6f} A"
        )
        self._draw_resistor_chart("parallel")

    def _divider(self) -> None:
        res = eng.voltage_divider(self.e_v.value(), self.e_r1.value(), self.e_r2.value())
        self.e_out.setPlainText(
            f"V_out = {res['v_out']:.4f} V\n"
            f"Total R = {res['total_r']:.2f} ohm\n"
            f"Current = {res['current']:.6f} A"
        )
        self._draw_resistor_chart("divider")

    def _draw_resistor_chart(self, mode: str) -> None:
        # Plot V-I characteristic for the equivalent resistance.
        r = {
            "series": eng.series_resistance(self.e_r1.value(), self.e_r2.value()),
            "parallel": eng.parallel_resistance(self.e_r1.value(), self.e_r2.value()),
            "divider": self.e_r1.value() + self.e_r2.value(),
        }[mode]
        volts = np.linspace(0, self.e_v.value() * 1.5, 100)
        amps = volts / r
        self.e_chart.plot_xy(volts, amps, "V (volts)", "I (amps)", "V–I characteristic", ACCENT)

    # -- Civil ------------------------------------------------------------
    def _build_civil(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("Simply supported beam (point load)")
        fl = QFormLayout(box)
        self.c_L = QDoubleSpinBox(); self.c_L.setRange(0.1, 1e3); self.c_L.setValue(4.0)
        self.c_P = QDoubleSpinBox(); self.c_P.setRange(0, 1e8); self.c_P.setValue(1000.0)
        self.c_pos = QDoubleSpinBox(); self.c_pos.setRange(0, 1e3); self.c_pos.setValue(2.0)
        self.c_E = QDoubleSpinBox(); self.c_E.setRange(1, 1e13); self.c_E.setValue(200e9)
        self.c_I = QDoubleSpinBox(); self.c_I.setRange(1e-9, 1e3); self.c_I.setValue(1e-4)
        fl.addRow("Length L (m)", self.c_L)
        fl.addRow("Load P (N)", self.c_P)
        fl.addRow("Load position a (m)", self.c_pos)
        fl.addRow("Young's modulus E (Pa)", self.c_E)
        fl.addRow("Moment of inertia I (m⁴)", self.c_I)
        calc_btn = QPushButton("Analyse beam")
        calc_btn.setObjectName("Primary")
        calc_btn.clicked.connect(self._beam)
        fl.addRow(calc_btn)
        self.c_out = QTextEdit()
        self.c_out.setReadOnly(True)
        self.c_out.setMaximumHeight(140)
        fl.addRow(self.c_out)
        lay.addWidget(box, 0)
        self.c_chart = ChartWidget()
        lay.addWidget(self.c_chart, 1)
        lay2 = QVBoxLayout()
        lay2.addWidget(self._warn())
        wh = QWidget(); wh.setLayout(lay2)
        lay.addWidget(wh, 0)
        self._beam()
        return container

    def _beam(self) -> None:
        try:
            res = eng.simply_supported_beam_point_load(
                self.c_L.value(), self.c_P.value(), self.c_pos.value(),
                self.c_E.value(), self.c_I.value())
            x, y = eng.beam_deflection_curve(
                self.c_L.value(), self.c_P.value(), self.c_pos.value(),
                self.c_E.value(), self.c_I.value())
            self.c_chart.plot_xy(x, y * 1000, "position (m)", "deflection (mm)",
                                 "Beam deflection", ACCENT)
            self.c_out.setPlainText(
                f"Reactions: R_left={res['reaction_left']:.2f} N, "
                f"R_right={res['reaction_right']:.2f} N\n"
                f"Max bending moment: {res['max_bending_moment']:.3f} N·m\n"
                f"Max deflection: {abs(res['max_deflection'])*1000:.4f} mm"
            )
        except (ValueError, ZeroDivisionError) as exc:
            self.c_out.setPlainText(f"Error: {exc}")