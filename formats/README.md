# Formats

Each `.json` file in this folder defines one question-paper format (a class +
subject layout). Adding a new class or subject is as simple as dropping a new
JSON file here — the app picks it up automatically on the Format Selector screen.

See `class7_chemistry.json` for a complete example.

## Required fields

| Field | Type | Notes |
|---|---|---|
| `format_id` | string | Unique id, no spaces (e.g. `class7_chemistry`) |
| `display_name` | string | Shown on the format card |
| `school_name` | string | Printed in the paper header |
| `paper_title` | string | Optional exam title, such as `Unit Test-1` |
| `subject` | string | |
| `class` | string | |
| `total_marks` | number | |
| `duration` | string | e.g. `"3 hours"` |
| `instructions` | list of strings | Printed under the header |
| `sections` | list of section objects | See below |
| `docx_template` | string or null | Optional path to a stored Word template, relative to this JSON file or absolute |
| `template_body_start` | integer | For a Word template: first document body element to replace with new questions |

## Section object

| Field | Type | Notes |
|---|---|---|
| `id` | string | e.g. `"A"` |
| `title` | string | Section heading |
| `description` | string | Sub-heading instruction line |
| `question_type` | string | `MCQ`, `short_answer`, or `long_answer` |
| `marks_per_question` | number | |
| `total_questions` | number | How many question slots in this section |
| `attempt_count` | number | Optional number students answer; defaults to all printed questions |
| `start_number` | number | Optional first printed question number; defaults to 1 |
| `sub_parts` | list of strings or null | e.g. `["i", "ii", "iii"]` |

For a choice section with three printed 5-mark questions where students answer any two, set `total_questions` to `3`, `attempt_count` to `2`, and `marks_per_question` to `5`. PprBase counts that section as 10 marks and prints the choice instruction.
