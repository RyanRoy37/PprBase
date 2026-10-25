"""Loading and validation of question-paper format JSON files.

A "format" describes the skeleton of a paper: header info, instructions and a
list of sections. Formats live as plain JSON files in the ``formats/`` folder so
that non-technical users can extend the app just by adding a file.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

VALID_QUESTION_TYPES = {"MCQ", "short_answer", "long_answer"}

REQUIRED_FORMAT_FIELDS = (
    "format_id",
    "display_name",
    "subject",
    "class",
    "sections",
)

REQUIRED_SECTION_FIELDS = (
    "id",
    "title",
    "question_type",
    "marks_per_question",
    "total_questions",
)


class FormatError(Exception):
    """Raised when a format JSON file is missing or malformed.

    The message is written in plain English so it can be shown directly to the
    user in a dialog.
    """


def load_format(path: str) -> dict[str, Any]:
    """Parse and validate a single format JSON file.

    Returns the format as a dict. Raises :class:`FormatError` with a friendly
    message if the file cannot be read, is not valid JSON, or fails validation.
    """
    if not os.path.isfile(path):
        raise FormatError(f"Couldn't find a format file at:\n{path}")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise FormatError(
            f"That format file isn't valid JSON.\n\n{os.path.basename(path)} "
            f"— line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise FormatError(f"Couldn't open the format file:\n{exc}") from exc

    validate_format(data, source=os.path.basename(path))
    template = data.get("docx_template")
    if template and not os.path.isabs(template):
        data["docx_template"] = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(path)), template))
    return data


def validate_format(data: Any, source: str = "format") -> None:
    """Validate an already-parsed format dict.

    Raises :class:`FormatError` describing the first problem found.
    """
    if not isinstance(data, dict):
        raise FormatError(f"{source}: the top level should be a JSON object.")

    missing = [f for f in REQUIRED_FORMAT_FIELDS if f not in data]
    if missing:
        raise FormatError(
            f"{source} is missing required field(s): {', '.join(missing)}."
        )

    for field in ("format_id", "display_name", "subject", "class"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise FormatError(f"{source}: '{field}' must be a non-empty text value.")
    for field in ("school_name", "paper_title", "duration"):
        if field in data and not isinstance(data[field], str):
            raise FormatError(f"{source}: '{field}' must be text.")
    template = data.get("docx_template")
    if template is not None and (not isinstance(template, str) or not template.strip()):
        raise FormatError(f"{source}: 'docx_template' must be a file path or null.")
    body_start = data.get("template_body_start")
    if body_start is not None and (isinstance(body_start, bool) or not isinstance(body_start, int) or body_start < 0):
        raise FormatError(f"{source}: 'template_body_start' must be a whole number of 0 or more.")
    if not data["format_id"].replace("_", "").replace("-", "").isalnum():
        raise FormatError(f"{source}: 'format_id' may use letters, numbers, dashes and underscores only.")
    if "total_marks" in data and (
        isinstance(data["total_marks"], bool)
        or not isinstance(data["total_marks"], (int, float))
        or not math.isfinite(data["total_marks"])
        or data["total_marks"] < 0
    ):
        raise FormatError(f"{source}: 'total_marks' must be a number of 0 or more.")
    if "instructions" in data and (
        not isinstance(data["instructions"], list)
        or not all(isinstance(line, str) for line in data["instructions"])
    ):
        raise FormatError(f"{source}: 'instructions' must be a list of text lines.")

    sections = data.get("sections")
    if not isinstance(sections, list) or not sections:
        raise FormatError(f"{source}: 'sections' must be a non-empty list.")

    seen_ids: set[str] = set()
    for idx, section in enumerate(sections, start=1):
        _validate_section(section, idx, source, seen_ids)


def calculated_total_marks(data: dict[str, Any]) -> float:
    """Maximum score, counting only required answers in choice sections."""
    return sum(
        section.get("attempt_count", section["total_questions"]) * section["marks_per_question"]
        for section in data.get("sections", [])
    )


def section_instruction(section: dict[str, Any]) -> str:
    """Human-readable section instruction, including any answer choice."""
    description = section.get("description", "").strip()
    printed = section.get("total_questions", 0)
    required = section.get("attempt_count", printed)
    if required < printed and "answer any" not in description.lower():
        choice = f"Answer any {required} of the {printed} questions."
        return f"{description} {choice}".strip()
    return description


def _validate_section(
    section: Any, idx: int, source: str, seen_ids: set[str]
) -> None:
    where = f"{source}: section #{idx}"
    if not isinstance(section, dict):
        raise FormatError(f"{where} should be a JSON object.")

    missing = [f for f in REQUIRED_SECTION_FIELDS if f not in section]
    if missing:
        raise FormatError(f"{where} is missing field(s): {', '.join(missing)}.")

    sid = section["id"]
    if not isinstance(sid, str) or not sid.strip():
        raise FormatError(f"{where}: 'id' must be a non-empty string.")
    if sid in seen_ids:
        raise FormatError(f"{source}: section id '{sid}' is used more than once.")
    seen_ids.add(sid)

    if not isinstance(section["title"], str) or not section["title"].strip():
        raise FormatError(f"{where}: 'title' must be a non-empty heading.")
    if "description" in section and not isinstance(section["description"], str):
        raise FormatError(f"{where}: 'description' must be text.")

    qtype = section["question_type"]
    if not isinstance(qtype, str) or qtype not in VALID_QUESTION_TYPES:
        raise FormatError(
            f"{where}: question_type '{qtype}' is not valid. "
            f"Use one of: {', '.join(sorted(VALID_QUESTION_TYPES))}."
        )

    total = section["total_questions"]
    if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
        raise FormatError(
            f"{where}: 'total_questions' must be a whole number greater than 0."
        )

    attempt_count = section.get("attempt_count", total)
    if isinstance(attempt_count, bool) or not isinstance(attempt_count, int) or not 1 <= attempt_count <= total:
        raise FormatError(
            f"{where}: 'attempt_count' must be between 1 and the number of printed questions."
        )
    start_number = section.get("start_number", 1)
    if isinstance(start_number, bool) or not isinstance(start_number, int) or start_number < 1:
        raise FormatError(f"{where}: 'start_number' must be a whole number greater than 0.")

    marks = section["marks_per_question"]
    if isinstance(marks, bool) or not isinstance(marks, (int, float)) or not math.isfinite(marks) or marks < 0:
        raise FormatError(f"{where}: 'marks_per_question' must be 0 or more.")

    sub_parts = section.get("sub_parts")
    if sub_parts is not None and (
        not isinstance(sub_parts, list)
        or not all(isinstance(p, str) and p.strip() for p in sub_parts)
        or len(sub_parts) != len(set(sub_parts))
    ):
        raise FormatError(
            f"{where}: 'sub_parts' must be null or a list of labels like "
            f'["i", "ii", "iii"].'
        )


def list_available_formats(formats_dir: str) -> list[dict[str, Any]]:
    """Scan ``formats_dir`` and return one summary per valid format file.

    Each entry has: ``path``, ``format_id``, ``display_name``, ``subject``,
    ``class`` and ``valid`` (bool). Invalid files are still returned with
    ``valid=False`` and an ``error`` message so the UI can flag them rather than
    silently hide them.
    """
    results: list[dict[str, Any]] = []
    if not os.path.isdir(formats_dir):
        return results

    for name in sorted(os.listdir(formats_dir)):
        if not name.lower().endswith(".json"):
            continue
        path = os.path.join(formats_dir, name)
        try:
            data = load_format(path)
        except FormatError as exc:
            results.append(
                {
                    "path": path,
                    "display_name": name,
                    "valid": False,
                    "error": str(exc),
                }
            )
            continue
        results.append(
            {
                "path": path,
                "format_id": data.get("format_id", name),
                "display_name": data.get("display_name", name),
                "subject": data.get("subject", ""),
                "class": data.get("class", ""),
                "word_template": bool(data.get("docx_template")),
                "valid": True,
            }
        )
    return results
