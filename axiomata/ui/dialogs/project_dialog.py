"""New / edit research project dialog."""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

DISCIPLINES = [
    "physics",
    "chemistry",
    "biology",
    "astronomy",
    "mechanical_engineering",
    "electrical_engineering",
    "civil_engineering",
    "mathematics",
    "interdisciplinary",
]


class ProjectDialog(QDialog):
    """Collects title, description, disciplines, objectives, hypothesis."""

    def __init__(self, parent: Optional[QWidget] = None, edit: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Edit Project" if edit else "New Research Project")
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.title = QLineEdit()
        self.title.setPlaceholderText("e.g. Study of damped harmonic oscillators")
        form.addRow("Title *", self.title)

        self.description = QPlainTextEdit()
        self.description.setPlaceholderText("Short description of the research…")
        self.description.setFixedHeight(70)
        form.addRow("Description", self.description)

        # Disciplines as checkboxes in a flow
        disc_widget = QWidget()
        disc_lay = QVBoxLayout(disc_widget)
        disc_lay.setContentsMargins(0, 0, 0, 0)
        disc_lay.setSpacing(4)
        self.disc_checks: dict[str, QCheckBox] = {}
        row_widgets: list[QCheckBox] = []
        for i, disc in enumerate(DISCIPLINES):
            cb = QCheckBox(disc.replace("_", " ").title())
            self.disc_checks[disc] = cb
            row_widgets.append(cb)
        # Arrange in two columns.
        for i in range(0, len(row_widgets), 2):
            row = QWidget()
            rl = QVBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(4)
            rl.addWidget(row_widgets[i])
            if i + 1 < len(row_widgets):
                rl.addWidget(row_widgets[i + 1])
            else:
                rl.addStretch(1)
            disc_lay.addWidget(row)
        form.addRow("Disciplines", disc_widget)

        self.objectives = QPlainTextEdit()
        self.objectives.setPlaceholderText("Research objectives…")
        self.objectives.setFixedHeight(60)
        form.addRow("Objectives", self.objectives)

        self.hypothesis = QPlainTextEdit()
        self.hypothesis.setPlaceholderText("Hypothesis (optional)…")
        self.hypothesis.setFixedHeight(60)
        form.addRow("Hypothesis", self.hypothesis)

        root.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttons.accepted.connect(self._on_accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

        self._edit = edit

    def _on_accept(self) -> None:
        if not self.title.text().strip():
            self.title.setFocus()
            self.title.setStyleSheet("border:1px solid #ef4444;")
            return
        self.accept()

    def disciplines_selected(self) -> list[str]:
        return [k for k, cb in self.disc_checks.items() if cb.isChecked()]

    def values(self) -> dict:
        return {
            "title": self.title.text().strip(),
            "description": self.description.toPlainText().strip(),
            "disciplines": self.disciplines_selected(),
            "objectives": self.objectives.toPlainText().strip(),
            "hypothesis": self.hypothesis.toPlainText().strip(),
        }

    def set_values(self, project: dict) -> None:
        self.title.setText(project.get("title", ""))
        self.description.setPlainText(project.get("description", ""))
        self.objectives.setPlainText(project.get("objectives", ""))
        self.hypothesis.setPlainText(project.get("hypothesis", ""))
        selected = set(project.get("disciplines") or [])
        for k, cb in self.disc_checks.items():
            cb.setChecked(k in selected)