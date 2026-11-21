"""Physics Laboratory page.

A tabbed interface covering Classical Mechanics, Thermodynamics, Electricity &
Magnetism, and Optics. Each tab has adjustable parameters, a Run/Reset control,
a governing-equations display, a live chart, and a results panel. All numbers
come from the tested physics engine in ``axiomata.modules.physics``.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core.application import AppContext
from ...ui.panels.base_page import BasePage
from ...ui.widgets.chart_widget import ChartWidget
from . import electromagnetism as em
from . import mechanics as mech
from . import optics
from . import thermodynamics as thermo
from ...ui.themes.theme import ACCENT, ACCENT_BLUE, SUCCESS, WARNING


class _Param(QGroupBox):
    """A group of parameter spin boxes laid out in a form."""

    def __init__(self, title: str):
        super().__init__(title)
        self.form = QFormLayout(self)
        self.form.setSpacing(8)
        self._fields: dict[str, QDoubleSpinBox] = {}

    def add(self, name: str, value: float, minimum: float, maximum: float,
            suffix: str = "", decimals: int = 3, step: float = 0.1) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(minimum, maximum)
        sb.setValue(value)
        sb.setSuffix(suffix)
        sb.setDecimals(decimals)
        sb.setSingleStep(step)
        self.form.addRow(name, sb)
        self._fields[name] = sb
        return sb

    def get(self, name: str) -> float:
        return self._fields[name].value()


class PhysicsLabPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Physics Laboratory",
                         "Classical mechanics, thermodynamics, electromagnetism & optics — "
                         "all in SI units.", parent)
        self.ctx = ctx
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_projectile(), "Projectile Motion")
        self.tabs.addTab(self._build_pendulum(), "Pendulum")
        self.tabs.addTab(self._build_collision(), "Collisions")
        self.tabs.addTab(self._build_ohm(), "Circuits (Ohm / Power)")
        self.tabs.addTab(self._build_gas(), "Gas Laws")
        self.tabs.addTab(self._build_refraction(), "Refraction / Lens")
        self.add_body_widget(self.tabs, 1)

    # -- generic two-column builder ---------------------------------------
    def _layout(self, params: _Param, chart: ChartWidget, results: QTextEdit,
                equation: str) -> QWidget:
        container = QWidget()
        cols = QHBoxLayout(container)
        cols.setContentsMargins(0, 0, 0, 0)
        cols.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(8)
        eq_box = QGroupBox("Governing equations")
        eq_l = QVBoxLayout(eq_box)
        eq_lbl = QLabel(equation)
        eq_lbl.setWordWrap(True)
        eq_lbl.setStyleSheet("font-family: Consolas, monospace; color:#8aa0bd;")
        eq_l.addWidget(eq_lbl)
        left.addWidget(eq_box)
        left.addWidget(params, 1)
        cols.addLayout(left, 0)

        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(chart, 1)
        right.addWidget(QLabel("Results"))
        right.addWidget(results, 0)
        cols.addLayout(right, 1)
        return container

    # -- Projectile -------------------------------------------------------
    def _build_projectile(self) -> QWidget:
        params = _Param("Initial conditions")
        params.add("Speed v0 (m/s)", 20.0, 0.0, 1000.0)
        params.add("Angle (deg)", 45.0, 0.0, 90.0)
        params.add("Initial height (m)", 0.0, 0.0, 1000.0)
        chart = ChartWidget()
        results = QTextEdit()
        results.setReadOnly(True)
        results.setMaximumHeight(130)
        eq = ("vx = v0 cos(theta),  vy = v0 sin(theta)\n"
              "x(t) = vx t\n"
              "y(t) = h0 + vy t - 1/2 g t^2\n"
              "g = 9.80665 m/s^2")
        container = self._layout(params, chart, results, eq)
        run = QPushButton("Simulate")
        run.setObjectName("Primary")
        run.clicked.connect(lambda: self._run_projectile(params, chart, results))
        # Place run button above params.
        holder = QVBoxLayout()
        holder.addWidget(run)
        holder.addWidget(container, 1)
        outer = QWidget()
        outer.setLayout(holder)
        self._run_projectile(params, chart, results)
        return outer

    def _run_projectile(self, params: _Param, chart: ChartWidget, results: QTextEdit):
        v0 = params.get("Speed v0 (m/s)")
        ang = params.get("Angle (deg)")
        h0 = params.get("Initial height (m)")
        x, y = mech.projectile_trajectory(v0, ang, h0)
        chart.plot_xy(x, y, "x (m)", "y (m)", "Projectile trajectory", ACCENT)
        r = mech.projectile_motion(v0, ang, h0)
        results.setPlainText(
            f"Range:        {r['range']:.3f} m\n"
            f"Max height:   {r['max_height']:.3f} m\n"
            f"Flight time:  {r['flight_time']:.3f} s"
        )

    # -- Pendulum ---------------------------------------------------------
    def _build_pendulum(self) -> QWidget:
        params = _Param("Pendulum")
        params.add("Length (m)", 1.0, 0.01, 100.0)
        params.add("Amplitude (deg)", 15.0, 0.0, 89.0)
        chart = ChartWidget()
        results = QTextEdit()
        results.setReadOnly(True)
        results.setMaximumHeight(130)
        eq = ("Nonlinear ODE: theta'' + (g/L) sin(theta) = 0\n"
              "Small-angle: T = 2 pi sqrt(L/g)\n"
              "Integrated with scipy (RK45)")
        container = self._layout(params, chart, results, eq)
        run = QPushButton("Simulate")
        run.setObjectName("Primary")
        run.clicked.connect(lambda: self._run_pendulum(params, chart, results))
        holder = QVBoxLayout()
        holder.addWidget(run)
        holder.addWidget(container, 1)
        outer = QWidget()
        outer.setLayout(holder)
        self._run_pendulum(params, chart, results)
        return outer

    def _run_pendulum(self, params: _Param, chart: ChartWidget, results: QTextEdit):
        length = params.get("Length (m)")
        amp = params.get("Amplitude (deg)")
        t, theta = mech.pendulum_trajectory(length, amp, duration=20.0)
        chart.plot_xy(t, np.degrees(theta), "time (s)", "angle (deg)",
                      "Pendulum angle", ACCENT)
        T = mech.pendulum_period(length, amplitude_deg=amp)
        T_small = mech.pendulum_period(length, amplitude_deg=0.0)
        results.setPlainText(
            f"Period (corrected): {T:.4f} s\n"
            f"Small-angle period: {T_small:.4f} s\n"
            f"Difference:         {(T - T_small) * 1000:.2f} ms"
        )

    # -- Collisions -------------------------------------------------------
    def _build_collision(self) -> QWidget:
        params = _Param("Collision (1D)")
        params.add("Mass m1 (kg)", 2.0, 0.001, 1e6)
        params.add("Velocity v1 (m/s)", 3.0, -1e6, 1e6)
        params.add("Mass m2 (kg)", 3.0, 0.001, 1e6)
        params.add("Velocity v2 (m/s)", -1.0, -1e6, 1e6)
        params.add("Restitution e", 1.0, 0.0, 1.0)
        chart = ChartWidget()
        results = QTextEdit()
        results.setReadOnly(True)
        results.setMaximumHeight(140)
        eq = ("Momentum: m1 v1 + m2 v2 = m1 v1' + m2 v2'\n"
              "Restitution: e = (v2' - v1') / (v1 - v2)\n"
              "e=1 elastic, e=0 perfectly inelastic")
        container = self._layout(params, chart, results, eq)
        run = QPushButton("Collide")
        run.setObjectName("Primary")
        run.clicked.connect(lambda: self._run_collision(params, chart, results))
        holder = QVBoxLayout()
        holder.addWidget(run)
        holder.addWidget(container, 1)
        outer = QWidget()
        outer.setLayout(holder)
        self._run_collision(params, chart, results)
        return outer

    def _run_collision(self, params: _Param, chart: ChartWidget, results: QTextEdit):
        m1 = params.get("Mass m1 (kg)")
        v1 = params.get("Velocity v1 (m/s)")
        m2 = params.get("Mass m2 (kg)")
        v2 = params.get("Velocity v2 (m/s)")
        e = params.get("Restitution e")
        v1f, v2f = mech.momentum_collision_1d(m1, v1, m2, v2, e)
        ke_before = 0.5 * m1 * v1**2 + 0.5 * m2 * v2**2
        ke_after = 0.5 * m1 * v1f**2 + 0.5 * m2 * v2f**2
        labels = ["m1", "m2"]
        before = [v1, v2]
        after = [v1f, v2f]
        chart.figure.clear()
        ax = chart.figure.add_subplot(111)
        xpos = np.arange(len(labels))
        ax.bar(xpos - 0.2, before, width=0.4, label="before", color=ACCENT_BLUE)
        ax.bar(xpos + 0.2, after, width=0.4, label="after", color=ACCENT)
        ax.set_xticks(xpos)
        ax.set_xticklabels(labels)
        ax.axhline(0, color="#223047", linewidth=0.8)
        ax.set_ylabel("velocity (m/s)")
        ax.legend(fontsize=8)
        for t in ax.get_legend().get_texts():
            t.set_color("#e6edf7")
        chart._style_axes()
        chart.figure.tight_layout()
        chart.canvas.draw_idle()
        results.setPlainText(
            f"v1' = {v1f:.3f} m/s    v2' = {v2f:.3f} m/s\n"
            f"Momentum before: {m1*v1 + m2*v2:.3f} kg·m/s\n"
            f"KE before: {ke_before:.3f} J\n"
            f"KE after:  {ke_after:.3f} J\n"
            f"KE lost:   {ke_before - ke_after:.3f} J"
        )

    # -- Circuits ---------------------------------------------------------
    def _build_ohm(self) -> QWidget:
        params = _Param("DC Circuit")
        params.add("Voltage (V)", 12.0, 0.0, 1e6)
        params.add("Resistance (ohm)", 100.0, 0.001, 1e9)
        chart = ChartWidget()
        results = QTextEdit()
        results.setReadOnly(True)
        results.setMaximumHeight(130)
        eq = ("Ohm's law: V = I R\n"
              "Power: P = V I = I^2 R\n"
              "Series: R = sum(Ri)\n"
              "Parallel: 1/R = sum(1/Ri)")
        container = self._layout(params, chart, results, eq)
        run = QPushButton("Calculate")
        run.setObjectName("Primary")
        run.clicked.connect(lambda: self._run_ohm(params, chart, results))
        holder = QVBoxLayout()
        holder.addWidget(run)
        holder.addWidget(container, 1)
        outer = QWidget()
        outer.setLayout(holder)
        self._run_ohm(params, chart, results)
        return outer

    def _run_ohm(self, params: _Param, chart: ChartWidget, results: QTextEdit):
        v = params.get("Voltage (V)")
        r = params.get("Resistance (ohm)")
        i = v / r if r else 0.0
        p = v * i
        # I-V line across a range of voltages.
        volts = np.linspace(0, max(v, 1.0) * 1.5, 100)
        amps = volts / r
        chart.plot_xy(volts, amps, "voltage (V)", "current (A)", "I–V characteristic", ACCENT)
        results.setPlainText(
            f"Current: {i:.6f} A\n"
            f"Power:   {p:.6f} W\n"
            f"Resistance: {r:.3f} ohm"
        )

    # -- Gas laws ---------------------------------------------------------
    def _build_gas(self) -> QWidget:
        params = _Param("Ideal Gas (solve P)")
        params.add("Amount n (mol)", 1.0, 0.0001, 1e6)
        params.add("Temperature (K)", 273.15, 1.0, 1e6)
        params.add("Volume (L)", 22.414, 0.0001, 1e9)
        chart = ChartWidget()
        results = QTextEdit()
        results.setReadOnly(True)
        results.setMaximumHeight(130)
        eq = ("Ideal gas law: P V = n R T\n"
              "R = 8.314462618 J/(mol K)\n"
              "Volume converted L -> m^3")
        container = self._layout(params, chart, results, eq)
        run = QPushButton("Calculate")
        run.setObjectName("Primary")
        run.clicked.connect(lambda: self._run_gas(params, chart, results))
        holder = QVBoxLayout()
        holder.addWidget(run)
        holder.addWidget(container, 1)
        outer = QWidget()
        outer.setLayout(holder)
        self._run_gas(params, chart, results)
        return outer

    def _run_gas(self, params: _Param, chart: ChartWidget, results: QTextEdit):
        n = params.get("Amount n (mol)")
        t = params.get("Temperature (K)")
        v_liters = params.get("Volume (L)")
        v_m3 = v_liters / 1000.0
        res = thermo.ideal_gas_law(v=v_m3, n=n, t=t)
        # P-V isotherm at this temperature.
        vols = np.linspace(v_m3 * 0.5, v_m3 * 2.0, 100)
        pressures = n * thermo.R * t / vols
        chart.plot_xy(vols, pressures, "volume (m^3)", "pressure (Pa)", "Isotherm P–V", ACCENT)
        results.setPlainText(
            f"Pressure: {res['p']:.3f} Pa\n"
            f"Volume:   {res['v']*1000:.4f} L\n"
            f"Temp:     {res['t']:.3f} K\n"
            f"Amount:   {res['n']:.6f} mol"
        )

    # -- Refraction / Lens ------------------------------------------------
    def _build_refraction(self) -> QWidget:
        params = _Param("Optics")
        params.add("n1 (incident medium)", 1.0, 1.0, 4.0)
        params.add("n2 (transmit medium)", 1.5, 1.0, 4.0)
        params.add("Incident angle (deg)", 30.0, 0.0, 89.9)
        params.add("Lens focal length (m)", 0.1, 0.001, 100.0)
        params.add("Object distance (m)", 0.3, 0.001, 1000.0)
        chart = ChartWidget()
        results = QTextEdit()
        results.setReadOnly(True)
        results.setMaximumHeight(160)
        eq = ("Snell: n1 sin(t1) = n2 sin(t2)\n"
              "Thin lens: 1/f = 1/do + 1/di\n"
              "Magnification: m = -di/do")
        container = self._layout(params, chart, results, eq)
        run = QPushButton("Calculate")
        run.setObjectName("Primary")
        run.clicked.connect(lambda: self._run_optics(params, chart, results))
        holder = QVBoxLayout()
        holder.addWidget(run)
        holder.addWidget(container, 1)
        outer = QWidget()
        outer.setLayout(holder)
        self._run_optics(params, chart, results)
        return outer

    def _run_optics(self, params: _Param, chart: ChartWidget, results: QTextEdit):
        n1 = params.get("n1 (incident medium)")
        n2 = params.get("n2 (transmit medium)")
        inc = params.get("Incident angle (deg)")
        f = params.get("Lens focal length (m)")
        do = params.get("Object distance (m)")
        refr = optics.snell_refraction(n1, n2, inc)
        crit = optics.critical_angle(n1, n2)
        lens = optics.thin_lens(f, do)
        # Plot deviation vs incidence angle.
        angles = np.linspace(0, 89, 100)
        out = [optics.snell_refraction(n1, n2, a)["refracted_deg"] for a in angles]
        out = [0.0 if np.isnan(o) else o for o in out]
        chart.plot_xy(angles, out, "incident (deg)", "refracted (deg)",
                      "Snell refraction", ACCENT)
        if refr["total_internal_reflection"]:
            refr_line = "Refracted: total internal reflection"
        else:
            refr_line = f"Refracted: {refr['refracted_deg']:.3f} deg"
        if np.isnan(crit):
            crit_line = "Critical angle: n/a (no TIR)"
        else:
            crit_line = f"Critical angle: {crit:.3f} deg"
        results.setPlainText(
            f"{refr_line}\n"
            f"{crit_line}\n"
            f"Lens image distance: {lens['image_distance']:.4f} m ({lens['image_type']})\n"
            f"Magnification: {lens['magnification']:.3f}"
        )