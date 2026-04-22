## Task: render the L35_P3 Teacher packet to LaTeX

You are working in `C:/Users/rober/Downloads/Projects/Lesson_planning`. The
docx-emitting Python toolchain has a parallel LaTeX path being built. Your
job is one .tex file. The L41_P2 lesson is already converted — read its
.tex files first to copy the style.

### Inputs you must read

1. `graph/eye_check/L35_P3.md` — the structured intent brief. The
   `## build_teacher` section in that file lists every callout,
   framework_phase_header, sentence frame, bank-item label, and section
   in source order. **Treat this as the spec — preserve verbatim.**
2. `tex/preamble.sty` — already exists. Use its commands and environments
   (callout, sentenceframebox, summaryexitbox, framework_phase_header,
   bankitem, packetheading, daybanner, sectionbanner, IconBook/Warn/Star
   etc.). **Do NOT modify it.** If you need a teacher-specific helper
   like \phasetag / \phaseitems / \teacheranswerbox, define it inline
   at the top of your output .tex file.
3. `tex/L41_P2_teacher.tex` — reference rendering for the same
   edition type. Copy its coding style (tcolorbox calls, math wrapping
   in \(...\), TikZ usage, table style for objectives).
4. `build_L35_P3_packets.py` — the Python builder for this lesson. Use
   only as a reference for visual hierarchy and bank-item ordering. Do
   NOT modify it.
5. `L35_P3_Teacher_Packet.docx` — canonical visual reference.
6. `questionbank/registry.jsonl` — read items by ID. Render `prompt` and
   `answers` (if any) verbatim — do NOT paraphrase.

### Output (one new file)

`tex/L35_P3_teacher.tex` — standalone document, starts with:
```
\documentclass[11pt]{article}
\usepackage{preamble}
```
plus any file-local helper commands you need.

Must include:
- packetheading subtitle marked "· Teacher Edition"
- The Objectives + Framework Header tables
- A PRE-FLIGHT callout at the top of the body (color: calloutpink)
- One \frameworkphaseheader block per phase (Do Now, Launch, Explore,
  Share/Summary, Exit Ticket) — copy DOK / minutes / teacher_does /
  students_do / questions_to_ask / adult_role verbatim from the brief
- Each bank item with both prompt AND answer key (use a small inline
  helper like \teacheranswerbox or a `\textbf{Answer:}` line)
- Page break before any trailing 65-MIN / IEP / ELL accommodation
  callouts

### Must preserve (non-negotiable)

- All callout titles AND body lines verbatim — these are 'rules printed
  on the page' and ELL-supports.
- Sentence frames verbatim — ELL non-negotiable.
- Bank-item ordering and labels exactly as listed in the brief's
  "Bank-item labels (in order)" section.
- Section ordering in source order from the brief.
- Every framework_phase_header field (DOK, minutes, teacher_does,
  students_do, questions_to_ask, adult_role) — evaluators look for these.
- All accommodation callouts (PRE-FLIGHT, MODIFICATIONS / IEP, ELL,
  PERIOD A/F variants) verbatim.

### May restructure

- Margin sizes, font choices — match the docx visual hierarchy but use
  LaTeX-native idioms.
- Color hex values — use closest equivalent from preamble's palette.
- Where to place answer keys (teacher only) — inline below each item or
  as an appendix. Pick whichever stays evaluator-friendly.

### Validation before reporting done

1. Run `pdflatex tex/L35_P3_teacher.tex --miktex-enable-installer`
   (or lualatex if pdflatex chokes on unicode).
2. Confirm a PDF was produced; report page count.
3. Sample-check via pdftotext that key anchors from the brief appear.
4. Brief summary: engine used, page count, any anchor not preserved.

### Constraints

- Write ONLY to `tex/L35_P3_teacher.tex`. Do not modify the
  preamble, the python builders, the docx files, or anything outside
  this single file.
- Do not commit or push.
- Hard timeout 600s. If time-pressured, prioritize compile-clean PDF
  with all callouts present over visual polish.
