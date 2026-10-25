"""Dialog for defining a simple table to attach to a question."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class TableDialog(QDialog):
    """Collects rows, cols and optional headers, with a live preview."""

    def __init__(self, parent=None, table_def: Optional[dict] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add a table")
        self.setMinimumWidth(440)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 30)
        self.rows_spin.setValue((table_def or {}).get("rows", 3))
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 12)
        self.cols_spin.setValue((table_def or {}).get("cols", 3))

        self.headers_edit = QLineEdit()
        self.headers_edit.setPlaceholderText("Optional, comma separated: Name, Symbol, Value")
        headers = (table_def or {}).get("headers") or []
        if headers:
            self.headers_edit.setText(", ".join(headers))

        form = QFormLayout()
        form.addRow("Rows", self.rows_spin)
        form.addRow("Columns", self.cols_spin)
        form.addRow("Column headers", self.headers_edit)

        self.preview = QTableWidget()
        self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview.setFixedHeight(180)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(QLabel("Preview"))
        layout.addWidget(self.preview)
        layout.addWidget(buttons)

        self.rows_spin.valueChanged.connect(self._refresh_preview)
        self.cols_spin.valueChanged.connect(self._refresh_preview)
        self.headers_edit.textChanged.connect(self._refresh_preview)
        self._refresh_preview()

    def _parse_headers(self) -> list[str]:
        raw = self.headers_edit.text().strip()
        if not raw:
            return []
        return [h.strip() for h in raw.split(",")]

    def _refresh_preview(self) -> None:
        rows = self.rows_spin.value()
        cols = self.cols_spin.value()
        headers = self._parse_headers()
        self.preview.setColumnCount(cols)
        self.preview.setRowCount(rows)
        if headers:
            labels = [headers[i] if i < len(headers) else "" for i in range(cols)]
            self.preview.setHorizontalHeaderLabels(labels)
        else:
            self.preview.setHorizontalHeaderLabels([""] * cols)
        for r in range(rows):
            for c in range(cols):
                self.preview.setItem(r, c, QTableWidgetItem(""))

    def table_def(self) -> dict:
        return {
            "rows": self.rows_spin.value(),
            "cols": self.cols_spin.value(),
            "headers": self._parse_headers(),
        }
