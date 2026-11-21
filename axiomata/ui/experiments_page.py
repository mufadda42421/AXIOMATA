"""Experiments page: create, list, and view experiment records per project."""
from __future__ import annotations

import json
from typing import Optional

from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QInputDialog, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout,
    QWidget,
)

from ..core.application import AppContext
from ..ui.panels.base_page import BasePage


class ExperimentsPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Experiment Records",
                         "Create and manage experiments linked to your research projects.",
                         parent)
        self.ctx = ctx
        self._current_exp_id: Optional[str] = None
        self._build()
        self._load()

    def _build(self) -> None:
        new_btn = QPushButton("+ New Experiment")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self._new_experiment)
        self.add_toolbar_widget(new_btn)

        self.save_btn = QPushButton("Save Results")
        self.save_btn.clicked.connect(self._save_results)
        self.add_toolbar_widget(self.save_btn)

        body = QHBoxLayout()
        body.setSpacing(8)

        self.exp_list = QListWidget()
        self.exp_list.setMaximumWidth(280)
        self.exp_list.currentItemChanged.connect(self._on_selected)
        body.addWidget(self.exp_list, 0)

        right = QVBoxLayout()
        self.exp_title = QLabel("No experiment selected")
        self.exp_title.setObjectName("H2")
        right.addWidget(self.exp_title)

        params_box = QGroupBox("Parameters (JSON)")
        pl = QVBoxLayout(params_box)
        self.params_view = QPlainTextEdit()
        self.params_view.setReadOnly(True)
        self.params_view.setStyleSheet("font-family: Consolas, monospace;")
        pl.addWidget(self.params_view)
        right.addWidget(params_box, 1)

        results_box = QGroupBox("Results / Notes")
        rl = QVBoxLayout(results_box)
        self.results_edit = QPlainTextEdit()
        self.results_edit.setStyleSheet("font-family: Consolas, monospace;")
        rl.addWidget(self.results_edit)
        right.addWidget(results_box, 2)

        rw = QWidget()
        rw.setLayout(right)
        body.addWidget(rw, 1)

        w = QWidget()
        w.setLayout(body)
        self.add_body_widget(w, 1)

    def _active_project_id(self) -> Optional[str]:
        proj = self.ctx.active_project
        return proj["id"] if proj else None

    def _load(self) -> None:
        self.exp_list.blockSignals(True)
        self.exp_list.clear()
        pid = self._active_project_id()
        if pid:
            for e in self.ctx.experiments.list_for_project(pid):
                item = QListWidgetItem(e["name"])
                item.setData(256, e["id"])
                item.setToolTip(f"{e.get('discipline','')} · {e.get('kind','')}")
                self.exp_list.addItem(item)
        self.exp_list.blockSignals(False)
        if self.exp_list.count() > 0:
            self.exp_list.setCurrentRow(0)
        else:
            self._current_exp_id = None
            self.exp_title.setText("No experiment selected")
            self.params_view.clear()
            self.results_edit.clear()

    def _new_experiment(self) -> None:
        pid = self._active_project_id()
        if not pid:
            QMessageBox.information(
                self, "No project",
                "Open or create a research project first to add experiments."
            )
            return
        name, ok = QInputDialog.getText(self, "New Experiment", "Experiment name:")
        if not ok or not name.strip():
            return
        exp = self.ctx.experiments.create(project_id=pid, name=name.strip())
        self._load()
        for i in range(self.exp_list.count()):
            if self.exp_list.item(i).data(256) == exp["id"]:
                self.exp_list.setCurrentRow(i)
                break

    def _on_selected(self, current: QListWidgetItem, _previous) -> None:
        if current is None:
            return
        eid = current.data(256)
        self._current_exp_id = eid
        exp = self.ctx.experiments.get(eid)
        if not exp:
            return
        self.exp_title.setText(
            f"{exp['name']}  ·  {exp.get('discipline') or 'generic'}  ·  {exp.get('kind')}"
        )
        params = exp.get("parameters") or {}
        self.params_view.setPlainText(json.dumps(params, indent=2))
        self.results_edit.setPlainText(exp.get("notes", ""))

    def _save_results(self) -> None:
        if not self._current_exp_id:
            return
        notes = self.results_edit.toPlainText()
        self.ctx.experiments.update(self._current_exp_id, notes=notes)
        # Show saved indicator via title.
        self.exp_title.setText(self.exp_title.text() + "  ✓")

    def refresh(self) -> None:
        self._load()