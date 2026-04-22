"""Generate dispatch/prompts/latex-scale/*.md and
dispatch/parallel-batch.manifest.json for the 17-lesson × 2-edition
LaTeX scaling pass. Each agent writes ONE .tex file; preamble.sty is
already in place and not modified.

Run:  python generate_latex_scale_manifest.py
Then: python C:/Users/rober/Downloads/Projects/Agent/runner/parallel-codex-runner.py \
        --manifest dispatch/parallel-batch.manifest.json --max-parallel 3
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
EYE_CHECK_DIR = ROOT / "graph" / "eye_check"
PROMPTS_DIR = ROOT / "dispatch" / "prompts" / "latex-scale"
MANIFEST = ROOT / "dispatch" / "parallel-batch.manifest.json"

# L41_P2 already done — exclude.
DONE = {"L41_P2"}

PROMPT_TEMPLATE = """## Task: render the {LESSON} {EDITION_TITLE} packet to LaTeX

You are working in `C:/Users/rober/Downloads/Projects/Lesson_planning`. The
docx-emitting Python toolchain has a parallel LaTeX path being built. Your
job is one .tex file. The L41_P2 lesson is already converted — read its
.tex files first to copy the style.

### Inputs you must read

1. `graph/eye_check/{LESSON}.md` — the structured intent brief. The
   `## build_{EDITION_LOWER}` section in that file lists every callout,
   framework_phase_header, sentence frame, bank-item label, and section
   in source order. **Treat this as the spec — preserve verbatim.**
2. `tex/preamble.sty` — already exists. Use its commands and environments
   (callout, sentenceframebox, summaryexitbox, framework_phase_header,
   bankitem, packetheading, daybanner, sectionbanner, IconBook/Warn/Star
   etc.). **Do NOT modify it.** If you need a teacher-specific helper
   like \\phasetag / \\phaseitems / \\teacheranswerbox, define it inline
   at the top of your output .tex file.
3. `tex/L41_P2_{EDITION_LOWER}.tex` — reference rendering for the same
   edition type. Copy its coding style (tcolorbox calls, math wrapping
   in \\(...\\), TikZ usage, table style for objectives).
4. `build_{BUILDER_NAME}.py` — the Python builder for this lesson. Use
   only as a reference for visual hierarchy and bank-item ordering. Do
   NOT modify it.
5. `{LESSON}_{EDITION_DOCX_NAME}.docx` — canonical visual reference.
6. `questionbank/registry.jsonl` — read items by ID. Render `prompt` and
   `answers` (if any) verbatim — do NOT paraphrase.

### Output (one new file)

`tex/{LESSON}_{EDITION_LOWER}.tex` — standalone document, starts with:
```
\\documentclass[11pt]{{article}}
\\usepackage{{preamble}}
```
plus any file-local helper commands you need.

{EDITION_SPECIFIC}

### Must preserve (non-negotiable)

- All callout titles AND body lines verbatim — these are 'rules printed
  on the page' and ELL-supports.
- Sentence frames verbatim — ELL non-negotiable.
- Bank-item ordering and labels exactly as listed in the brief's
  "Bank-item labels (in order)" section.
- Section ordering in source order from the brief.
{EDITION_MUST_PRESERVE}

### May restructure

- Margin sizes, font choices — match the docx visual hierarchy but use
  LaTeX-native idioms.
- Color hex values — use closest equivalent from preamble's palette.
- Where to place answer keys (teacher only) — inline below each item or
  as an appendix. Pick whichever stays evaluator-friendly.

### Validation before reporting done

1. Run `pdflatex tex/{LESSON}_{EDITION_LOWER}.tex --miktex-enable-installer`
   (or lualatex if pdflatex chokes on unicode).
2. Confirm a PDF was produced; report page count.
3. Sample-check via pdftotext that key anchors from the brief appear.
4. Brief summary: engine used, page count, any anchor not preserved.

### Constraints

- Write ONLY to `tex/{LESSON}_{EDITION_LOWER}.tex`. Do not modify the
  preamble, the python builders, the docx files, or anything outside
  this single file.
- Do not commit or push.
- Hard timeout 600s. If time-pressured, prioritize compile-clean PDF
  with all callouts present over visual polish.
"""

EDITION_SPECIFIC = {
    "student": """Must include:
- The standard packetheading (subtitle marked "· Student Packet")
- The Objectives table and Topic Goals/Essential Question/Materials table
- All callouts in the brief's `## build_student` section in source order
- All EXPLORE bank items with prompts (no answer keys for student edition)
- Sentence frame box for Share/Summary
- Summary exit box for Exit Ticket
- (back) Optional Reinforcement section after a `\\clearpage`""",
    "teacher": """Must include:
- packetheading subtitle marked "· Teacher Edition"
- The Objectives + Framework Header tables
- A PRE-FLIGHT callout at the top of the body (color: calloutpink)
- One \\frameworkphaseheader block per phase (Do Now, Launch, Explore,
  Share/Summary, Exit Ticket) — copy DOK / minutes / teacher_does /
  students_do / questions_to_ask / adult_role verbatim from the brief
- Each bank item with both prompt AND answer key (use a small inline
  helper like \\teacheranswerbox or a `\\textbf{Answer:}` line)
- Page break before any trailing 65-MIN / IEP / ELL accommodation
  callouts""",
}

EDITION_MUST_PRESERVE = {
    "student": "",
    "teacher": """- Every framework_phase_header field (DOK, minutes, teacher_does,
  students_do, questions_to_ask, adult_role) — evaluators look for these.
- All accommodation callouts (PRE-FLIGHT, MODIFICATIONS / IEP, ELL,
  PERIOD A/F variants) verbatim.""",
}


def builder_name(lesson: str) -> str:
    """L41_P2 -> L41_P2_packets"""
    return f"{lesson}_packets"


def docx_edition_name(edition: str) -> str:
    return {"student": "Student_Packet", "teacher": "Teacher_Packet"}[edition]


def lessons() -> list[str]:
    return sorted(p.stem for p in EYE_CHECK_DIR.glob("L*_P*.md") if p.stem not in DONE)


def main() -> None:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    agents = []
    for lesson in lessons():
        for edition in ("student", "teacher"):
            agent_name = f"{lesson.lower()}_{edition}"
            prompt_path = PROMPTS_DIR / f"{agent_name}.md"
            prompt_text = PROMPT_TEMPLATE.format(
                LESSON=lesson,
                EDITION_TITLE=edition.title(),
                EDITION_LOWER=edition,
                EDITION_DOCX_NAME=docx_edition_name(edition),
                BUILDER_NAME=builder_name(lesson),
                EDITION_SPECIFIC=EDITION_SPECIFIC[edition],
                EDITION_MUST_PRESERVE=EDITION_MUST_PRESERVE[edition],
            )
            prompt_path.write_text(prompt_text, encoding="utf-8")
            agents.append({
                "name": agent_name,
                "description": f"LaTeX rendering of {lesson} {edition} packet",
                "prompt_file": f"dispatch/prompts/latex-scale/{agent_name}.md",
                # Glob covers .tex, .pdf, .aux, .log, .out, .synctex.gz so the
                # build artifacts pdflatex emits in-place don't trigger
                # ownership-enforcement rejection.
                "owned_paths": [f"tex/{lesson}_{edition}.*"],
            })

    manifest = {
        "$schema": "../../Agent/schema/parallel-runner-manifest.schema.json",
        "version": 1,
        "batch_name": "latex-scale-v1",
        "target_branch": "main",
        "base_ref": "main",
        "codex_approval_mode": "full-auto",
        "verify_commands": [],
        "agents": agents,
        "merge": {
            "enabled": True,
            "commit_prefix": "latex-scale",
            "verify_commands": [],
        },
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {MANIFEST.relative_to(ROOT)} with {len(agents)} agents.")
    print(f"Wrote {len(agents)} prompt files under {PROMPTS_DIR.relative_to(ROOT)}/")
    print(f"\nNext: python C:/Users/rober/Downloads/Projects/Agent/runner/parallel-codex-runner.py \\\n"
          f"        --manifest dispatch/parallel-batch.manifest.json --max-parallel 3")


if __name__ == "__main__":
    main()
