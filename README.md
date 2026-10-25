# PprBase

PprBase helps a teacher make a neatly formatted question paper without laying out a Word document by hand. It is a desktop app for Windows, written in Python with PyQt6. It works offline; AI question generation is outside the current version.

## For the teacher

1. Open **PprBase.exe** from the `PprBase` folder supplied by the builder. Keep the whole folder together.
2. To reuse a paper you already like, click **Import Word Template** and choose its `.docx` file. Review the detected sections, marks and **Replace old questions from** line. Everything above that line stays in new Word papers; the questions below it are replaced. Save the template to open a blank paper in that format. Its card stays on the Formats screen; click **New paper** whenever you want another blank paper from it.
   Click **Edit Template** on that card to change its name, header details, sections, marks, or replacement boundary. Use **Replace Word file…** there if you have revised the sample document itself; review the newly detected layout before saving. Existing drafts retain their own copy of the earlier Word file. You can also click **Create Format** to make a format without a Word file. For an “answer any 2 of 3” section, set **Number of questions** to 3 and **Students answer** to 2.
3. Type each question. Use **Next** or the paper structure panel to move around. Edits are kept when you move. You can add multiple choice options, sub-parts, an image, a blank table, and optional answers for the answer key. Select a digit in the question and click **Subscript** or **Superscript** for science notation.
4. Click **Preview / PDF** to inspect the printable pages inside PprBase. Click **Save PDF…** in that window to make a ready-to-print PDF.
5. Click **Generate Paper** to save an editable `.docx`. The app warns if any question is empty or if assigned marks differ from the paper total. **Answer Key** saves a separate `.docx`.

Drafts save automatically every two minutes, when you move between questions, and when you return to Formats or close the app. Click **Save Draft** for an immediate save. Recent drafts appear under **Continue a draft** on the Formats screen. Attached images are copied into the draft folder so the saved paper can reopen if the original image moves. The **A−** and **A+** buttons change text size.

For an imported Word template, the editable `.docx` starts with a copy of the uploaded file. It keeps the content above the chosen boundary, page setup and document styles, then lays out the new sections and questions. Review the generated file in Word before printing: the new question body is rebuilt and may need a small formatting adjustment for unusual source documents. The PDF preview uses PprBase's separate layout and may look different from an imported Word template. A Word-compatible application such as Microsoft Word or LibreOffice is needed to edit the `.docx`. A blank line is printed for each unfilled question if you choose to export an incomplete paper.

## Build for Windows

On a Windows computer with Python 3 installed, double-click `build_windows.bat`. It installs the required Python packages and builds `dist\PprBase\PprBase.exe`. Copy the **entire** `dist\PprBase` folder to the teacher's computer. The teacher does not need Python installed for the built app.

If Python is installed but you have not built the app, double-click `Start PprBase.bat` to run it from source. That script installs dependencies on first use. The release build is the simpler option for daily use.

The Windows app keeps user files in `%APPDATA%\PprBase\`. If a previous QuestionCraft version stored files in `%APPDATA%\QuestionCraft\`, PprBase copies that folder on first launch and keeps the original as a backup.

- `formats\` — paper formats, including the sample on first launch
- `templates\` — saved copies of imported Word templates
- `drafts\` — recoverable papers and copied images
- `output\` — default destination for generated documents

Keep a backup of that folder to preserve formats and drafts. Building the app on Linux does not produce a Windows executable; run the build script on Windows.

## Development

Requires Python 3.11 or newer.

```bash
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python main.py
./venv/bin/python -m unittest discover -s tests -v
```

The sample paper layout is `formats/class7_chemistry.json`. The editor model is `core/state_manager.py`; local draft storage is `core/draft_store.py`; Word template detection is `core/word_template.py`; Word generation is `core/document_engine.py`; PDF generation is `core/pdf_engine.py`. A format can also be imported from a JSON file; the schema is documented in `formats/README.md`. The original `master.txt` and `additional.txt` are planning notes.

Three complete dummy papers (25, 50 and 100 marks), their PDFs, and answer keys are in `samples/`. Run `./venv/bin/python -m scripts.generate_sample_papers` to regenerate them. The automated tests export all three through the app, reopen saved drafts, and inspect the generated Word and PDF files.

The supplied Class VI and VII Chemistry Unit Test Word papers are installed as reusable Word templates in `templates/`, with matching format cards. Their originals are in `tests/fixtures/chemistry/` for repeatable tests. Earlier transcribed drafts and exports remain in `samples/reference_papers/`; see that folder's README for details.

Four new example Word papers made from those two templates are in `samples/template_reuse_demo/` (two different papers per template). Run `./venv/bin/python -m scripts.generate_template_reuse_demo` to regenerate them. The script checks the 25-mark totals, retained school header, and absence of old sample questions.
