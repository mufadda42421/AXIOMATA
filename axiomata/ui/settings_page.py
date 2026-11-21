"""Settings page: profession, appearance, units, autosave, backups, about."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..core.application import AppContext
from ..core.professions import PROFESSIONS
from .panels.base_page import BasePage
from .. import __version__


class SettingsPage(BasePage):
    settings_saved = Signal()

    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Settings", "Personalise AXIOMATA. Changes apply immediately or on save.", parent)
        self.ctx = ctx
        self.setObjectName("SettingsPage")
        self._build()
        self._load()

    def _build(self) -> None:
        # Profession
        prof_group = QGroupBox("Profession & Workspace")
        prof_form = QFormLayout(prof_group)
        self.prof_combo = QComboBox()
        for p in PROFESSIONS:
            self.prof_combo.addItem(f"{p.icon}  {p.name}", p.key)
        prof_form.addRow("Profession", self.prof_combo)
        hint = QLabel(
            "Profession personalises your dashboard and shortcuts. It does not restrict "
            "access — every laboratory remains available."
        )
        hint.setObjectName("MutedLabel")
        hint.setWordWrap(True)
        prof_form.addRow("", hint)
        self.body_layout.addWidget(prof_group)

        # Appearance
        appear_group = QGroupBox("Appearance")
        appear_form = QFormLayout(appear_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark (Scientific)", "dark")
        self.theme_combo.addItem("Light", "light")
        appear_form.addRow("Theme", self.theme_combo)
        self.body_layout.addWidget(appear_group)

        # Units
        units_group = QGroupBox("Units & Simulation")
        units_form = QFormLayout(units_group)
        self.units_combo = QComboBox()
        self.units_combo.addItem("SI (International System)", "SI")
        self.units_combo.addItem("Imperial", "imperial")
        units_form.addRow("Default units", self.units_combo)
        self.body_layout.addWidget(units_group)

        # Autosave & backup
        data_group = QGroupBox("Data & Reliability")
        data_form = QFormLayout(data_group)
        self.autosave_check = QCheckBox("Enable autosave")
        data_form.addRow(self.autosave_check)
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(15, 3600)
        self.autosave_interval.setSuffix(" sec")
        data_form.addRow("Autosave interval", self.autosave_interval)
        self.backup_check = QCheckBox("Enable periodic backups")
        data_form.addRow(self.backup_check)
        self.body_layout.addWidget(data_group)

        # Data location + actions
        loc_group = QGroupBox("Storage")
        loc_form = QFormLayout(loc_group)
        self.loc_label = QLabel(str(self.ctx.paths.root))
        self.loc_label.setWordWrap(True)
        loc_form.addRow("Data directory", self.loc_label)
        self.body_layout.addWidget(loc_group)

        # Buttons
        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addStretch(1)
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setObjectName("Primary")
        self.save_btn.clicked.connect(self._save)
        self.reset_btn = QPushButton("Reset Workspace…")
        self.reset_btn.setObjectName("Ghost")
        self.reset_btn.clicked.connect(self._reset_workspace)
        bl.addWidget(self.reset_btn)
        bl.addWidget(self.save_btn)
        self.body_layout.addWidget(btn_row)

        self.about_label = QLabel(
            f"AXIOMATA v{__version__} — Explore. Experiment. Understand.\n"
            "Offline scientific research & simulation environment."
        )
        self.about_label.setObjectName("MutedLabel")
        self.body_layout.addWidget(self.about_label)
        self.body_layout.addStretch(1)

    def _load(self) -> None:
        s = self.ctx.settings
        self._select_combo_value(self.prof_combo, s.get("profession"))
        self._select_combo_value(self.theme_combo, s.get("theme"))
        self._select_combo_value(self.units_combo, s.get("default_units"))
        self.autosave_check.setChecked(bool(s.get("autosave_enabled")))
        self.autosave_interval.setValue(int(s.get("autosave_interval_sec") or 60))
        self.backup_check.setChecked(bool(s.get("backup_enabled")))

    @staticmethod
    def _select_combo_value(combo: QComboBox, value) -> None:
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _save(self) -> None:
        s = self.ctx.settings
        s.update(
            profession=self.prof_combo.currentData(),
            theme=self.theme_combo.currentData(),
            default_units=self.units_combo.currentData(),
            autosave_enabled=self.autosave_check.isChecked(),
            autosave_interval_sec=self.autosave_interval.value(),
            backup_enabled=self.backup_check.isChecked(),
        )
        s.save()
        self.ctx.events.publish("settings.changed")
        QMessageBox.information(self, "Settings", "Settings saved.")
        self.settings_saved.emit()

    def _reset_workspace(self) -> None:
        resp = QMessageBox.warning(
            self,
            "Reset workspace",
            "This clears all preferences and the profession selection so AXIOMATA "
            "shows onboarding again on next launch. Projects and datasets on disk are "
            "NOT deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            s = self.ctx.settings
            s.set("profession", None)
            s.set("onboarded", False)
            s.set("active_project_id", None)
            s.save()
            QMessageBox.information(
                self, "Reset", "Preferences reset. Restart to choose a profession again."
            )