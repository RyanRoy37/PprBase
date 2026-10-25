"""In-memory model of the paper a teacher is currently composing.

``PaperState`` is the single source of truth for the app. The UI only ever reads
from and writes to it, and the document engine only ever reads from it. It can be
serialised to/from JSON so work-in-progress can be saved and resumed.

State shape::

    {
        section_id: {
            question_num (int): {
                "text": str,
                "type": str,            # MCQ | short_answer | long_answer
                "options": list[str],   # MCQ only
                "answer": str,          # correct option / model answer
                "marks": float,
                "image_path": str | None,
                "image_width_pct": int, # 10..100, % of usable page width
                "image_position": str,  # "below" | "alongside" | "before_parts"
                "table_def": {"rows": int, "cols": int, "headers": list[str]} | None,
                "sub_parts": { label: {"text": str, "marks": float}, ... },
            }
        }
    }
"""

from __future__ import annotations

import json
from typing import Any, Optional


class PaperState:
    """Holds every entered question for the paper being built."""

    def __init__(self, format_id: Optional[str] = None) -> None:
        self.format_id = format_id
        # section_id -> { question_num -> question dict }
        self._sections: dict[str, dict[int, dict[str, Any]]] = {}

    # -- mutation ---------------------------------------------------------
    def add_question(
        self, section_id: str, question_num: int, data: dict[str, Any]
    ) -> None:
        """Create or replace a question. ``add`` and ``update`` are equivalent;
        both store the normalised question under ``(section_id, question_num)``."""
        section = self._sections.setdefault(section_id, {})
        section[int(question_num)] = self._normalise(data)

    def update_question(
        self, section_id: str, question_num: int, data: dict[str, Any]
    ) -> None:
        """Merge ``data`` into an existing question, or create it if absent."""
        section = self._sections.setdefault(section_id, {})
        existing = section.get(int(question_num), {})
        merged = {**existing, **data}
        section[int(question_num)] = self._normalise(merged)

    def delete_question(self, section_id: str, question_num: int) -> None:
        section = self._sections.get(section_id)
        if section:
            section.pop(int(question_num), None)

    # -- access -----------------------------------------------------------
    def get_question(
        self, section_id: str, question_num: int
    ) -> Optional[dict[str, Any]]:
        return self._sections.get(section_id, {}).get(int(question_num))

    def get_section(self, section_id: str) -> dict[int, dict[str, Any]]:
        """Return ``{question_num: question}`` for a section (may be empty)."""
        return self._sections.get(section_id, {})

    def get_all(self) -> dict[str, dict[int, dict[str, Any]]]:
        return self._sections

    def is_filled(self, section_id: str, question_num: int) -> bool:
        """True if the question (or any of its sub-parts) has text."""
        q = self.get_question(section_id, question_num)
        if not q:
            return False
        if q.get("text", "").strip():
            return True
        for part in q.get("sub_parts", {}).values():
            if part.get("text", "").strip():
                return True
        return False

    def count_filled(self, section_id: str) -> int:
        section = self._sections.get(section_id, {})
        return sum(1 for n in section if self.is_filled(section_id, n))

    def allocated_marks(self, fmt: dict[str, Any]) -> float:
        """Maximum score offered by filled questions, respecting answer choices."""
        total = 0.0
        for section in fmt.get("sections", []):
            sid = section["id"]
            scores = []
            for number in range(1, section["total_questions"] + 1):
                if not self.is_filled(sid, number):
                    continue
                question = self.get_question(sid, number) or {}
                scores.append(float(question.get("marks", section["marks_per_question"])))
            total += sum(sorted(scores, reverse=True)[:section.get("attempt_count", section["total_questions"])])
        return total

    # -- normalisation ----------------------------------------------------
    @staticmethod
    def _normalise(data: dict[str, Any]) -> dict[str, Any]:
        """Return a complete question dict with all keys present and typed."""
        sub_parts_in = data.get("sub_parts") or {}
        sub_parts: dict[str, dict[str, Any]] = {}
        for label, part in sub_parts_in.items():
            part = part or {}
            sub_parts[str(label)] = {
                "text": str(part.get("text", "")),
                "marks": float(part.get("marks", 0) or 0),
            }
        return {
            "text": str(data.get("text", "")),
            "type": data.get("type", "short_answer"),
            "options": list(data.get("options") or []),
            "answer": str(data.get("answer", "")),
            "marks": float(data.get("marks", 0) or 0),
            "image_path": data.get("image_path") or None,
            "image_width_pct": int(data.get("image_width_pct", 100) or 100),
            "image_position": data.get("image_position", "below"),
            "table_def": data.get("table_def") or None,
            "sub_parts": sub_parts,
        }

    # -- serialisation ----------------------------------------------------
    def to_json(self) -> str:
        """Serialise the whole state to a JSON string (question nums as strings)."""
        payload = {
            "format_id": self.format_id,
            "sections": {
                sid: {str(num): q for num, q in questions.items()}
                for sid, questions in self._sections.items()
            },
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "PaperState":
        payload = json.loads(raw)
        state = cls(format_id=payload.get("format_id"))
        for sid, questions in payload.get("sections", {}).items():
            for num, q in questions.items():
                state.add_question(sid, int(num), q)
        return state
