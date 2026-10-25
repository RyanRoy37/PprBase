"""Root window: top nav, view stack, and the export flow."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import Any, Optional

from PyQt6.QtCore import QSettings, QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.document_engine import DocumentEngine
from core.draft_store import DraftError, DraftStore
from core.format_loader import load_format
from core.pdf_engine import PdfEngine
from core.state_manager import PaperState
from ui.format_selector import FormatSelector
from ui.paper_editor import PaperEditor
from ui.pdf_preview import PdfPreviewDialog
from ui import styles


class MainWindow(QMainWindow):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        paths = config.get("paths", {})
        self.formats_dir = paths.get("formats_dir", "formats")
        self.output_dir = paths.get("output_dir", "output")
        self.drafts = DraftStore(paths.get("drafts_dir", "drafts"))
        self.draft_id: Optional[str] = None

        self.fmt: Optional[dict[str, Any]] = None
        self.state: Optional[PaperState] = None
        self.editor: Optional[PaperEditor] = None

        self.setWindowTitle("PprBase")
        self.resize(1180, 760)
        self._build_ui()
        self.auto_save = QTimer(self)
        self.auto_save.setInterval(max(1, int(config.get("editor", {}).get("auto_save_minutes", 2))) * 60_000)
        self.auto_save.timeout.connect(self._auto_save)
        self.auto_save.start()

    # -- ui ---------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_nav())

        self.stack = QStackedWidget()
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 14, 18, 14)
        body_layout.addWidget(self.stack)
        root.addWidget(body, 1)

        # View 0: format selector.
        self.selector = FormatSelector(self.formats_dir)
        self.selector.format_chosen.connect(self._open_format)
        self.selector.draft_chosen.connect(self._resume_draft)
        self.selector.set_drafts(self.drafts.list_drafts())
        self.stack.addWidget(self.selector)

        self.setCentralWidget(central)

    def _build_nav(self) -> QFrame:
        nav = QFrame()
        nav.setObjectName("NavBar")
        nav.setFixedHeight(58)
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(18, 8, 18, 8)

        title = QLabel("PprBase")
        title.setObjectName("AppTitle")
        layout.addWidget(title)

        self.crumb = QLabel("Choose a format")
        self.crumb.setObjectName("Crumb")
        layout.addWidget(self.crumb)
        layout.addStretch()

        smaller = QPushButton("A−")
        smaller.setObjectName("Ghost")
        smaller.setToolTip("Make text smaller")
        smaller.clicked.connect(lambda: self._change_font(-1))
        layout.addWidget(smaller)
        larger = QPushButton("A+")
        larger.setObjectName("Ghost")
        larger.setToolTip("Make text larger")
        larger.clicked.connect(lambda: self._change_font(1))
        layout.addWidget(larger)

        self.home_btn = QPushButton("Formats")
        self.home_btn.setObjectName("Ghost")
        self.home_btn.clicked.connect(self._go_home)
        self.home_btn.setVisible(False)
        layout.addWidget(self.home_btn)

        self.draft_btn = QPushButton("Save Draft")
        self.draft_btn.setObjectName("Ghost")
        self.draft_btn.clicked.connect(self._save_draft)
        self.draft_btn.setVisible(False)
        layout.addWidget(self.draft_btn)

        self.preview_btn = QPushButton("Preview / PDF")
        self.preview_btn.setObjectName("Ghost")
        self.preview_btn.clicked.connect(self._quick_preview)
        self.preview_btn.setVisible(False)
        layout.addWidget(self.preview_btn)

        self.key_btn = QPushButton("Answer Key")
        self.key_btn.setObjectName("Ghost")
        self.key_btn.clicked.connect(self._export_answer_key)
        self.key_btn.setVisible(False)
        layout.addWidget(self.key_btn)

        self.export_btn = QPushButton("Generate Paper")
        self.export_btn.clicked.connect(self._export)
        self.export_btn.setVisible(False)
        layout.addWidget(self.export_btn)

        return nav

    def _change_font(self, amount: int) -> None:
        editor_settings = self.config.setdefault("editor", {})
        size = max(9, min(20, int(editor_settings.get("font_size", 11)) + amount))
        editor_settings["font_size"] = size
        QApplication.instance().setStyleSheet(styles.app_stylesheet(size))
        QSettings("PprBase", "PprBase").setValue("font_size", size)

    # -- navigation -------------------------------------------------------
    def _open_format(self, fmt: dict[str, Any], path: str) -> None:
        self.draft_id = None
        self._show_editor(fmt, PaperState(fmt.get("format_id")))

    def _show_editor(self, fmt: dict[str, Any], state: PaperState) -> None:
        self.fmt = fmt
        self.state = state
        self.editor = PaperEditor(fmt, self.state)
        self.editor.state_changed.connect(self._schedule_save)
        # Replace any previous editor in the stack.
        if self.stack.count() > 1:
            old = self.stack.widget(1)
            self.stack.removeWidget(old)
            old.deleteLater()
        self.stack.addWidget(self.editor)
        self.stack.setCurrentWidget(self.editor)
        self.crumb.setText(f"  ›  {fmt.get('display_name','')}")
        self.home_btn.setVisible(True)
        self.draft_btn.setVisible(True)
        self.preview_btn.setVisible(True)
        self.key_btn.setVisible(True)
        self.export_btn.setVisible(True)

    def _resume_draft(self, draft_id: str) -> None:
        try:
            fmt, state = self.drafts.load(draft_id)
        except DraftError as exc:
            QMessageBox.warning(self, "Couldn't open draft", str(exc))
            self.selector.set_drafts(self.drafts.list_drafts())
            return
        self.draft_id = draft_id
        self._show_editor(fmt, state)

    def _schedule_save(self) -> None:
        QTimer.singleShot(1500, self._auto_save)

    def _auto_save(self) -> None:
        if self.stack.currentWidget() == self.editor and self.state:
            self._save_draft(silent=True)

    def _save_draft(self, silent: bool = False) -> bool:
        if not self.fmt or not self.state:
            return True
        if self.editor:
            self.editor.save_current()
        if not self.state.get_all():
            if not silent:
                self.statusBar().showMessage("Add a question before saving a draft.", 4000)
            return True
        try:
            self.draft_id = self.drafts.save(self.fmt, self.state, self.draft_id)
        except (DraftError, OSError) as exc:
            if not silent:
                QMessageBox.warning(self, "Couldn't save draft", str(exc))
            else:
                self.statusBar().showMessage("Draft could not be saved. Use Save Draft to see the error.", 8000)
            return False
        if not silent:
            self.statusBar().showMessage("Draft saved. You can reopen it from Formats.", 5000)
        return True

    def _go_home(self) -> None:
        if not self._save_draft():
            return
        self.stack.setCurrentWidget(self.selector)
        self.selector.reload()
        self.selector.set_drafts(self.drafts.list_drafts())
        self.crumb.setText("Choose a format")
        self.home_btn.setVisible(False)
        self.draft_btn.setVisible(False)
        self.preview_btn.setVisible(False)
        self.key_btn.setVisible(False)
        self.export_btn.setVisible(False)

    def closeEvent(self, event) -> None:
        if self.editor and self.state and not self._save_draft(silent=True):
            answer = QMessageBox.question(
                self, "Draft not saved", "Your latest changes could not be saved. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()

    # -- export flow ------------------------------------------------------
    def _confirm_incomplete(self) -> bool:
        if not self.fmt or not self.state:
            return False
        total = sum(section["total_questions"] for section in self.fmt["sections"])
        filled = sum(self.state.count_filled(section["id"]) for section in self.fmt["sections"])
        allocated = self.state.allocated_marks(self.fmt)
        maximum = self.fmt.get("total_marks")
        issues = []
        if filled < total:
            issues.append(f"{total - filled} question(s) are empty and will show blank lines.")
        if maximum is not None and allocated != maximum:
            issues.append(f"Entered questions add up to {allocated:g} marks; the paper says {maximum:g}.")
        for section in self.fmt["sections"]:
            if section.get("attempt_count", section["total_questions"]) >= section["total_questions"]:
                continue
            expected = section["marks_per_question"]
            if any(
                self.state.is_filled(section["id"], number)
                and self.state.get_question(section["id"], number)["marks"] != expected
                for number in range(1, section["total_questions"] + 1)
            ):
                issues.append(f"Each question in {section['title']} should be worth {expected:g} marks because students choose which to answer.")
        if not issues:
            return True
        answer = QMessageBox.question(
            self, "Check your paper", "\n".join(issues) + "\n\nGenerate it anyway?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _quick_preview(self) -> None:
        if not self.fmt or not self.state:
            return
        if self.editor:
            self.editor.save_current()
        try:
            with tempfile.TemporaryDirectory(prefix="pprbase_preview_") as folder:
                path = os.path.join(folder, "Paper Preview.pdf")
                PdfEngine(self.fmt, self.state).save(path)
                dialog = PdfPreviewDialog(path, self, word_template=bool(self.fmt.get("docx_template")))
                dialog.save_button.clicked.connect(self._save_pdf)
                dialog.exec()
                dialog.document.close()
        except Exception as exc:
            QMessageBox.warning(self, "Couldn't preview paper", str(exc))

    def _save_pdf(self) -> None:
        if not self.fmt or not self.state:
            return
        if self.editor:
            self.editor.save_current()
        if not self._confirm_incomplete():
            return
        os.makedirs(self.output_dir, exist_ok=True)
        suggested = os.path.join(self.output_dir, f"{self.fmt.get('format_id', 'paper')}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Save printable PDF", suggested, "PDF files (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            PdfEngine(self.fmt, self.state).save(path)
        except Exception as exc:
            QMessageBox.warning(self, "Couldn't save PDF", str(exc))
            return
        self._show_success(path)

    def _export_answer_key(self) -> None:
        if not self.fmt or not self.state:
            return
        if self.editor:
            self.editor.save_current()
        os.makedirs(self.output_dir, exist_ok=True)
        suggested = os.path.join(self.output_dir, f"{self.fmt['format_id']}_answer_key.docx")
        path, _ = QFileDialog.getSaveFileName(self, "Save answer key", suggested, "Word documents (*.docx)")
        if not path:
            return
        if not path.lower().endswith(".docx"):
            path += ".docx"
        try:
            DocumentEngine(self.fmt, self.state).build_answer_key().save(path)
        except Exception as exc:
            QMessageBox.warning(self, "Couldn't save answer key", str(exc))
            return
        self._show_success(path)

    def _export(self) -> None:
        if not self.fmt or not self.state:
            return
        # Persist whatever's currently on screen first.
        if self.editor:
            self.editor.save_current()
        if not self._confirm_incomplete():
            return

        os.makedirs(self.output_dir, exist_ok=True)
        suggested = os.path.join(
            self.output_dir, f"{self.fmt.get('format_id','paper')}.docx"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Save question paper", suggested, "Word documents (*.docx)"
        )
        if not path:
            return
        if not path.lower().endswith(".docx"):
            path += ".docx"

        try:
            engine = DocumentEngine(self.fmt, self.state)
            engine.build_document()
            engine.save(path)
        except Exception as exc:  # noqa: BLE001 — show any failure plainly
            QMessageBox.critical(
                self,
                "Couldn't generate the paper",
                f"Something went wrong while building the document:\n\n{exc}",
            )
            return

        self._show_success(path)

    def _show_success(self, path: str) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Paper ready")
        box.setText("Your question paper was generated successfully.")
        box.setInformativeText(path)
        open_file = box.addButton("Open File", QMessageBox.ButtonRole.AcceptRole)
        open_folder = box.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole)
        box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == open_file:
            self._open_in_os(path)
        elif clicked == open_folder:
            self._open_in_os(os.path.dirname(os.path.abspath(path)))

    def _open_in_os(self, target: str) -> None:
        try:
            if sys.platform.startswith("darwin"):
                subprocess.Popen(["open", target])
            elif os.name == "nt":
                os.startfile(target)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", target])
        except Exception as exc:
            QMessageBox.warning(self, "Couldn't open file", f"The file was saved, but your computer could not open it automatically.\n\n{target}\n\n{exc}")
