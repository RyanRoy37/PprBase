"""Live structural preview of the paper as a clickable tree.

Green = filled, grey = empty, orange = has an image or table. Clicking a leaf
emits ``question_selected(section_id, question_num)`` so the editor can jump to
it.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from core.state_manager import PaperState
from ui import styles

GREEN = QColor(styles.GREEN)
ORANGE = QColor(styles.ORANGE)
GREY = QColor(styles.GREY)


class PreviewPanel(QWidget):
    question_selected = pyqtSignal(str, int)

    def __init__(self, fmt: dict[str, Any], state: PaperState, parent=None) -> None:
        super().__init__(parent)
        self.fmt = fmt
        self.state = state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Paper structure")
        title.setObjectName("FieldLabel")
        layout.addWidget(title)

        self.summary = QLabel("")
        self.summary.setObjectName("Hint")
        layout.addWidget(self.summary)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_click)
        layout.addWidget(self.tree)

        self.refresh()

    def refresh(self) -> None:
        self.tree.clear()
        total = 0
        filled = 0
        for section in self.fmt.get("sections", []):
            sid = section.get("id", "")
            count = int(section.get("total_questions", 0))
            done = self.state.count_filled(sid)
            total += count
            filled += done
            parent = QTreeWidgetItem(self.tree, [f"{section.get('title','')}  ({done}/{count})"])
            parent.setExpanded(True)
            parent.setData(0, Qt.ItemDataRole.UserRole, None)
            for qnum in range(1, count + 1):
                q = self.state.get_question(sid, qnum)
                is_filled = self.state.is_filled(sid, qnum)
                has_extra = bool(q and (q.get("image_path") or q.get("table_def")))
                mark = "✓" if is_filled else "○"
                printed_number = section.get("start_number", 1) + qnum - 1
                child = QTreeWidgetItem(parent, [f"  Q{printed_number}  {mark}"])
                child.setData(0, Qt.ItemDataRole.UserRole, (sid, qnum))
                if has_extra:
                    child.setForeground(0, QBrush(ORANGE))
                elif is_filled:
                    child.setForeground(0, QBrush(GREEN))
                else:
                    child.setForeground(0, QBrush(GREY))
        self.summary.setText(f"{filled} of {total} questions filled")
        allocated = self.state.allocated_marks(self.fmt)
        maximum = self.fmt.get("total_marks")
        if maximum is not None:
            self.summary.setText(
                f"{filled} of {total} questions filled  ·  "
                f"{allocated:g} / {maximum:g} marks assigned"
            )
            self.summary.setStyleSheet("color: #B04A37;" if allocated > maximum else "")

    def _on_click(self, item: QTreeWidgetItem, _column: int) -> None:
        payload = item.data(0, Qt.ItemDataRole.UserRole)
        if payload:
            sid, qnum = payload
            self.question_selected.emit(sid, qnum)
