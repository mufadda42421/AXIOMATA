"""Research Notebook page.

A digital scientific notebook with project-linked pages. Each page is a Markdown
document autosaved to the SQLite ``notes`` table. Supports creating, switching,
and deleting notes, plus Markdown export to a file. A live preview renders the
Markdown to HTML.
"""
from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QInputDialog, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

from ..core.application import AppContext
from ..ui.panels.base_page import BasePage

# A very small Markdown -> HTML converter sufficient for notebook preview.
import re
import html as _html


def _markdown_to_html(md: str) -> str:
    """Convert a subset of Markdown to HTML for the preview pane.

    Supports: headings, bold/italic, inline code, code blocks, lists,
    blockquotes, links, and paragraphs. This is intentionally minimal and safe
    (all text is HTML-escaped before formatting).
    """
    # Escape HTML first.
    text = _html.escape(md)

    # Code blocks (```...```).
    def _code_block(m):
        code = m.group(1)
        return f"<pre style='background:#0e1728;padding:8px;border-radius:6px;'><code>{code}</code></pre>"

    text = re.sub(r"```(.*?)```", _code_block, text, flags=re.DOTALL)

    lines = text.split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>"); in_ul = False
        if in_ol:
            out.append("</ol>"); in_ol = False

    for line in lines:
        # Headings
        hm = re.match(r"^(#{1,6})\s+(.*)", line)
        if hm:
            close_lists()
            level = len(hm.group(1))
            out.append(f"<h{level}>{hm.group(2)}</h{level}>")
            continue
        # Unordered list
        um = re.match(r"^[-*]\s+(.*)", line)
        if um:
            if in_ol:
                out.append("</ol>"); in_ol = False
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{_inline(um.group(1))}</li>")
            continue
        # Ordered list
        om = re.match(r"^\d+\.\s+(.*)", line)
        if om:
            if in_ul:
                out.append("</ul>"); in_ul = False
            if not in_ol:
                out.append("<ol>"); in_ol = True
            out.append(f"<li>{_inline(om.group(1))}</li>")
            continue
        # Blockquote
        if line.startswith("&gt; "):
            close_lists()
            out.append(f"<blockquote>{_inline(line[5:])}</blockquote>")
            continue
        # Blank line
        if line.strip() == "":
            close_lists()
            out.append("<br>")
            continue
        close_lists()
        out.append(f"<p>{_inline(line)}</p>")

    close_lists()
    return "\n".join(out)


def _inline(text: str) -> str:
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r"<code style='background:#0e1728;padding:1px 4px;border-radius:3px;'>\1</code>", text)
    # Links [text](url)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"<a href='\2'>\1</a>", text)
    return text


class NotebookPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("Research Notebook",
                         "Project-linked scientific notes with Markdown autosave & preview.",
                         parent)
        self.ctx = ctx
        self._current_note_id: Optional[str] = None
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(1500)
        self._autosave_timer.timeout.connect(self._autosave)

        self._build()
        self._load_notes()

        # Refresh when active project changes.
        self.ctx.events.subscribe("project.opened", self._on_project_changed)

    def _build(self) -> None:
        # Toolbar
        new_btn = QPushButton("+ New Note")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self._new_note)
        self.add_toolbar_widget(new_btn)

        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self._delete_note)
        self.add_toolbar_widget(del_btn)

        export_btn = QPushButton("Export .md")
        export_btn.clicked.connect(self._export)
        self.add_toolbar_widget(export_btn)

        self.autosave_lbl = QLabel("Saved")
        self.autosave_lbl.setObjectName("MutedLabel")
        self.add_toolbar_widget(self.autosave_lbl)

        # Main: list | editor/preview tabs
        body = QHBoxLayout()
        body.setSpacing(8)

        self.note_list = QListWidget()
        self.note_list.setMaximumWidth(240)
        self.note_list.currentItemChanged.connect(self._on_note_selected)
        body.addWidget(self.note_list, 0)

        self.tabs = QTabWidget()
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write your scientific notes in Markdown…")
        self.editor.textChanged.connect(self._on_text_changed)
        self.tabs.addTab(self.editor, "Editor")

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.tabs.addTab(self.preview, "Preview")
        body.addWidget(self.tabs, 1)

        w = QWidget()
        w.setLayout(body)
        self.add_body_widget(w, 1)

    # -- data -------------------------------------------------------------
    def _active_project_id(self) -> Optional[str]:
        proj = self.ctx.active_project
        return proj["id"] if proj else None

    def _load_notes(self) -> None:
        self.note_list.blockSignals(True)
        self.note_list.clear()
        pid = self._active_project_id()
        notes = self.ctx.notes.list_for_project(pid) if pid else []
        for n in notes:
            item = QListWidgetItem(n.get("title") or "(untitled)")
            item.setData(256, n["id"])  # Qt.UserRole = 256
            self.note_list.addItem(item)
        self.note_list.blockSignals(False)
        if self.note_list.count() > 0:
            self.note_list.setCurrentRow(0)
        else:
            self._current_note_id = None
            self.editor.clear()
            self.preview.setHtml("")

    def _on_project_changed(self, *_args) -> None:
        self._flush_autosave()
        self._load_notes()

    def _on_note_selected(self, current: QListWidgetItem, _previous) -> None:
        self._flush_autosave()
        if current is None:
            self._current_note_id = None
            self.editor.clear()
            self.preview.setHtml("")
            return
        nid = current.data(256)
        self._current_note_id = nid
        note = self.ctx.notes.get(nid)
        if note:
            self.editor.setPlainText(note.get("body", ""))
            self.preview.setHtml(_markdown_to_html(note.get("body", "")))
        self.autosave_lbl.setText("Saved")

    # -- editing ----------------------------------------------------------
    def _new_note(self) -> None:
        pid = self._active_project_id()
        if not pid:
            QMessageBox.information(
                self, "No project",
                "Open or create a research project first to link notes to it."
            )
            return
        title, ok = QInputDialog.getText(self, "New Note", "Note title:")
        if not ok or not title.strip():
            return
        note = self.ctx.notes.create(pid, title=title.strip(), body="")
        self._load_notes()
        # Select the new note.
        for i in range(self.note_list.count()):
            item = self.note_list.item(i)
            if item.data(256) == note["id"]:
                self.note_list.setCurrentRow(i)
                break
        self.editor.setFocus()

    def _delete_note(self) -> None:
        if not self._current_note_id:
            return
        resp = QMessageBox.question(
            self, "Delete note", "Delete this note permanently?",
            QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.ctx.notes.delete(self._current_note_id)
            self._current_note_id = None
            self._load_notes()

    def _on_text_changed(self) -> None:
        # Update preview live and schedule autosave.
        self.preview.setHtml(_markdown_to_html(self.editor.toPlainText()))
        self.autosave_lbl.setText("Unsaved…")
        self._autosave_timer.start()

    def _autosave(self) -> None:
        self._autosave_timer.stop()
        self._flush_autosave()

    def _flush_autosave(self) -> None:
        if not self._current_note_id:
            return
        body = self.editor.toPlainText()
        self.ctx.notes.update(self._current_note_id, body=body)
        self.autosave_lbl.setText("Saved")

    def _export(self) -> None:
        body = self.editor.toPlainText()
        if not body.strip():
            QMessageBox.information(self, "Empty", "The current note is empty.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export note", "note.md", "Markdown (*.md);;Text (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(body)
                self.autosave_lbl.setText(f"Exported to {os.path.basename(path)}")
            except OSError as exc:
                QMessageBox.warning(self, "Export failed", str(exc))

    def refresh(self) -> None:
        self._load_notes()