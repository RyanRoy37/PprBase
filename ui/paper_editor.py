"""Screen 2: the main question-entry workspace.

Two panes: the question form on the left, the live preview tree on the right.
Section tabs across the top, with a question-number stepper and an optional
sub-part selector below them.
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from core.state_manager import PaperState
from ui.preview_panel import PreviewPanel
from ui.question_form import QuestionForm


class PaperEditor(QWidget):
    state_changed = pyqtSignal()

    def __init__(self, fmt: dict[str, Any], state: PaperState, parent=None) -> None:
        super().__init__(parent)
        self.fmt = fmt
        self.state = state
        self.sections = fmt.get("sections", [])
        self._current_section_index = 0

        self._build_ui()
        if self.sections:
            self._load_section(0)

    # -- ui ---------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Section tabs.
        self.tab_bar = QTabBar()
        self.tab_bar.setExpanding(False)
        for section in self.sections:
            self.tab_bar.addTab(section.get("title", section.get("id", "")))
        self.tab_bar.currentChanged.connect(self._load_section)
        layout.addWidget(self.tab_bar)

        # Navigation row: question stepper + sub-part selector.
        nav = QHBoxLayout()
        nav.addWidget(QLabel("Question"))
        self.q_spin = QSpinBox()
        self.q_spin.setMinimum(1)
        self.q_spin.valueChanged.connect(self._on_question_changed)
        nav.addWidget(self.q_spin)
        self.printed_label = QLabel("")
        nav.addWidget(self.printed_label)

        self.prev_btn = QPushButton("‹ Prev")
        self.prev_btn.setObjectName("Ghost")
        self.prev_btn.clicked.connect(lambda: self.q_spin.setValue(self.q_spin.value() - 1))
        self.next_btn = QPushButton("Next ›")
        self.next_btn.setObjectName("Ghost")
        self.next_btn.clicked.connect(lambda: self.q_spin.setValue(self.q_spin.value() + 1))
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.next_btn)

        self.subpart_label = QLabel("Sub-part")
        self.subpart_combo = QComboBox()
        self.subpart_combo.currentIndexChanged.connect(self._on_subpart_changed)
        nav.addWidget(self.subpart_label)
        nav.addWidget(self.subpart_combo)
        nav.addStretch()
        layout.addLayout(nav)

        # Split: form | preview.
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.form = QuestionForm(self.state)
        self.form.question_saved.connect(self._on_saved)
        self.preview = PreviewPanel(self.fmt, self.state)
        self.preview.question_selected.connect(self._jump_to)
        splitter.addWidget(self.form)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

    # -- section / question navigation -----------------------------------
    def _current_section(self) -> dict[str, Any]:
        return self.sections[self._current_section_index]

    def _load_section(self, index: int) -> None:
        if index < 0 or index >= len(self.sections):
            return
        self.save_current()
        self._current_section_index = index
        section = self.sections[index]
        total = int(section.get("total_questions", 1))
        self.q_spin.blockSignals(True)
        self.q_spin.setMaximum(max(1, total))
        self.q_spin.setValue(1)
        self.q_spin.blockSignals(False)
        self._populate_subparts(section)
        self._reload_form()

    def _populate_subparts(self, section: dict[str, Any]) -> None:
        sub_parts = section.get("sub_parts")
        self.subpart_combo.blockSignals(True)
        self.subpart_combo.clear()
        has_parts = bool(sub_parts)
        if has_parts:
            self.subpart_combo.addItem("Main question", None)
            for label in sub_parts:
                self.subpart_combo.addItem(f"Part ({label})", label)
        self.subpart_combo.blockSignals(False)
        self.subpart_label.setVisible(has_parts)
        self.subpart_combo.setVisible(has_parts)

    def _current_subpart(self) -> Optional[str]:
        if not self.subpart_combo.isVisible():
            return None
        return self.subpart_combo.currentData()

    def _reload_form(self) -> None:
        section = self._current_section()
        self.form.load(section, self.q_spin.value(), self._current_subpart())
        start = section.get("start_number", 1)
        self.printed_label.setText(f"Printed as Q{start + self.q_spin.value() - 1}" if start != 1 else "")
        total = int(section.get("total_questions", 1))
        self.prev_btn.setEnabled(self.q_spin.value() > 1)
        self.next_btn.setEnabled(self.q_spin.value() < total)

    def _on_question_changed(self, _value: int) -> None:
        self.save_current()
        self._reload_form()

    def _on_subpart_changed(self, _index: int) -> None:
        self.save_current()
        self._reload_form()

    def _on_saved(self, _sid: str, _qnum: int) -> None:
        self.preview.refresh()
        self.state_changed.emit()

    def _jump_to(self, sid: str, qnum: int) -> None:
        for i, section in enumerate(self.sections):
            if section.get("id") == sid:
                if i != self._current_section_index:
                    self.tab_bar.setCurrentIndex(i)
                self.q_spin.setValue(qnum)
                break

    def save_current(self) -> None:
        """Persist whatever is on screen (used before export)."""
        if self.form.dirty:
            self.form.save()
