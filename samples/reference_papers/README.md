# Supplied Chemistry Unit Test papers

The Class VI and Class VII 2024 Word files supplied for testing are installed as **Word Template** cards on the Formats screen. Opening a card starts a new, blank paper with that sample's section and marks pattern. The original `.docx` files are stored in `templates/` and preserved in `tests/fixtures/chemistry/` for repeatable tests.

The earlier manually transcribed complete papers are still available under **Continue a draft**. Their previous format definitions are archived in `samples/reference_papers/legacy_formats/`. The table below describes those earlier exports, not new papers created from the Word templates.

| Class | Editable paper | Printable paper | PDF pages |
|---|---|---|---:|
| VI | `chemistry_ut1_class_vi.docx` | `chemistry_ut1_class_vi.pdf` | 4 |
| VII | `chemistry_ut1_class_vii.docx` | `chemistry_ut1_class_vii.pdf` | 5 |

Both papers contain 21 editable question slots. Section I supplies 15 marks. Section II prints Questions 2–4 at 5 marks each and asks students to answer any two, giving a 25-mark maximum. The import retains the paper title, section structure, half marks, six answer parts per Section II question, and the main diagrams. Answer keys are blank because no answers were supplied.

Those earlier complete papers are reviewed transcriptions of these two specific documents. Run `python -m scripts.import_chemistry_references` to regenerate those drafts; use `--refresh` only to replace their content. For new formats from other `.docx` files, use **Import Word Template** in the app and review the detected section counts and replacement boundary.

## Source content to review

- Class VII case-study text says “proteins” where it appears to mean “protons.” This wording is preserved.
- Class VII asks students to identify X and Y in the separating-funnel image, but the supplied image has no X/Y labels. Its sublimation image labels camphor while the question discusses ammonium chloride and sodium chloride.
- Class VI asks about an aluminium property using an image labelled “Stainless Steel Pipes.” The supplied image is preserved.
- Several source option labels and chemical formulas appear inconsistent. Please check the imported question text and choices before handing either paper to students.

The automated tests check the imported marks, choice rule, numbering, draft recovery, images, Word export, PDF export, and pagination. See `import_report.json` for the output names and page counts.
