"""Simple forms for creating a paper layout without editing JSON."""

from __future__ import annotations

import json
import os
import re
import tempfile
from copy import deepcopy
from uuid import uuid4

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPlainTextEdit,
    QPushButton, QSpinBox, QVBoxLayout,
)

from core.format_loader import FormatError, calculated_total_marks, validate_format
from core.word_template import WordTemplateError, inspect_word_template, template_body_choices


class SectionDialog(QDialog):
    def __init__(self, parent=None, section: dict | None = None, number: int = 1) -> None:
        super().__init__(parent)
        section = section or {}
        self.setWindowTitle("Section details")
        self.setMinimumWidth(400)
        self.sid = QLineEdit(str(section.get("id", chr(64 + min(number, 26)))))
        self.title = QLineEdit(section.get("title", f"Section {self.sid.text()}"))
        self.description = QLineEdit(section.get("description", ""))
        self.qtype = QComboBox()
        self.qtype.addItem("Multiple choice", "MCQ")
        self.qtype.addItem("Short answer", "short_answer")
        self.qtype.addItem("Long answer", "long_answer")
        self.qtype.setCurrentIndex(max(0, self.qtype.findData(section.get("question_type", "short_answer"))))
        self.count = QSpinBox()
        self.count.setRange(1, 200)
        self.count.setValue(section.get("total_questions", 5))
        self.attempt_count = QSpinBox()
        self.attempt_count.setRange(1, self.count.value())
        self.attempt_count.setValue(section.get("attempt_count", self.count.value()))
        self._last_count = self.count.value()
        self.count.valueChanged.connect(self._update_attempt_limit)
        self.start_number = QSpinBox()
        self.start_number.setRange(1, 999)
        self.start_number.setValue(section.get("start_number", 1))
        self.marks = QDoubleSpinBox()
        self.marks.setRange(0, 100)
        self.marks.setDecimals(1)
        self.marks.setValue(section.get("marks_per_question", 1))
        self.parts = QLineEdit(", ".join(section.get("sub_parts") or []))
        self.parts.setPlaceholderText("Optional: a, b, c")

        form = QFormLayout()
        form.addRow("Section letter", self.sid)
        form.addRow("Heading on paper", self.title)
        form.addRow("Instructions for section", self.description)
        form.addRow("Question type", self.qtype)
        form.addRow("Number of questions", self.count)
        form.addRow("Students answer", self.attempt_count)
        form.addRow("First printed question number", self.start_number)
        form.addRow("Marks per question", self.marks)
        form.addRow("Sub-parts", self.parts)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept_valid)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _accept_valid(self) -> None:
        if not self.sid.text().strip() or not self.title.text().strip():
            QMessageBox.warning(self, "Section needs a name", "Enter a section letter and a heading.")
            return
        self.accept()

    def _update_attempt_limit(self, count: int) -> None:
        answer_all = self.attempt_count.value() == self._last_count
        self.attempt_count.setMaximum(count)
        if answer_all:
            self.attempt_count.setValue(count)
        self._last_count = count

    def section_data(self) -> dict:
        parts = [part.strip() for part in self.parts.text().split(",") if part.strip()]
        return {
            "id": self.sid.text().strip(),
            "title": self.title.text().strip(),
            "description": self.description.text().strip(),
            "question_type": self.qtype.currentData(),
            "marks_per_question": self.marks.value(),
            "total_questions": self.count.value(),
            "attempt_count": self.attempt_count.value(),
            "start_number": self.start_number.value(),
            "sub_parts": parts or None,
        }


class FormatWizard(QDialog):
    def __init__(self, parent=None, source: dict | None = None) -> None:
        super().__init__(parent)
        source = deepcopy(source or {})
        self.sections = source.get("sections", [])
        self._docx_template = source.get("docx_template")
        self._template_body_start = source.get("template_body_start")
        self.setWindowTitle("Create a paper format")
        self.setMinimumSize(580, 570)
        self.display_name = QLineEdit(source.get("display_name", ""))
        self.display_name.setPlaceholderText("For example: Chemistry Unit Test — Class 7")
        self.school = QLineEdit(source.get("school_name", ""))
        self.paper_title = QLineEdit(source.get("paper_title", ""))
        self.subject = QLineEdit(source.get("subject", ""))
        self.klass = QLineEdit(str(source.get("class", "")))
        self.duration = QLineEdit(source.get("duration", ""))
        self.duration.setPlaceholderText("For example: 2 hours")
        self.instructions = QPlainTextEdit()
        self.instructions.setPlaceholderText("One instruction per line")
        self.instructions.setPlainText("\n".join(source.get("instructions") or []))
        self.instructions.setFixedHeight(75)

        form = QFormLayout()
        form.addRow("Template name", self.display_name)
        form.addRow("School name", self.school)
        form.addRow("Exam / paper title", self.paper_title)
        form.addRow("Subject", self.subject)
        form.addRow("Class", self.klass)
        form.addRow("Time allowed", self.duration)
        form.addRow("General instructions", self.instructions)
        self.template_boundary = None
        if self._docx_template:
            self.word_file_label = QLabel(os.path.basename(self._docx_template))
            self.word_file_label.setWordWrap(True)
            replace_word = QPushButton("Replace Word file…")
            replace_word.setObjectName("Ghost")
            replace_word.clicked.connect(self._replace_word_file)
            source_row = QHBoxLayout()
            source_row.addWidget(self.word_file_label, 1)
            source_row.addWidget(replace_word)
            form.addRow("Saved Word layout", source_row)
            self.template_boundary = QComboBox()
            self.template_boundary.setMinimumContentsLength(35)
            self.template_boundary.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            self._refresh_template_choices()
            form.addRow("Replace old questions from", self.template_boundary)
            note = QLabel("The lines above this point stay in every new paper. Everything after it is replaced with your new questions.")
            note.setWordWrap(True)
            form.addRow("", note)

        self.section_list = QListWidget()
        self.section_list.itemDoubleClicked.connect(self._edit_section)
        add = QPushButton("Add Section")
        add.clicked.connect(self._add_section)
        edit = QPushButton("Edit")
        edit.setObjectName("Ghost")
        edit.clicked.connect(self._edit_section)
        remove = QPushButton("Remove")
        remove.setObjectName("Danger")
        remove.clicked.connect(self._remove_section)
        row = QHBoxLayout()
        row.addWidget(add)
        row.addWidget(edit)
        row.addWidget(remove)
        row.addStretch()
        self.total_label = QLabel()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept_valid)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel("Sections, in paper order"))
        layout.addWidget(self.section_list, 1)
        layout.addLayout(row)
        layout.addWidget(self.total_label)
        layout.addWidget(buttons)
        self._refresh()

    def _refresh_template_choices(self) -> None:
        self.template_boundary.clear()
        if os.path.isfile(self._docx_template):
            for index, text in template_body_choices(self._docx_template):
                self.template_boundary.addItem(text, index)
            chosen = self.template_boundary.findData(self._template_body_start)
            if chosen >= 0:
                self.template_boundary.setCurrentIndex(chosen)
            self.template_boundary.setEnabled(True)
        else:
            self.template_boundary.addItem("Word template file is missing", self._template_body_start)
            self.template_boundary.setEnabled(False)

    def _replace_word_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose the revised Word template", "", "Word documents (*.docx)"
        )
        if not path:
            return
        try:
            proposal = inspect_word_template(path)
        except (WordTemplateError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "Couldn't read Word file", str(exc))
            return
        self._docx_template = proposal["docx_template"]
        self._template_body_start = proposal["template_body_start"]
        self.word_file_label.setText(os.path.basename(path))
        self._refresh_template_choices()
        self.school.setText(proposal["school_name"])
        self.paper_title.setText(proposal["paper_title"])
        self.subject.setText(proposal["subject"])
        self.klass.setText(proposal["class"])
        self.duration.setText(proposal["duration"])
        self.instructions.setPlainText("\n".join(proposal["instructions"]))
        self.sections = proposal["sections"]
        self._refresh()

    def _refresh(self) -> None:
        self.section_list.clear()
        for section in self.sections:
            attempt = section.get("attempt_count", section["total_questions"])
            choice = f"; answer any {attempt}" if attempt < section["total_questions"] else ""
            self.section_list.addItem(
                f"{section['title']}  ·  {section['total_questions']} questions{choice} × {section['marks_per_question']} marks"
            )
        total = calculated_total_marks({"sections": self.sections})
        self.total_label.setText(f"Maximum marks: {total:g} (calculated from sections)")

    def _add_section(self) -> None:
        dialog = SectionDialog(self, number=len(self.sections) + 1)
        if dialog.exec():
            self.sections.append(dialog.section_data())
            self._refresh()

    def _edit_section(self, *_args) -> None:
        index = self.section_list.currentRow()
        if index < 0:
            return
        dialog = SectionDialog(self, self.sections[index])
        if dialog.exec():
            self.sections[index] = dialog.section_data()
            self._refresh()
            self.section_list.setCurrentRow(index)

    def _remove_section(self) -> None:
        index = self.section_list.currentRow()
        if index >= 0:
            del self.sections[index]
            self._refresh()

    def _accept_valid(self) -> None:
        if not self.subject.text().strip() or not self.klass.text().strip() or not self.sections:
            QMessageBox.warning(self, "More details needed", "Enter a subject and class, then add at least one section.")
            return
        try:
            validate_format(self.format_data())
        except FormatError as exc:
            QMessageBox.warning(self, "Check your format", str(exc))
            return
        self.accept()

    def format_data(self) -> dict:
        subject = self.subject.text().strip()
        klass = self.klass.text().strip()
        stem = re.sub(r"[^a-z0-9]+", "_", f"class_{klass}_{subject}".lower()).strip("_")
        total = calculated_total_marks({"sections": self.sections})
        return {
            "format_id": stem,
            "display_name": self.display_name.text().strip() or f"Class {klass} — {subject}",
            "school_name": self.school.text().strip(),
            "paper_title": self.paper_title.text().strip(),
            "subject": subject,
            "class": klass,
            "total_marks": total,
            "duration": self.duration.text().strip(),
            "instructions": [line.strip() for line in self.instructions.toPlainText().splitlines() if line.strip()],
            "sections": deepcopy(self.sections),
            "docx_template": self._docx_template,
            "template_body_start": self.template_boundary.currentData() if self.template_boundary else self._template_body_start,
        }


def save_new_format(fmt: dict, directory: str) -> str:
    """Save as a new file, never replacing an existing format."""
    validate_format(fmt)
    os.makedirs(directory, exist_ok=True)
    stem = fmt["format_id"]
    path = os.path.join(directory, f"{stem}.json")
    if os.path.exists(path):
        stem = f"{stem}_{uuid4().hex[:6]}"
        fmt["format_id"] = stem
        path = os.path.join(directory, f"{stem}.json")
    stored = deepcopy(fmt)
    template = stored.get("docx_template")
    if template and os.path.isabs(template):
        stored["docx_template"] = os.path.relpath(template, directory)
    with open(path, "x", encoding="utf-8") as file:
        json.dump(stored, file, ensure_ascii=False, indent=2)
    return path


def update_format(fmt: dict, path: str) -> None:
    """Replace a format after validation, keeping its existing file name."""
    validate_format(fmt)
    directory = os.path.dirname(os.path.abspath(path))
    stored = deepcopy(fmt)
    template = stored.get("docx_template")
    if template and os.path.isabs(template):
        stored["docx_template"] = os.path.relpath(template, directory)
    fd, temporary = tempfile.mkstemp(prefix=".format_", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(stored, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
