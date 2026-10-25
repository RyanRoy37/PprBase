"""Self-contained A4 PDF generation for the paper preview and printing."""

from __future__ import annotations

from html import escape
import os
from pathlib import Path
import re
import tempfile
from typing import Any
import unicodedata

from PyQt6.QtCore import QMarginsF, QUrl
from PyQt6.QtGui import QImage, QPageLayout, QPageSize, QTextDocument
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPrintSupport import QPrinter

from core.image_handler import DEFAULT_MAX_WIDTH_CM, prepare_image
from core.format_loader import section_instruction
from core.state_manager import PaperState


def _text(value: Any) -> str:
    return escape(str(value or "")).replace("\n", "<br>")


def _marks(value: Any) -> str:
    try:
        number = float(value)
        return str(int(number)) if number.is_integer() else f"{number:g}"
    except (TypeError, ValueError):
        return str(value)


class PdfEngine:
    """Render a paper from the same format and saved question state as Word export."""

    def __init__(self, fmt: dict[str, Any], state: PaperState) -> None:
        self.fmt = fmt
        self.state = state
        self._images: list[tuple[str, QImage]] = []

    def _image(self, question: dict[str, Any]) -> str:
        prepared = prepare_image(question["image_path"], DEFAULT_MAX_WIDTH_CM)
        try:
            image = QImage(prepared.embed_path)
            if image.isNull():
                raise ValueError("Couldn't display an attached image in the PDF.")
            name = f"pprbase-image-{len(self._images)}"
            self._images.append((name, image))
            pct = max(10, min(100, int(question.get("image_width_pct", 100) or 100)))
            width = round(prepared.width_cm * pct / 100 * 96 / 2.54)
            return f'<img src="{name}" width="{width}">'
        finally:
            prepared.cleanup()

    def build_document(
        self, break_before: set[str] | None = None,
        question_breaks: set[tuple[str, int]] | None = None,
    ) -> QTextDocument:
        self._images = []
        parts = ['<html><body style="font-family: DejaVu Sans; font-size: 11pt; color: #111;">']
        school = self.fmt.get("school_name")
        if school:
            parts.append(f'<p align="center" style="font-size:16pt; font-weight:bold; margin:0;">{_text(school)}</p>')
        paper_title = self.fmt.get("paper_title")
        if paper_title:
            parts.append(f'<p align="center" style="font-size:14pt; font-weight:bold; margin:3px 0;">{_text(paper_title)}</p>')
        subject = self.fmt.get("subject")
        klass = self.fmt.get("class")
        heading = "  —  ".join(filter(None, (_text(subject), f"Class {_text(klass)}" if klass else "")))
        if heading:
            parts.append(f'<p align="center" style="font-size:13pt; font-weight:bold; margin:3px 0 12px;">{heading}</p>')
        duration = self.fmt.get("duration")
        maximum = self.fmt.get("total_marks")
        if duration or maximum is not None:
            parts.append('<table width="100%" cellspacing="0" cellpadding="0"><tr>')
            parts.append(f'<td><b>{"Time: " + _text(duration) if duration else ""}</b></td>')
            parts.append(f'<td align="right"><b>{"Maximum Marks: " + _text(maximum) if maximum is not None else ""}</b></td>')
            parts.append('</tr></table>')
        parts.append('<hr>')
        instructions = self.fmt.get("instructions") or []
        if instructions:
            parts.append('<p style="margin:6px 0 2px;"><b><u>General Instructions:</u></b></p><ol style="margin-top:2px;">')
            parts.extend(f'<li>{_text(line)}</li>' for line in instructions)
            parts.append('</ol><hr>')
        for section in self.fmt.get("sections", []):
            sid = section.get("id", "")
            page_break = "page-break-before:always;" if sid in (break_before or set()) else ""
            parts.append(f'<p align="center" style="font-size:13pt; font-weight:bold; border-top:1px solid #888; margin:14px 0 3px; {page_break}">{_text(section.get("title", f"Section {sid}"))}</p>')
            description = section_instruction(section)
            if description:
                parts.append(f'<p align="center" style="font-style:italic; margin:0 0 9px;">{_text(description)}</p>')
            for number in range(1, int(section.get("total_questions", 0)) + 1):
                question = self.state.get_question(sid, number) or {}
                printed_number = section.get("start_number", 1) + number - 1
                body = _text(question.get("text", "").strip()) or "____________________________"
                marks = question.get("marks", section.get("marks_per_question"))
                mark_label = f'[{_text(_marks(marks))}]' if marks not in (None, "") else ""
                if question.get("image_path") and question.get("image_position") == "alongside":
                    body += " &nbsp; " + self._image(question)
                question_break = "page-break-before:always;" if (sid, number) in (question_breaks or set()) else ""
                parts.append(f'<table width="100%" cellspacing="0" cellpadding="0" style="margin-top:7px; {question_break}"><tr>')
                parts.append(f'<td valign="top"><b>{printed_number}.</b> {body}</td>')
                parts.append(f'<td width="55" align="right" valign="top">{mark_label}</td></tr></table>')
                if question.get("image_path") and question.get("image_position") == "before_parts":
                    parts.append(f'<p align="center" style="margin:5px 0;">{self._image(question)}</p>')
                if section.get("question_type") == "MCQ":
                    for index, option in enumerate(question.get("options") or []):
                        if str(option).strip():
                            label = chr(ord("a") + index) if index < 8 else str(index + 1)
                            parts.append(f'<p style="margin:1px 0 1px 28px;"><b>({label})</b> {_text(option)}</p>')
                for label, part in (question.get("sub_parts") or {}).items():
                    part_text = _text(part.get("text")) or "____________________"
                    part_marks = part.get("marks")
                    suffix = f' [{_text(_marks(part_marks))}]' if part_marks else ""
                    parts.append(f'<p style="margin:2px 0 2px 28px;"><b>({_text(label)})</b> {part_text}{suffix}</p>')
                if question.get("image_path") and question.get("image_position") == "below":
                    parts.append(f'<p align="center" style="margin:5px 0;">{self._image(question)}</p>')
                if question.get("table_def"):
                    definition = question["table_def"]
                    rows = max(1, int(definition.get("rows", 1)))
                    cols = max(1, int(definition.get("cols", 1)))
                    headers = definition.get("headers") or []
                    parts.append('<table width="95%" border="1" cellspacing="0" cellpadding="5" style="margin:6px 0 10px 20px; border-color:#777;">')
                    for row in range(rows):
                        parts.append("<tr>")
                        for col in range(cols):
                            cell = _text(headers[col]) if row == 0 and col < len(headers) else "&nbsp;"
                            parts.append(f"<td>{cell}</td>")
                        parts.append("</tr>")
                    parts.append("</table>")
        parts.append("</body></html>")
        document = QTextDocument()
        document.setHtml("".join(parts))
        for name, image in self._images:
            document.addResource(QTextDocument.ResourceType.ImageResource, QUrl(name), image)
        return document

    @staticmethod
    def _flat(value: str) -> str:
        return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()

    def _orphaned_sections(self, path: Path) -> set[str]:
        """Find headings whose first question runs onto the following page."""
        pages = self._page_text(path)
        breaks = set()
        for section in self.fmt.get("sections", [])[1:]:
            title = self._flat(section.get("title", f"Section {section.get('id', '')}"))
            first = self.state.get_question(section.get("id", ""), 1) or {}
            words = self._flat(first.get("text", "")).split()
            if not words:
                continue
            page = next((text for text in pages if title in text), None)
            if page is None:
                continue
            start = " ".join(words[: min(5, len(words))])
            end = " ".join(words[-min(5, len(words)):])
            first_part = next(iter((first.get("sub_parts") or {}).values()), None)
            part_words = self._flat(first_part.get("text", "")).split() if first_part else []
            part_start = " ".join(part_words[: min(5, len(part_words))])
            if start not in page or end not in page or (part_start and part_start not in page):
                breaks.add(section.get("id", ""))
        return breaks

    def _page_text(self, path: Path) -> list[str]:
        pdf = QPdfDocument(None)
        if pdf.load(str(path)) != QPdfDocument.Error.None_:
            raise OSError("The saved PDF could not be checked.")
        try:
            return [self._flat(pdf.getAllText(index).text()) for index in range(pdf.pageCount())]
        finally:
            pdf.close()

    def _orphaned_questions(self, path: Path) -> set[tuple[str, int]]:
        """Find a grouped question whose first part starts on the next page."""
        pages = self._page_text(path)
        breaks = set()
        for section in self.fmt.get("sections", []):
            sid = section["id"]
            for number in range(1, section["total_questions"] + 1):
                question = self.state.get_question(sid, number) or {}
                first_part = next(iter((question.get("sub_parts") or {}).values()), None)
                if not first_part:
                    continue
                stem_words = self._flat(question.get("text", "")).split()
                part_words = self._flat(first_part.get("text", "")).split()
                if not stem_words or not part_words:
                    continue
                printed = section.get("start_number", 1) + number - 1
                marker = f" {printed}. {' '.join(stem_words[:min(5, len(stem_words))])}"
                page = next((text for text in pages if marker in f" {text}"), None)
                if page and " ".join(part_words[:min(5, len(part_words))]) not in page:
                    breaks.add((sid, number))
        return breaks

    def _print(self, path: Path, break_before: set[str], question_breaks: set[tuple[str, int]]) -> None:
        document = self.build_document(break_before, question_breaks)
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageMargins(QMarginsF(20, 20, 20, 20), QPageLayout.Unit.Millimeter)
        printer.setOutputFileName(str(path))
        document.print(printer)

    def save(self, output_path: str) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(prefix="pprbase_", suffix=".pdf", dir=path.parent, delete=False)
        temporary = Path(handle.name)
        handle.close()
        try:
            self._print(temporary, set(), set())
            breaks = self._orphaned_sections(temporary)
            if breaks:
                self._print(temporary, breaks, set())
            question_breaks = self._orphaned_questions(temporary)
            if question_breaks:
                self._print(temporary, breaks, question_breaks)
            if temporary.stat().st_size == 0:
                raise OSError("The PDF could not be saved.")
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return str(path)
