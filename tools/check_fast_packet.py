#!/usr/bin/env python3
"""Lint a fast-lesson packet (and optionally its short-form quiz) against the fast-lesson spec.

    python tools/check_fast_packet.py a2_2-1_fast.tex --te a2_2-1_TE.tex \
        --quiz a2_2-1_quiz_fast.tex --ixl-map ../algebra2-live-worksheet/data/ixl-algebra2-skills.json \
        [--max-examples 2] [--max-pages 4] [--compile] [--build-dir DIR] [--report out.json]

Spec: algebra2-live-worksheet/docs/a2-fast-lesson-spec.md (sections 4, 5, 6, 11).

FAIL (exit 1) when the packet is not on the template, lacks the goals / quiz-target / topic-target /
IXL blocks (the topic-target box must name the lesson's own topic),
keeps an Example without its Try It, names an Example or Try It the Teacher Edition does not have,
stars nothing, drops the SmartScore sentence, uses an IXL code outside the Algebra 2 map, has no PDF,
or runs past the page budget. Softer things (title wording, missing "Say it", example count) are
WARN. --compile runs pdflatex first (into --build-dir, default <tex dir>/build) and copies the PDF
next to the .tex. Prints a JSON report; --report writes it to a file too.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SMARTSCORE = "SmartScore 70 or above on each starred"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def strip_comments(tex: str) -> str:
    out = []
    for line in tex.splitlines():
        # drop everything after an unescaped %
        buf = []
        prev = ""
        for ch in line:
            if ch == "%" and prev != "\\":
                break
            buf.append(ch)
            prev = ch
        out.append("".join(buf))
    return "\n".join(out)


def pdf_pages(pdf: Path) -> int | None:
    exe = shutil.which("pdfinfo")
    if not exe or not pdf.exists():
        return None
    try:
        res = subprocess.run([exe, str(pdf)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"^Pages:\s+(\d+)", res.stdout, re.M)
    return int(m.group(1)) if m else None


def compile_tex(tex: Path, build_dir: Path) -> tuple[bool, str]:
    exe = shutil.which("pdflatex")
    if not exe:
        return False, "pdflatex not on PATH"
    build_dir.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "-interaction=nonstopmode", "-halt-on-error",
           f"-output-directory={build_dir}", tex.name]
    try:
        res = subprocess.run(cmd, cwd=str(tex.parent), capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=300)
    except subprocess.TimeoutExpired:
        return False, "pdflatex timed out after 300 s"
    except OSError as exc:
        return False, f"pdflatex failed to start: {exc}"
    log = build_dir / (tex.stem + ".log")
    log_text = read(log) if log.exists() else res.stdout
    if res.returncode != 0:
        errs = [ln for ln in log_text.splitlines() if ln.startswith("!")]
        return False, "; ".join(errs[:5]) or f"pdflatex exit {res.returncode}"
    built = build_dir / (tex.stem + ".pdf")
    if not built.exists():
        return False, "pdflatex produced no PDF"
    shutil.copyfile(built, tex.with_suffix(".pdf"))
    return True, "ok"


def te_numbers(te_text: str, env: str) -> set[int]:
    return {int(n) for n in re.findall(r"\\begin\{" + env + r"\}\{(\d+)\}", te_text)}


def te_title(te_text: str) -> str | None:
    m = re.search(r"^title:\s*(.+)$", te_text, re.M)
    return m.group(1).strip() if m else None


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def check_packet(args, report: dict) -> None:
    tex_path = Path(args.tex)
    fails, warns, info = report["fails"], report["warns"], report["info"]
    if not tex_path.exists():
        fails.append(f"packet not found: {tex_path}")
        return
    raw = read(tex_path)
    tex = strip_comments(raw)
    info["packet"] = str(tex_path)

    if r"\input{fast-packet-template}" not in tex:
        fails.append("packet does not \\input{fast-packet-template}")
    head = re.search(r"\\packethead\{Lesson\s+([\d]+-[\d]+)\}\{([^}]*)\}", tex)
    if not head:
        fails.append("missing \\packethead{Lesson X-Y}{Title}")
        lesson, title = None, None
    else:
        lesson, title = head.group(1), head.group(2).strip()
        info["lesson"], info["title"] = lesson, title
        if args.lesson and args.lesson != lesson:
            fails.append(f"packethead lesson {lesson} != expected {args.lesson}")
    if "\\goals{" not in tex:
        fails.append("missing \\goals{learning}{language}")
    if "\\quiztarget{" not in tex:
        fails.append("missing \\quiztarget{...}")
    topic_box = re.search(r"\\topictarget\{(\d+)\}\{", tex)
    if not topic_box:
        fails.append("missing \\topictarget{<topic>}{...} (the Topic Assessment items the kept Examples answer; spec R1, R8)")
    elif lesson and topic_box.group(1) != lesson.split("-")[0]:
        fails.append(f"\\topictarget names Topic {topic_box.group(1)} but lesson {lesson} is in Topic {lesson.split('-')[0]}")
    else:
        info["topicTarget"] = topic_box.group(1)

    examples = [int(n) for n in re.findall(r"\\wspart\{Example\s+(\d+)\}", tex)]
    tryits = [int(n) for n in re.findall(r"\\wspart\{Try It\s+(\d+)\}", tex)]
    info["examples"], info["tryIts"] = examples, tryits
    if not examples:
        fails.append("no \\wspart{Example N} block")
    if len(examples) != len(set(examples)):
        fails.append(f"an Example number repeats: {examples}")
    if args.max_examples and len(examples) > args.max_examples:
        warns.append(f"{len(examples)} Examples kept; the plan allows {args.max_examples}")
    for n in examples:
        if n not in tryits:
            fails.append(f"Example {n} has no \\wspart{{Try It {n}}} block")
    for n in tryits:
        if n not in examples:
            warns.append(f"Try It {n} appears without Example {n}")
    # Example before its Try It, in document order
    order = [(m.start(), m.group(1), int(m.group(2))) for m in re.finditer(r"\\wspart\{(Example|Try It)\s+(\d+)\}", tex)]
    for n in examples:
        ex_pos = next((p for p, k, m in order if k == "Example" and m == n), None)
        ti_pos = next((p for p, k, m in order if k == "Try It" and m == n), None)
        if ex_pos is not None and ti_pos is not None and ti_pos < ex_pos:
            fails.append(f"Try It {n} comes before Example {n}")

    if args.te:
        te_path = Path(args.te)
        if not te_path.exists():
            fails.append(f"TE transcription not found: {te_path}")
        else:
            te = read(te_path)
            te_ex, te_ti = te_numbers(te, "example"), te_numbers(te, "tryit")
            info["teExamples"] = sorted(te_ex)
            for n in examples:
                if n not in te_ex:
                    fails.append(f"Example {n} is not in the TE ({sorted(te_ex)})")
            for n in tryits:
                if n not in te_ti:
                    fails.append(f"Try It {n} is not in the TE ({sorted(te_ti)})")
            tt = te_title(te)
            if tt and title and norm(tt) != norm(title):
                warns.append(f"title '{title}' differs from the TE title '{tt}'")
            if tt:
                info["teTitle"] = tt

    ixl_section = re.search(r"\\wspart\{IXL\}", tex)
    if not ixl_section:
        fails.append("missing \\wspart{IXL}{...} block")
    rows = re.findall(r"\\ixlrow\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}", tex)
    info["ixlRows"] = [{"code": r[0].split()[0] if r[0].split() else "", "skill": r[1].strip(), "feeds": r[2].strip(),
                        "starred": ("\\bigstar" in r[0] or "\\star" in r[0])} for r in rows]
    if not rows:
        fails.append("no \\ixlrow{code}{skill}{feeds} rows")
    if rows and not any(row["starred"] for row in info["ixlRows"]):
        fails.append("no starred IXL skill (\\bigstar or \\star)")
    if SMARTSCORE not in tex:
        fails.append(f'missing the sentence "{SMARTSCORE} ..."')
    core_rows = [row for row in info["ixlRows"] if row["starred"]]
    if len(info["ixlRows"]) > 6:
        warns.append(f"{len(info['ixlRows'])} IXL rows; the spec wants 2-4 core plus 0-2 warm-up")
    if args.ixl_map:
        map_path = Path(args.ixl_map)
        if not map_path.exists():
            fails.append(f"IXL map not found: {map_path}")
        else:
            codes = {s["code"] for s in json.loads(read(map_path))["skills"]}
            for row in info["ixlRows"]:
                if row["code"] and row["code"] not in codes:
                    fails.append(f"IXL code {row['code']} is not in the Algebra 2 map")
    if not re.search(r"Say it", tex):
        warns.append('no "Say it:" sentence frame after an Example')
    after_ixl = tex[ixl_section.end():] if ixl_section else ""
    if ixl_section and not (re.search(r"\\wspart\{", after_ixl) or re.search(r"Before the quiz|finish these sentences", after_ixl)):
        warns.append("nothing after the IXL block: the spec wants an exit question or sentence completions")

    if args.compile:
        ok, msg = compile_tex(tex_path, Path(args.build_dir) if args.build_dir else tex_path.parent / "build")
        info["compile"] = msg
        if not ok:
            fails.append(f"pdflatex: {msg}")
    pdf = Path(args.pdf) if args.pdf else tex_path.with_suffix(".pdf")
    pages = pdf_pages(pdf)
    info["pdf"], info["pages"] = str(pdf), pages
    if pages is None:
        fails.append(f"no readable PDF at {pdf} (compile it, or pass --pdf)")
    elif pages > args.max_pages:
        fails.append(f"{pages} pages; the budget is {args.max_pages}")


def check_quiz(args, report: dict) -> None:
    quiz_path = Path(args.quiz)
    fails, warns, info = report["fails"], report["warns"], report["info"]
    if not quiz_path.exists():
        fails.append(f"quiz not found: {quiz_path}")
        return
    tex = strip_comments(read(quiz_path))
    info["quiz"] = str(quiz_path)
    if "\\documentclass" not in tex:
        fails.append("quiz is not a standalone document")
    if not re.search(r"Scoring", tex):
        fails.append("quiz has no Scoring line")
    if not re.search(r"answer key", tex, re.I):
        fails.append("quiz has no answer key page")
    if not re.search(r"IXL replacement|replaces this quiz|replaces your quiz", tex):
        warns.append("quiz key does not name the IXL replacement rule")
    items = re.findall(r"\\textbf\{(\d+)\.\}", tex)
    info["quizItems"] = sorted({int(n) for n in items})
    if args.compile:
        ok, msg = compile_tex(quiz_path, Path(args.build_dir) if args.build_dir else quiz_path.parent / "build")
        info["quizCompile"] = msg
        if not ok:
            fails.append(f"quiz pdflatex: {msg}")
    pages = pdf_pages(quiz_path.with_suffix(".pdf"))
    info["quizPages"] = pages
    if pages is None:
        fails.append(f"no readable PDF for the quiz at {quiz_path.with_suffix('.pdf')}")
    elif pages > args.max_quiz_pages:
        fails.append(f"quiz has {pages} pages; the budget is {args.max_quiz_pages}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", help="a2_<L>_fast.tex")
    ap.add_argument("--te", help="a2_<L>_TE.tex (checks Example / Try It numbers and the title)")
    ap.add_argument("--quiz", help="a2_<L>_quiz_fast.tex")
    ap.add_argument("--ixl-map", help="algebra2-live-worksheet/data/ixl-algebra2-skills.json")
    ap.add_argument("--lesson", help="expected lesson key, e.g. 2-1")
    ap.add_argument("--pdf", help="packet PDF (default: next to the .tex)")
    ap.add_argument("--max-examples", type=int, default=2)
    ap.add_argument("--max-pages", type=int, default=4)
    ap.add_argument("--max-quiz-pages", type=int, default=3)
    ap.add_argument("--compile", action="store_true", help="run pdflatex first")
    ap.add_argument("--build-dir", help="pdflatex output directory (default <tex dir>/build)")
    ap.add_argument("--report", help="write the JSON report here too")
    args = ap.parse_args()

    report = {"ok": False, "fails": [], "warns": [], "info": {}}
    check_packet(args, report)
    if args.quiz:
        check_quiz(args, report)
    report["ok"] = not report["fails"]
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.report:
        Path(args.report).write_text(text + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
