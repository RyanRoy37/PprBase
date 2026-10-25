"""Reusable question-entry widget that adapts to the question type.

Emits ``question_saved(section_id, question_num)`` after writing into the shared
:class:`PaperState`. The form reads its initial values from state so navigating
between questions shows what was previously entered.
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.state_manager import PaperState
from ui.image_picker import ImagePicker
from ui.table_dialog import TableDialog


class QuestionForm(QWidget):
    question_saved = pyqtSignal(str, int)

    def __init__(self, state: PaperState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self.section: dict[str, Any] = {}
        self.section_id = ""
        self.question_num = 1
        self.sub_part: Optional[str] = None

        # Staged attachments (committed on Save).
        self._image_def: dict[str, Any] = {}
        self._table_def: Optional[dict[str, Any]] = None
        self._loading = False
        self.dirty = False

        self._build_ui()

    # -- ui construction --------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.heading = QLabel("Question")
        self.heading.setObjectName("FieldLabel")
        layout.addWidget(self.heading)

        layout.addWidget(self._label("Question text"))
        notation_row = QHBoxLayout()
        for title, mapping, fallback in (
            ("Subscript ₂", str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎"), "₂"),
            ("Superscript ²", str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"), "²"),
        ):
            button = QPushButton(title)
            button.setObjectName("Ghost")
            button.setToolTip("Select a number in the question and click to format it")
            button.clicked.connect(lambda _checked=False, m=mapping, f=fallback: self._insert_notation(m, f))
            notation_row.addWidget(button)
        notation_row.addStretch()
        layout.addLayout(notation_row)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type the question here…")
        self.text_edit.setFixedHeight(110)
        self.text_edit.textChanged.connect(self._mark_dirty)
        layout.addWidget(self.text_edit)

        # MCQ options group (shown only for MCQ).
        self.mcq_group = QGroupBox("Answer options")
        mcq_layout = QVBoxLayout(self.mcq_group)
        self.option_edits: list[QLineEdit] = []
        for i in range(4):
            row = QHBoxLayout()
            lbl = QLabel(f"({'abcd'[i]})")
            lbl.setFixedWidth(28)
            edit = QLineEdit()
            edit.setPlaceholderText(f"Option {'abcd'[i]}")
            row.addWidget(lbl)
            row.addWidget(edit)
            mcq_layout.addLayout(row)
            self.option_edits.append(edit)
            edit.textChanged.connect(self._mark_dirty)
        answer_row = QHBoxLayout()
        answer_row.addWidget(self._label("Correct answer"))
        self.answer_combo = QComboBox()
        self.answer_combo.addItems(["Choose answer", "(a)", "(b)", "(c)", "(d)"])
        self.answer_combo.currentIndexChanged.connect(self._mark_dirty)
        answer_row.addWidget(self.answer_combo)
        answer_row.addStretch()
        mcq_layout.addLayout(answer_row)
        layout.addWidget(self.mcq_group)

        self.model_answer_group = QGroupBox("Answer key (optional)")
        answer_layout = QVBoxLayout(self.model_answer_group)
        self.model_answer = QTextEdit()
        self.model_answer.setPlaceholderText("Type a suggested answer for the separate answer key…")
        self.model_answer.setFixedHeight(70)
        self.model_answer.textChanged.connect(self._mark_dirty)
        answer_layout.addWidget(self.model_answer)
        layout.addWidget(self.model_answer_group)

        # Marks.
        marks_row = QHBoxLayout()
        marks_row.addWidget(self._label("Marks"))
        self.marks_spin = QDoubleSpinBox()
        self.marks_spin.setRange(0, 100)
        self.marks_spin.setDecimals(1)
        self.marks_spin.setSingleStep(0.5)
        self.marks_spin.valueChanged.connect(self._mark_dirty)
        marks_row.addWidget(self.marks_spin)
        marks_row.addStretch()
        layout.addLayout(marks_row)

        # Attachments.
        attach_row = QHBoxLayout()
        self.image_btn = QPushButton("Attach Image")
        self.image_btn.setObjectName("Ghost")
        self.image_btn.clicked.connect(self._attach_image)
        self.table_btn = QPushButton("Add Table")
        self.table_btn.setObjectName("Ghost")
        self.table_btn.clicked.connect(self._add_table)
        attach_row.addWidget(self.image_btn)
        attach_row.addWidget(self.table_btn)
        attach_row.addStretch()
        layout.addLayout(attach_row)

        self.attach_status = QLabel("")
        self.attach_status.setObjectName("Hint")
        layout.addWidget(self.attach_status)

        layout.addStretch()

        save_row = QHBoxLayout()
        save_row.addStretch()
        self.clear_btn = QPushButton("Clear this question")
        self.clear_btn.setObjectName("Danger")
        self.clear_btn.clicked.connect(self._clear_question)
        self.save_btn = QPushButton("Save Question")
        self.save_btn.clicked.connect(self.save)
        save_row.addWidget(self.clear_btn)
        save_row.addWidget(self.save_btn)
        layout.addLayout(save_row)

    @staticmethod
    def _label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        return lbl

    # -- loading a question ----------------------------------------------
    def load(
        self,
        section: dict[str, Any],
        question_num: int,
        sub_part: Optional[str] = None,
    ) -> None:
        self._loading = True
        self.section = section
        self.section_id = section.get("id", "")
        self.question_num = question_num
        self.sub_part = sub_part
        qtype = section.get("question_type", "short_answer")

        is_mcq = qtype == "MCQ"
        self.mcq_group.setVisible(is_mcq)
        self.model_answer_group.setVisible(not is_mcq and not sub_part)

        existing = self.state.get_question(self.section_id, question_num) or {}

        # Heading reflects question + optional sub-part.
        sub_label = f" — part ({sub_part})" if sub_part else ""
        printed_number = section.get("start_number", 1) + question_num - 1
        self.heading.setText(f"{section.get('title','')}  ·  Q{printed_number}{sub_label}")

        # Populate fields. With a sub-part selected we edit that sub-part's text.
        self._image_def = {
            k: existing.get(k)
            for k in ("image_path", "image_position", "image_width_pct")
            if existing.get(k) is not None
        }
        self._table_def = existing.get("table_def")

        if sub_part:
            part = (existing.get("sub_parts") or {}).get(sub_part, {})
            self.text_edit.setPlainText(part.get("text", ""))
            self.marks_spin.setValue(
                float(part.get("marks", 0))
            )
        else:
            self.text_edit.setPlainText(existing.get("text", ""))
            self.marks_spin.setValue(
                float(existing.get("marks", section.get("marks_per_question", 0)))
            )

        opts = existing.get("options") or []
        for i, edit in enumerate(self.option_edits):
            edit.setText(opts[i] if i < len(opts) else "")
        answer = existing.get("answer", "")
        self.model_answer.setPlainText(answer if not is_mcq else "")
        if answer and answer in opts:
            self.answer_combo.setCurrentIndex(opts.index(answer) + 1)
        else:
            self.answer_combo.setCurrentIndex(0)

        self._refresh_attach_status()
        self.dirty = False
        self._loading = False

    def _mark_dirty(self, *_args) -> None:
        if not self._loading:
            self.dirty = True

    def _insert_notation(self, mapping: dict, fallback: str) -> None:
        cursor = self.text_edit.textCursor()
        selected = cursor.selectedText()
        cursor.insertText(selected.translate(mapping) if selected else fallback)
        self.text_edit.setFocus()

    # -- attachments ------------------------------------------------------
    def _attach_image(self) -> None:
        dlg = ImagePicker(self, current=self._image_def)
        if dlg.exec():
            self._image_def = dlg.result_def()
            self._refresh_attach_status()
            self._mark_dirty()

    def _add_table(self) -> None:
        dlg = TableDialog(self, table_def=self._table_def)
        if dlg.exec():
            self._table_def = dlg.table_def()
            self._refresh_attach_status()
            self._mark_dirty()

    def _refresh_attach_status(self) -> None:
        bits = []
        if self._image_def.get("image_path"):
            bits.append("🖼  image attached")
        if self._table_def:
            td = self._table_def
            bits.append(f"▦  table {td['rows']}×{td['cols']}")
        self.attach_status.setText("   ".join(bits))

    # -- saving -----------------------------------------------------------
    def save(self) -> None:
        if not self.section_id:
            return
        qtype = self.section.get("question_type", "short_answer")
        text = self.text_edit.toPlainText().strip()
        marks = self.marks_spin.value()

        if self.sub_part:
            existing = self.state.get_question(self.section_id, self.question_num) or {}
            sub_parts = dict(existing.get("sub_parts") or {})
            if text:
                sub_parts[self.sub_part] = {"text": text, "marks": marks}
            else:
                sub_parts.pop(self.sub_part, None)
            data = {
                "type": qtype,
                "sub_parts": sub_parts,
                "marks": existing.get("marks", self.section.get("marks_per_question", 0)),
                **self._image_def,
                "table_def": self._table_def,
            }
            # Preserve the main question fields if already present.
            if "text" in existing:
                data["text"] = existing["text"]
            if not (data.get("text") or sub_parts or data.get("image_path") or data.get("table_def")):
                self.state.delete_question(self.section_id, self.question_num)
            else:
                self.state.update_question(self.section_id, self.question_num, data)
        else:
            options = [e.text().strip() for e in self.option_edits]
            answer = ""
            if qtype == "MCQ":
                idx = self.answer_combo.currentIndex() - 1
                if 0 <= idx < len(options):
                    answer = options[idx]
            else:
                answer = self.model_answer.toPlainText().strip()
            data = {
                "text": text,
                "type": qtype,
                "options": options if qtype == "MCQ" else [],
                "answer": answer,
                "marks": marks,
                **self._image_def,
                "table_def": self._table_def,
            }
            existing = self.state.get_question(self.section_id, self.question_num) or {}
            if not (text or any(options) or self._image_def.get("image_path") or self._table_def or existing.get("sub_parts")):
                self.state.delete_question(self.section_id, self.question_num)
            else:
                self.state.update_question(self.section_id, self.question_num, data)

        self.dirty = False
        self.question_saved.emit(self.section_id, self.question_num)

    def _clear_question(self) -> None:
        if self.state.get_question(self.section_id, self.question_num) or self.dirty:
            answer = QMessageBox.question(
                self, "Clear question", "Remove this question and all its parts?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.state.delete_question(self.section_id, self.question_num)
        self._image_def = {}
        self._table_def = None
        self.load(self.section, self.question_num, self.sub_part)
        self.question_saved.emit(self.section_id, self.question_num)
