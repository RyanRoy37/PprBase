"""Dialog to attach an image to a question, with preview and sizing options."""

from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from core import image_handler

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)"


class ImagePicker(QDialog):
    """Pick an image file, preview it, and choose width + position."""

    def __init__(self, parent=None, current: Optional[dict] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Attach an image")
        self.setMinimumWidth(420)
        self._path: Optional[str] = (current or {}).get("image_path")

        self.preview = QLabel("No image selected")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedHeight(200)
        self.preview.setStyleSheet(
            "border: 1px dashed #C9C2B8; border-radius: 8px; color: #8A8580;"
        )

        choose = QPushButton("Choose image…")
        choose.setObjectName("Ghost")
        choose.clicked.connect(self._choose_file)

        self.position = QComboBox()
        self.position.addItem("Below the question", "below")
        self.position.addItem("Alongside the question", "alongside")
        self.position.addItem("Before the answer parts", "before_parts")
        pos = (current or {}).get("image_position", "below")
        self.position.setCurrentIndex(max(0, self.position.findData(pos)))

        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(10, 100)
        self.width_slider.setValue((current or {}).get("image_width_pct", 100))
        self.width_label = QLabel()
        self.width_slider.valueChanged.connect(
            lambda v: self.width_label.setText(f"{v}% of max width")
        )
        self.width_label.setText(f"{self.width_slider.value()}% of max width")
        width_row = QHBoxLayout()
        width_row.addWidget(self.width_slider)
        width_row.addWidget(self.width_label)

        form = QFormLayout()
        form.addRow("Position", self.position)
        form.addRow("Width", width_row)

        self.clear_btn = QPushButton("Remove image")
        self.clear_btn.setObjectName("Danger")
        self.clear_btn.clicked.connect(self._clear)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.preview)
        top = QHBoxLayout()
        top.addWidget(choose)
        top.addWidget(self.clear_btn)
        top.addStretch()
        layout.addLayout(top)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if self._path and os.path.isfile(self._path):
            self._show_preview(self._path)

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose an image", "", IMAGE_FILTER
        )
        if not path:
            return
        thumb = image_handler.make_thumbnail(path)
        if thumb is None:
            self.preview.setText("Couldn't read that image — is it a JPEG, PNG or WEBP?")
            self._path = None
            return
        self._path = path
        self._show_preview(path, thumb)

    def _show_preview(self, path: str, thumb: Optional[bytes] = None) -> None:
        if thumb is None:
            thumb = image_handler.make_thumbnail(path)
        if thumb is None:
            return
        pix = QPixmap()
        pix.loadFromData(thumb)
        self.preview.setPixmap(pix)

    def _clear(self) -> None:
        self._path = None
        self.preview.setPixmap(QPixmap())
        self.preview.setText("No image selected")

    def result_def(self) -> dict:
        """Return the image fields to merge into the question."""
        return {
            "image_path": self._path,
            "image_position": self.position.currentData(),
            "image_width_pct": self.width_slider.value(),
        }
