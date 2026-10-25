"""Export two new 25-mark papers from each imported Word template."""

from __future__ import annotations

from pathlib import Path

from docx import Document

from core.document_engine import DocumentEngine
from core.format_loader import load_format
from core.state_manager import PaperState


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "samples" / "template_reuse_demo"

QUESTIONS = {
    "A": [
        "Which substance is an element?",
        "Which process separates sand from water?",
        "Which particle has a negative charge?",
        "Which material dissolves in water?",
        "Which change forms a new substance?",
        "Which gas supports combustion?",
    ],
    "B": [
        "Which substance is a compound?",
        "Which process separates salt from water?",
        "Which particle has a positive charge?",
        "Which material is insoluble in water?",
        "Which change can be reversed easily?",
        "Which gas is most abundant in air?",
    ],
}


def make_paper(fmt: dict, variant: str, destination: Path, old_question: str) -> None:
    state = PaperState(fmt["format_id"])
    for section in fmt["sections"]:
        sid = section["id"]
        for number in range(1, section["total_questions"] + 1):
            if sid == "A":
                prompt = QUESTIONS[variant][number - 1]
                options = ["Iron", "Water", "Air", "Soil"] if variant == "A" else ["Oxygen", "Water", "Air", "Sand"]
            else:
                topics = ["matter", "elements", "mixtures", "atoms", "compounds", "solutions"]
                topic = topics[(number + ord(sid) - 66 + (0 if variant == "A" else 3)) % len(topics)]
                if section["question_type"] == "MCQ":
                    prompt = f"Which description best fits {topic}?"
                    options = [
                        "A pure substance", "Two or more substances together",
                        "A form of energy", "A change of state",
                    ]
                else:
                    prompt = (
                        f"State one property of {topic}." if variant == "A"
                        else f"Give an example of {topic} and explain your choice."
                    )
                    options = []
            state.add_question(sid, number, {
                "text": prompt,
                "type": section["question_type"],
                "options": options,
                "marks": section["marks_per_question"],
            })
    if state.allocated_marks(fmt) != fmt["total_marks"]:
        raise AssertionError("Demo paper marks do not match the template")
    DocumentEngine(fmt, state).save(str(destination))
    exported = "\n".join(paragraph.text for paragraph in Document(destination).paragraphs)
    if QUESTIONS[variant][0] not in exported:
        raise AssertionError("New questions are missing from exported paper")
    other_variant = "B" if variant == "A" else "A"
    if QUESTIONS[other_variant][0] in exported:
        raise AssertionError("A different new paper's questions leaked into this paper")
    if "St Vincent Pallotti School" not in exported:
        raise AssertionError("The original Word header was lost")
    if old_question in exported:
        raise AssertionError("An old sample question leaked into the new paper")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for klass, old_question in (("vi", "Risa prepared lemonade"), ("vii", "Vishal has a mixture")):
        fmt = load_format(str(ROOT / "formats" / f"chemistry_ut1_class_{klass}.json"))
        for variant in ("A", "B"):
            destination = OUT / f"chemistry_class_{klass}_new_paper_{variant.lower()}.docx"
            make_paper(fmt, variant, destination, old_question)
            print(destination)


if __name__ == "__main__":
    main()
