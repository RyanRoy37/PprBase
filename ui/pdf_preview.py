"""Scrollable, page accurate preview of the PDF the teacher can save."""

from __future__ import annotations

from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class PdfPreviewDialog(QDialog):
    def __init__(self, path: str, parent=None, word_template: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paper preview — PprBase")
        self.resize(850, 760)
        self.document = QPdfDocument(self)
        if self.document.load(path) != QPdfDocument.Error.None_:
            raise OSError("The preview PDF could not be opened.")

        root = QVBoxLayout(self)
        note = (
            "This preview uses PprBase's PDF layout. Open the exported Word file to check the uploaded template's layout."
            if word_template else
            "This is the printable PDF layout. Word may paginate slightly differently."
        )
        label = QLabel(note)
        label.setWordWrap(True)
        root.addWidget(label)
        self.view = QPdfView(self)
        self.view.setDocument(self.document)
        self.view.setPageMode(QPdfView.PageMode.MultiPage)
        self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        root.addWidget(self.view, 1)

        actions = QHBoxLayout()
        self.page_label = QLabel(f"{self.document.pageCount()} page(s)")
        actions.addWidget(self.page_label)
        actions.addStretch()
        self.save_button = QPushButton("Save PDF…")
        actions.addWidget(self.save_button)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        actions.addWidget(close_button)
        root.addLayout(actions)
