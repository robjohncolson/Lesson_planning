r"""Read lessons/L{NN}_P{N}.yaml → emit tex/L{NN}_P{N}_{student,teacher}.tex.

Single shared generator; each lesson becomes a ~200-line YAML config.
Future new-unit onboarding (Algebra 1, APStats) writes YAML + an item
bank; no Python per lesson.

Usage:  python build_lesson_from_yaml.py lessons/L41_P2.yaml

Schema (overview):

  lesson_id: <L{NN}_P{N}>
  title, label, period, cadence
  objectives: [{label, body}]
  framework_header: [{label, body}]  # topic goals / essential Q / materials
  preflight: {title, color, body}    # teacher-only top callout
  phases: {do_now, launch, explore, share_summary, exit} each with
    {framework_tag, dok, minutes, teacher_does[], students_do[],
     questions_to_ask[], adult_role}
  items:
    do_now: [id]
    explore: [{id, label, dok3?, visual?}]
    reinforcement: [{id, label}]
  callouts: [{section, title, color, body}]
  sentence_frames: {section, frames[]}
  exit_ticket: {title, items[]}
  teacher_callouts: [{title, color, body}]  # IEP / ELL / period variants
  chain_callbacks: [{chain, anchor_item, title, body}]
  visuals: {<name>: {kind: pgfplot|tikz_boxes|raw_tikz, ...}}
  section_notes: {do_now|launch|explore|share_summary|exit: str | [str]}
    # emitted as \textit{...}\par immediately after the section banner,
    # before callouts/items; use for free-form "work with a partner..." prose

Content is pulled from questionbank/registry.jsonl by item id.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
REGISTRY = ROOT / "questionbank" / "registry.jsonl"
TEX_DIR = ROOT / "tex"


# ---- Registry access ----------------------------------------------------


def load_registry() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with REGISTRY.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                hint = line[:80] + ("..." if len(line) > 80 else "")
                raise SystemExit(
                    f"registry.jsonl line {lineno}: JSON decode error ({e.msg} at col {e.colno}).\n"
                    f"  first 80 chars: {hint}"
                ) from e
            out[row["id"]] = row
    return out


# ---- Visual renderers ---------------------------------------------------


def render_visual(name: str, spec: dict) -> str:
    kind = spec.get("kind")
    if kind == "pgfplot":
        return render_pgfplot(spec)
    if kind == "tikz_boxes":
        return render_tikz_boxes(spec)
    if kind == "raw_tikz":
        return render_raw_tikz(spec)
    return f"% unknown visual kind: {kind}\n"


def render_raw_tikz(s: dict) -> str:
    """Emit an author-provided TikZ body verbatim.

    Schema: {kind: raw_tikz, body: "<latex>", wrap_center: true|false}
    The body is written inside `\\begin{center}...\\end{center}` when
    wrap_center is true (default).
    """
    body = s.get("body", "").rstrip()
    if s.get("wrap_center", True):
        return "\\begin{center}\n" + body + "\n\\end{center}\n"
    return body + "\n"


def render_pgfplot(s: dict) -> str:
    data = "\n".join(f"  ({x},{y})" for x, y in s.get("data_points", []))
    dom = s.get("curve_domain", [1, 100])
    return (
        "\\begin{center}\n"
        "\\begin{tikzpicture}\n"
        "\\begin{axis}[\n"
        "  width=0.9\\linewidth,\n"
        "  height=2.6in,\n"
        f"  xmin={s['xmin']}, xmax={s['xmax']},\n"
        f"  ymin={s['ymin']}, ymax={s['ymax']},\n"
        f"  xlabel={{{s.get('xlabel','')}}}, ylabel={{{s.get('ylabel','')}}},\n"
        "  grid=major,\n"
        "  tick label style={font=\\small}, label style={font=\\small},\n"
        "  every axis plot/.append style={line width=1pt}\n"
        "]\n"
        f"\\addplot[tealheader, smooth, domain={dom[0]}:{dom[1]}, samples=250] {{{s['curve_expression']}}};\n"
        f"\\addplot[only marks, mark=*, mark size=2.2pt, color=dayblue] coordinates {{\n{data}\n}};\n"
        f"\\node[anchor=south east, font=\\small] at (axis cs:{s['xmax']*0.98},{s['ymax']*0.87}) {{\\({s.get('curve_label','')}\\)}};\n"
        "\\end{axis}\n"
        "\\end{tikzpicture}\n"
        "\\end{center}\n"
    )


def render_tikz_boxes(s: dict) -> str:
    lines = [
        "\\begin{center}",
        "\\begin{tikzpicture}[>=stealth, line width=0.9pt, font=\\small]",
    ]
    node_names = ["a", "b", "c", "d", "e", "f"]
    for i, box in enumerate(s.get("boxes", [])):
        x, y = box["pos"]
        lines.append(
            f"\\node[draw, rounded corners, fill={box.get('fill','frameshade')}, "
            f"minimum width=1.7in, minimum height=0.58in] ({node_names[i]}) "
            f"at ({x},{y}) {{\\textbf{{{box['label']}}}}};"
        )
    arrow = s.get("arrow")
    if arrow:
        lbl = arrow.get("label", "").replace("\\\\", "\\\\")
        lines.append(
            f"\\draw[->, tealheader] ({node_names[0]}.east) -- "
            f"node[above, align=center] {{{lbl}}} ({node_names[1]}.west);"
        )
    for extra in s.get("extra", []):
        x, y = extra["pos"]
        lines.append(
            f"\\node[draw, rounded corners, fill={extra.get('fill','frameshade')}, "
            f"minimum width=2.1in, minimum height=0.6in] at ({x},{y}) {{{extra['label']}}};"
        )
    lines.extend(["\\end{tikzpicture}", "\\end{center}"])
    return "\n".join(lines) + "\n"


# ---- Block renderers ----------------------------------------------------


def objectives_table(rows: list[dict]) -> str:
    header = (
        "\\sectionbanner{OBJECTIVES}\n"
        "{\\small\n"
        "\\renewcommand{\\arraystretch}{1.25}\n"
        "\\noindent\\begin{tabular}{|p{1.8in}|p{4.8in}|}\n\\hline\n"
    )
    body = "".join(
        f"\\textbf{{{r['label']}}} & {r['body']} \\\\ \\hline\n"
        for r in rows
    )
    return header + body + "\\end{tabular}\n}\n\n"


def framework_header_table(rows: list[dict]) -> str:
    header = (
        "\\sectionbanner{TOPIC GOALS / ESSENTIAL QUESTION / MATERIALS}\n"
        "{\\small\n"
        "\\renewcommand{\\arraystretch}{1.25}\n"
        "\\noindent\\begin{tabular}{|p{1.8in}|p{4.8in}|}\n\\hline\n"
    )
    body = "".join(
        f"\\textbf{{{r['label']}}} & {r['body']} \\\\ \\hline\n"
        for r in rows
    )
    return header + body + "\\end{tabular}\n}\n\n"


def callout_block(title: str, color: str, body: str) -> str:
    return (
        f"\\begin{{callout}}{{{title}}}{{{color}}}\n"
        f"{body.rstrip()}\n"
        f"\\end{{callout}}\n\n"
    )


def bulleted(items: list[str]) -> str:
    if not items:
        return ""
    return (
        "\\begin{itemize}[leftmargin=1.5em,itemsep=2pt,topsep=2pt]\n"
        + "".join(f"  \\item {it}\n" for it in items)
        + "\\end{itemize}\n"
    )


def phase_header(name: str, p: dict) -> str:
    label = name.replace("_", " ").title()
    tag = f"\\phasetag{{{p['framework_tag']}}}\n" if p.get("framework_tag") else ""
    return (
        f"{tag}"
        f"\\frameworkphaseheader{{{label}}}{{{p['dok']}}}{{{p['minutes']}}}"
        f"{{%\n{bulleted(p.get('teacher_does', []))}}}"
        f"{{%\n{bulleted(p.get('students_do', []))}}}"
        f"{{%\n{bulleted(p.get('questions_to_ask', []))}}}"
        f"{{{p.get('adult_role', '')}}}\n\n"
    )


def bank_item_block(item_spec: dict, registry: dict, visuals: dict, for_teacher: bool) -> str:
    iid = item_spec["id"]
    q = registry.get(iid, {})
    prompt = q.get("prompt", f"[item {iid} not in registry]")
    answers = q.get("answers") or []
    label = item_spec.get("label", iid)
    out = [f"\\bankitem{{{label}}}{{%"]
    out.append(prompt.strip())
    if item_spec.get("visual") and item_spec["visual"] in visuals:
        out.append(render_visual(item_spec["visual"], visuals[item_spec["visual"]]))
    out.append("}{%")
    if answers:
        for i, a in enumerate(answers):
            out.append(f"  \\answerchoice{{{chr(65 + i)}}}{{{a}}}")
    out.append("}")
    if for_teacher:
        out.append(
            "\\teacheranswerbox{\\IconCheck\\ ANSWER / ANTICIPATED TALK}{%"
        )
        body = (q.get("teacher_answer") or "").strip()
        out.append(body if body else "(no answer key --- verify before class)")
        out.append("}")
    return "\n".join(out) + "\n\n"


def chain_callout_for(anchor_id: str, callbacks: list[dict]) -> str:
    out = []
    for cb in callbacks:
        if cb.get("anchor_item") == anchor_id:
            title = f"\\IconSpeak\\ CHAIN {cb['chain']} CALLBACK --- {cb['title']}"
            out.append(callout_block(title, "calloutpeach", cb["body"]))
    return "".join(out)


# ---- Edition assemblers -------------------------------------------------


def emit_student(lesson: dict, registry: dict) -> str:
    visuals = lesson.get("visuals", {})
    parts = [
        "\\documentclass[11pt]{article}\n\\usepackage{preamble}\n\n",
        "\\newcommand{\\phasetag}[1]{{\\small\\itshape Tag: #1\\par}}\n\n",
        "\\begin{document}\n\n",
        f"\\packetheading{{{lesson['label']} \\textperiodcentered\\ Student Packet}}{{{lesson['title']}}}\n\n",
        objectives_table(lesson["objectives"]),
        framework_header_table(lesson["framework_header"]),
    ]

    # Callouts and items grouped by section, in canonical section order.
    section_order = ["do_now", "launch", "explore", "share_summary", "exit"]
    section_labels = {
        "do_now": "DO NOW",
        "launch": "LAUNCH",
        "explore": "EXPLORE",
        "share_summary": "SHARE / SUMMARY",
        "exit": "EXIT",
    }
    callouts_by_section: dict[str, list[dict]] = {s: [] for s in section_order}
    for c in lesson.get("callouts", []):
        callouts_by_section.setdefault(c["section"], []).append(c)

    items = lesson.get("items", {})
    do_now_ids = items.get("do_now", [])
    explore_items = items.get("explore", [])

    section_notes = lesson.get("section_notes", {}) or {}

    def _notes(name: str) -> str:
        val = section_notes.get(name)
        if not val:
            return ""
        if isinstance(val, list):
            return "".join(f"\\textit{{{line}}}\\par\n" for line in val) + "\n"
        return f"\\textit{{{val}}}\\par\n\n"

    # DO NOW
    if callouts_by_section.get("do_now") or do_now_ids:
        parts.append(f"\\sectionbanner{{{section_labels['do_now']}}}\n\n")
        parts.append(_notes("do_now"))
        for c in callouts_by_section.get("do_now", []):
            parts.append(callout_block(c["title"], c["color"], c["body"]))
        for iid in do_now_ids:
            parts.append(bank_item_block({"id": iid, "label": f"Do Now"}, registry, visuals, for_teacher=False))

    # LAUNCH
    parts.append(f"\\sectionbanner{{{section_labels['launch']}}}\n\n")
    parts.append(_notes("launch"))
    for c in callouts_by_section.get("launch", []):
        parts.append(callout_block(c["title"], c["color"], c["body"]))

    # EXPLORE
    parts.append(f"\\sectionbanner{{{section_labels['explore']}}}\n\n")
    parts.append(_notes("explore"))
    if explore_items:
        parts.append("\\textbf{Bank-item labels (in order):}\n")
        parts.append("\\begin{enumerate}[leftmargin=1.6em,itemsep=2pt,topsep=2pt]\n")
        for it in explore_items:
            parts.append(f"  \\item {it['label']}\n")
        parts.append("\\end{enumerate}\n\n")
        for it in explore_items:
            parts.append(bank_item_block(it, registry, visuals, for_teacher=False))

    # SHARE / SUMMARY
    parts.append(f"\\sectionbanner{{{section_labels['share_summary']}}}\n\n")
    parts.append(_notes("share_summary"))
    for c in callouts_by_section.get("share_summary", []):
        parts.append(callout_block(c["title"], c["color"], c["body"]))
    sf = lesson.get("sentence_frames")
    if sf:
        parts.append("\\begin{sentenceframebox}\n\\textbf{Sentence frames}\n\n")
        for f in sf.get("frames", []):
            parts.append(f"{f}\n\n")
        parts.append("\\end{sentenceframebox}\n\n")

    # EXIT
    exit_t = lesson.get("exit_ticket")
    if exit_t:
        parts.append(f"\\sectionbanner{{{section_labels['exit']}}}\n\n")
        parts.append(_notes("exit"))
        parts.append(f"\\begin{{summaryexitbox}}{{{exit_t['title']}}}\n")
        for it in exit_t["items"]:
            parts.append(f"{it}\n\n")
        parts.append("\\end{summaryexitbox}\n\n")

    # Optional reinforcement
    reinf = items.get("reinforcement", [])
    if reinf:
        parts.append("\\clearpage\n\n")
        parts.append("\\sectionbanner{OPTIONAL REINFORCEMENT (not collected)}\n\n")
        for it in reinf:
            parts.append(bank_item_block(it, registry, visuals, for_teacher=False))

    parts.append("\\end{document}\n")
    return "".join(parts)


def emit_teacher(lesson: dict, registry: dict) -> str:
    visuals = lesson.get("visuals", {})
    callbacks = lesson.get("chain_callbacks", [])
    parts = [
        "\\documentclass[11pt]{article}\n\\usepackage{preamble}\n\n",
        "\\newcommand{\\IconCheck}{[CHECK]}\n",
        "\\newcommand{\\phasetag}[1]{{\\small\\itshape Tag: #1\\par}}\n",
        "\\newcommand{\\teacheranswerbox}[2]{\\begin{callout}{#1}{calloutgreen}#2\\end{callout}}\n\n",
        "\\begin{document}\n\n",
        f"\\packetheading{{{lesson['label']} \\textperiodcentered\\ Teacher Edition}}{{{lesson['title']}}}\n\n",
        objectives_table(lesson["objectives"]),
        framework_header_table(lesson["framework_header"]),
    ]

    # Preflight at top of teacher body
    pf = lesson.get("preflight")
    if pf:
        parts.append(callout_block(f"\\IconPin\\ {pf['title']}", pf.get("color", "calloutpink"), pf["body"]))

    phases = lesson.get("phases", {})
    callouts_by_section: dict[str, list[dict]] = {}
    for c in lesson.get("callouts", []):
        callouts_by_section.setdefault(c["section"], []).append(c)

    items = lesson.get("items", {})

    phase_order = [
        ("do_now", items.get("do_now", [])),
        ("launch", []),
        ("explore", items.get("explore", [])),
        ("share_summary", []),
        ("exit", []),
    ]

    section_notes = lesson.get("section_notes", {}) or {}

    def _notes(name: str) -> str:
        val = section_notes.get(name)
        if not val:
            return ""
        if isinstance(val, list):
            return "".join(f"\\textit{{{line}}}\\par\n" for line in val) + "\n"
        return f"\\textit{{{val}}}\\par\n\n"

    for phase_name, phase_items in phase_order:
        ph = phases.get(phase_name)
        if ph:
            parts.append(phase_header(phase_name, ph))
        parts.append(_notes(phase_name))
        for c in callouts_by_section.get(phase_name, []):
            parts.append(callout_block(c["title"], c["color"], c["body"]))
        for it in phase_items:
            spec = {"id": it, "label": f"{phase_name.replace('_',' ').title()}"} if isinstance(it, str) else it
            parts.append(chain_callout_for(spec["id"], callbacks))
            parts.append(bank_item_block(spec, registry, visuals, for_teacher=True))
        if phase_name == "share_summary":
            sf = lesson.get("sentence_frames")
            if sf:
                parts.append("\\begin{sentenceframebox}\n\\textbf{Sentence frames}\n\n")
                for f in sf.get("frames", []):
                    parts.append(f"{f}\n\n")
                parts.append("\\end{sentenceframebox}\n\n")
        if phase_name == "exit":
            exit_t = lesson.get("exit_ticket")
            if exit_t:
                parts.append(f"\\begin{{summaryexitbox}}{{{exit_t['title']}}}\n")
                for it in exit_t["items"]:
                    parts.append(f"{it}\n\n")
                parts.append("\\end{summaryexitbox}\n\n")

    # Optional reinforcement
    reinf = items.get("reinforcement", [])
    if reinf:
        parts.append("\\clearpage\n\n")
        parts.append("\\sectionbanner{OPTIONAL REINFORCEMENT (not collected)}\n\n")
        for it in reinf:
            parts.append(bank_item_block(it, registry, visuals, for_teacher=True))

    # Trailing teacher callouts (IEP / ELL / period variants)
    tc = lesson.get("teacher_callouts", [])
    if tc:
        parts.append("\\clearpage\n\n")
        for c in tc:
            parts.append(callout_block(c["title"], c.get("color", "calloutpink"), c["body"]))

    parts.append("\\end{document}\n")
    return "".join(parts)


# ---- Main ---------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("yaml_path", help="path to lessons/L{NN}_P{N}.yaml")
    p.add_argument("--edition", choices=("student", "teacher", "both"), default="both")
    args = p.parse_args()

    lesson_path = Path(args.yaml_path)
    lesson = yaml.safe_load(lesson_path.read_text(encoding="utf-8"))
    lesson_id = lesson["lesson_id"]
    registry = load_registry()

    TEX_DIR.mkdir(exist_ok=True)

    if args.edition in ("student", "both"):
        out = emit_student(lesson, registry)
        (TEX_DIR / f"{lesson_id}_student.tex").write_text(out, encoding="utf-8")
        print(f"wrote tex/{lesson_id}_student.tex ({len(out)} chars)")
    if args.edition in ("teacher", "both"):
        out = emit_teacher(lesson, registry)
        (TEX_DIR / f"{lesson_id}_teacher.tex").write_text(out, encoding="utf-8")
        print(f"wrote tex/{lesson_id}_teacher.tex ({len(out)} chars)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
