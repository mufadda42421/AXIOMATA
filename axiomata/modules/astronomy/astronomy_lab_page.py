"""Astronomy Laboratory page: solar system, orbits, moon phases, planet data."""
from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from ...core.application import AppContext
from ...ui.panels.base_page import BasePage
from ...ui.widgets.chart_widget import ChartWidget
from ...ui.themes.theme import ACCENT, ACCENT_BLUE
from . import astronomy_engine as astro


class AstronomyLabPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Astronomy Laboratory",
                         "Orbital mechanics, planetary data & lunar phases (Astropy where useful).",
                         parent)
        self.ctx = ctx
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_solar_system(), "Solar System")
        self.tabs.addTab(self._build_orbits(), "Orbital Mechanics")
        self.tabs.addTab(self._build_moon(), "Moon Phases")
        self.add_body_widget(self.tabs, 1)

    def _build_solar_system(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        table = QTableWidget(len(astro.PLANETS), 6)
        table.setHorizontalHeaderLabels(
            ["Planet", "a (AU)", "e", "Radius (km)", "Period (days)", "Computed period (days)"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        for r, p in enumerate(astro.PLANETS):
            table.setItem(r, 0, QTableWidgetItem(p["name"]))
            table.setItem(r, 1, QTableWidgetItem(f"{p['a_au']:.3f}"))
            table.setItem(r, 2, QTableWidgetItem(f"{p['e']:.4f}"))
            table.setItem(r, 3, QTableWidgetItem(f"{p['radius_km']:.0f}"))
            table.setItem(r, 4, QTableWidgetItem(f"{p['period_days']:.2f}"))
            table.setItem(r, 5, QTableWidgetItem(f"{astro.planet_period_check(p):.2f}"))
        lay.addWidget(table, 1)
        note = QLabel(
            "Orbital periods computed from Kepler's third law match tabulated values "
            "within a few percent, confirming the model. Data are approximate mean elements."
        )
        note.setObjectName("MutedLabel")
        note.setWordWrap(True)
        lay.addWidget(note)
        return container

    def _build_orbits(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("Two-body orbit")
        fl = QFormLayout(box)
        self.o_a = QDoubleSpinBox(); self.o_a.setRange(0.01, 1e3); self.o_a.setValue(1.0)
        self.o_e = QDoubleSpinBox(); self.o_e.setRange(0, 0.99); self.o_e.setDecimals(3); self.o_e.setValue(0.5)
        fl.addRow("Semi-major axis (AU)", self.o_a)
        fl.addRow("Eccentricity", self.o_e)
        calc_btn = QPushButton("Analyse")
        calc_btn.setObjectName("Primary")
        calc_btn.clicked.connect(self._orbit)
        fl.addRow(calc_btn)
        self.o_out = QTextEdit()
        self.o_out.setReadOnly(True)
        self.o_out.setMaximumHeight(130)
        fl.addRow(self.o_out)
        lay.addWidget(box, 0)
        self.o_chart = ChartWidget()
        lay.addWidget(self.o_chart, 1)
        self._orbit()
        return container

    def _orbit(self) -> None:
        a = self.o_a.value() * astro.AU_M
        e = self.o_e.value()
        T_days = astro.orbital_period_semi_major_axis(a, astro.M_SUN) / astro.DAY_S
        v_circ = astro.orbital_velocity_circular(a, astro.M_SUN)
        v_esc = astro.escape_velocity(a, astro.M_SUN)
        x, y = astro.orbit_sample(self.o_a.value(), e)
        self.o_chart.plot_xy(x, y, "x (AU)", "y (AU)", "Elliptical orbit", ACCENT)
        self.o_out.setPlainText(
            f"Period: {T_days:.3f} days\n"
            f"Circular velocity at a: {v_circ/1000:.3f} km/s\n"
            f"Escape velocity at a: {v_esc/1000:.3f} km/s\n"
            f"Light travel time at a: {astro.light_travel_time_from_sun(self.o_a.value()):.2f} min"
        )

    def _build_moon(self) -> QWidget:
        container = QWidget()
        lay = QHBoxLayout(container)
        box = QGroupBox("Lunar phase (approx.)")
        fl = QFormLayout(box)
        self.m_days = QDoubleSpinBox(); self.m_days.setRange(0, 29.53); self.m_days.setDecimals(2); self.m_days.setValue(0)
        self.m_days.setSuffix(" days since new moon")
        fl.addRow("Days", self.m_days)
        calc_btn = QPushButton("Phase")
        calc_btn.setObjectName("Primary")
        calc_btn.clicked.connect(self._moon)
        fl.addRow(calc_btn)
        self.m_out = QTextEdit()
        self.m_out.setReadOnly(True)
        fl.addRow(self.m_out)
        lay.addWidget(box, 0)
        # Illumination curve chart.
        self.m_chart = ChartWidget()
        lay.addWidget(self.m_chart, 1)
        # Pre-draw illumination curve.
        days = np.linspace(0, 29.530588853, 200)
        illum = [astro.moon_phase_illumination(d)["illumination"] for d in days]
        self.m_chart.plot_xy(days, illum, "days", "illumination", "Lunar illumination cycle", ACCENT_BLUE)
        self._moon()
        return container

    def _moon(self) -> None:
        res = astro.moon_phase_illumination(self.m_days.value())
        self.m_out.setPlainText(
            f"Phase: {res['phase_name']}\n"
            f"Illumination: {res['illumination']*100:.1f}%\n"
            f"Cycle fraction: {res['phase_fraction']*100:.1f}%"
        )