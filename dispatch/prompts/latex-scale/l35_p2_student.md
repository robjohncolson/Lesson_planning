## Task: render the L35_P2 Student packet to LaTeX

You are working in `C:/Users/rober/Downloads/Projects/Lesson_planning`. The
docx-emitting Python toolchain has a parallel LaTeX path being built. Your
job is one .tex file. The L41_P2 lesson is already converted — read its
.tex files first to copy the style.

### Inputs you must read

1. `graph/eye_check/L35_P2.md` — the structured intent brief. The
   `## build_student` section in that file lists every callout,
   framework_phase_header, sentence frame, bank-item label, and section
   in source order. **Treat this as the spec — preserve verbatim.**
2. `tex/preamble.sty` — already exists. Use its commands and environments
   (callout, sentenceframebox, summaryexitbox, framework_phase_header,
   bankitem, packetheading, daybanner, sectionbanner, IconBook/Warn/Star
   etc.). **Do NOT modify it.** If you need a teacher-specific helper
   like \phasetag / \phaseitems / \teacheranswerbox, define it inline
   at the top of your output .tex file.
3. `tex/L41_P2_student.tex` — reference rendering for the same
   edition type. Copy its coding style (tcolorbox calls, math wrapping
   in \(...\), TikZ usage, table style for objectives).
4. `build_L35_P2_packets.py` — the Python builder for this lesson. Use
   only as a reference for visual hierarchy and bank-item ordering. Do
   NOT modify it.
5. `L35_P2_Student_Packet.docx` — canonical visual reference.
6. `questionbank/registry.jsonl` — read items by ID. Render `prompt` and
   `answers` (if any) verbatim — do NOT paraphrase.

### Output (one new file)

`tex/L35_P2_student.tex` — standalone document, starts with:
```
\documentclass[11pt]{article}
\usepackage{preamble}
```
plus any file-local helper commands you need.

Must include:
- The standard packetheading (subtitle marked "· Student Packet")
- The Objectives table and Topic Goals/Essential Question/Materials table
- All callouts in the brief's `## build_student` section in source order
- All EXPLORE bank items with prompts (no answer keys for student edition)
- Sentence frame box for Share/Summary
- Summary exit box for Exit Ticket
- (back) Optional Reinforcement section after a `\clearpage`

### Must preserve (non-negotiable)

- All callout titles AND body lines verbatim — these are 'rules printed
  on the page' and ELL-supports.
- Sentence frames verbatim — ELL non-negotiable.
- Bank-item ordering and labels exactly as listed in the brief's
  "Bank-item labels (in order)" section.
- Section ordering in source order from the brief.
- **Do not substitute computed answers into prompt content.** If a
  Savvas item describes a curve as `w = k/f`, your TikZ/text annotation
  must also say `w = k/f` — NOT `w = 300000/f` even though k=300000
  follows from the given pair. Pre-computing k strips the problem of
  its pedagogical purpose. (Teacher edition is the only place computed
  k values may appear, and only inside the answer-key block.)
- TikZ annotations should mirror the prompt's symbolic form, not your
  derived numeric form.


### May restructure

- Margin sizes, font choices — match the docx visual hierarchy but use
  LaTeX-native idioms.
- Color hex values — use closest equivalent from preamble's palette.
- Where to place answer keys (teacher only) — inline below each item or
  as an appendix. Pick whichever stays evaluator-friendly.

### Validation before reporting done

1. Run `pdflatex tex/L35_P2_student.tex --miktex-enable-installer`
   (or lualatex if pdflatex chokes on unicode).
2. Confirm a PDF was produced; report page count.
3. Sample-check via pdftotext that key anchors from the brief appear.
4. Brief summary: engine used, page count, any anchor not preserved.

### Constraints

- Write ONLY to `tex/L35_P2_student.tex`. Do not modify the
  preamble, the python builders, the docx files, or anything outside
  this single file.
- Do not commit or push.
- Hard timeout 600s. If time-pressured, prioritize compile-clean PDF
  with all callouts present over visual polish.
