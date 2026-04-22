"""Walk every build_L*_P*_packets.py and emit graph/eye_check/L{NN}_P{N}.md.

Each output file is a structured "intent anchor" brief: the bits a LaTeX
(or any non-docx) rewrite MUST preserve verbatim — phase headers,
callouts, sentence frames, bank-item ordering, visual requirements,
period variants, teacher-edition deltas.

Codex (or a human) can use the brief as the spec for a target-format
rewrite; the original Word output is the reference rendering.

Usage:  python extract_intent_anchors.py
Writes: graph/eye_check/L{NN}_P{N}.md  (one per builder)
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
BUILDERS_GLOB = "build_L*_packets.py"
OUT_DIR = ROOT / "graph" / "eye_check"
OPERATIONAL = ROOT / "tagging" / "operational_ids.json"


# ---- AST literal helpers -------------------------------------------------


def lit(node):
    """Best-effort literal extraction: returns the value if literal, else
    a placeholder string showing the source expression."""
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [lit(e) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(lit(e) for e in node.elts)
    if isinstance(node, ast.Name):
        return f"<{node.id}>"
    if isinstance(node, ast.JoinedStr):  # f-string
        return "".join(lit(v) if not isinstance(v, ast.FormattedValue)
                       else f"{{{ast.unparse(v.value)}}}" for v in node.values)
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return ast.unparse(node)


def kw_dict(call: ast.Call) -> dict:
    return {kw.arg: lit(kw.value) for kw in call.keywords if kw.arg}


def get_module_constants(tree: ast.Module) -> dict:
    """Pull module-level assignments for LESSON_TITLE, LESSON_LABEL, OBJECTIVES,
    FRAMEWORK_HEADER, and any *_IDS lists."""
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name):
                out[tgt.id] = lit(node.value)
    return out


# ---- Per-call extractors -------------------------------------------------


def call_qualname(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
        return f"{f.value.id}.{f.attr}"
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return "?"


def extract_call(call: ast.Call) -> dict | None:
    """Recognize the call shapes that matter for intent. Returns a dict
    or None to skip."""
    name = call_qualname(call)
    args_pos = [lit(a) for a in call.args]
    kw = kw_dict(call)

    if name == "ps.framework_phase_header":
        return {"kind": "phase_header",
                "phase": kw.get("phase"),
                "framework_tag": kw.get("framework_tag"),
                "dok": kw.get("dok"),
                "minutes": kw.get("minutes"),
                "teacher_does": kw.get("teacher_does"),
                "students_do": kw.get("students_do"),
                "questions_to_ask": kw.get("questions_to_ask"),
                "adult_role": kw.get("adult_role")}

    if name == "add_callout":
        return {"kind": "callout",
                "title": args_pos[1] if len(args_pos) > 1 else kw.get("title"),
                "body": args_pos[2] if len(args_pos) > 2 else kw.get("body_lines"),
                "color_hex": kw.get("color_hex", "CFE2F3")}

    if name == "bank_item_block":
        return {"kind": "bank_item",
                "label": kw.get("label"),
                "space_after_inches": kw.get("space_after_inches")}

    if name == "ps.teal_section":
        return {"kind": "section",
                "title": args_pos[1] if len(args_pos) > 1 else None,
                "body": args_pos[2] if len(args_pos) > 2 else []}

    if name == "ps.sentence_frame_box":
        return {"kind": "sentence_frames",
                "frames": args_pos[1] if len(args_pos) > 1 else []}

    if name == "ps.summary_exit_box":
        return {"kind": "exit_box",
                "title": args_pos[1] if len(args_pos) > 1 else None,
                "items": args_pos[2] if len(args_pos) > 2 else []}

    if name in ("doc.add_page_break", "doc.add_paragraph"):
        return None  # cosmetic

    if name == "doc.save":
        return None

    if name == "qb.get_for_packet":
        return {"kind": "fetch_items",
                "from_var": ast.unparse(call.args[0]) if call.args else None}

    return None


def walk_function(func: ast.FunctionDef) -> list[dict]:
    """Collect interesting calls in source order. Also detect `labels = [...]`
    list assignments and inject them as 'label_list' entries so loop-driven
    bank_item_block calls show real labels instead of `<label>`."""
    out = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and tgt.id in ("labels", "LABELS"):
                val = lit(node.value)
                if isinstance(val, list):
                    out.append({"kind": "label_list",
                                "labels": val,
                                "_lineno": node.lineno})
        if isinstance(node, ast.Call):
            ext = extract_call(node)
            if ext:
                ext["_lineno"] = node.lineno
                out.append(ext)
    out.sort(key=lambda d: d["_lineno"])
    return out


# ---- Markdown emission ---------------------------------------------------


def fmt_lines(items, indent: str = "  ") -> str:
    if items is None:
        return f"{indent}_(none)_"
    if isinstance(items, str):
        items = [items]
    if isinstance(items, (list, tuple)):
        if not items:
            return f"{indent}_(empty)_"
        return "\n".join(f"{indent}- {x}" for x in items)
    return f"{indent}{items}"


def render_phase(c: dict) -> list[str]:
    out = [f"### Phase: **{c['phase']}**  ·  DOK {c['dok']}  ·  {c['minutes']} min"]
    if c.get("framework_tag"):
        out.append(f"_Tag: {c['framework_tag']}_")
    out.append("")
    out.append(f"**Teacher does:**")
    out.append(fmt_lines(c.get("teacher_does")))
    out.append(f"**Students do:**")
    out.append(fmt_lines(c.get("students_do")))
    if c.get("questions_to_ask"):
        out.append(f"**Questions to ask:**")
        out.append(fmt_lines(c["questions_to_ask"]))
    if c.get("adult_role"):
        out.append(f"**Adult role:** {c['adult_role']}")
    out.append("")
    return out


def render_callout(c: dict) -> list[str]:
    return [f"> **CALLOUT** — {c.get('title','?')}  _(color: #{c.get('color_hex','?')})_",
            "> ",
            *(f"> {line}" for line in (c.get("body") or [])),
            ""]


def render_section(c: dict) -> list[str]:
    out = [f"## SECTION — {c.get('title','?')}"]
    body = c.get("body") or []
    if body:
        out.append("")
        for line in body:
            out.append(f"_{line}_")
    out.append("")
    return out


def render_sentence_frames(c: dict) -> list[str]:
    out = ["**Sentence frames:**"]
    for f in c.get("frames", []):
        out.append(f"- {f}")
    out.append("")
    return out


def render_exit_box(c: dict) -> list[str]:
    out = [f"**Exit ticket — {c.get('title','?')}:**"]
    for it in c.get("items", []):
        out.append(f"- {it}")
    out.append("")
    return out


def render_bank_item(c: dict, ids_iter: list[str]) -> list[str]:
    label = c.get("label") or "(no label)"
    return [f"- **Item:** {label}", ""]


def render_function_block(name: str, calls: list[dict]) -> list[str]:
    out = [f"## `{name}`", ""]
    bank_idx = 0
    for c in calls:
        kind = c["kind"]
        if kind == "phase_header":
            out.extend(render_phase(c))
        elif kind == "callout":
            out.extend(render_callout(c))
        elif kind == "section":
            out.extend(render_section(c))
        elif kind == "sentence_frames":
            out.extend(render_sentence_frames(c))
        elif kind == "exit_box":
            out.extend(render_exit_box(c))
        elif kind == "bank_item":
            out.extend(render_bank_item(c, []))
            bank_idx += 1
        elif kind == "fetch_items":
            out.append(f"_(fetches items from `{c['from_var']}`)_")
            out.append("")
        elif kind == "label_list":
            out.append("**Bank-item labels (in order):**")
            for lbl in c["labels"]:
                out.append(f"  1. {lbl}")
            out.append("")
    return out


# ---- Visuals checklist parse --------------------------------------------


def load_visuals(prefix: str) -> list[str]:
    p = ROOT / f"{prefix}_Visuals_Checklist.md"
    if not p.exists():
        return []
    return [line for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("-")]


# ---- Main ---------------------------------------------------------------


def builder_prefix(name: str) -> str:
    m = re.match(r"build_(L\d+_P\d+)_packets\.py", name)
    return m.group(1) if m else name


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    operational = json.loads(OPERATIONAL.read_text(encoding="utf-8"))

    written = []
    for builder in sorted(ROOT.glob(BUILDERS_GLOB)):
        prefix = builder_prefix(builder.name)
        src = builder.read_text(encoding="utf-8")
        tree = ast.parse(src)
        consts = get_module_constants(tree)

        per_func: dict[str, list[dict]] = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in (
                    "build_do_now", "build_student", "build_teacher"):
                per_func[node.name] = walk_function(node)

        info = operational.get(builder.name, {})
        annotations = info.get("annotations", {})
        ids = info.get("ids", {})
        visuals = load_visuals(prefix)

        out_lines: list[str] = [
            f"# Eye-Check Intent Anchors — {prefix}",
            "",
            f"**Source builder:** `{builder.name}`",
            f"**Lesson title:** {consts.get('LESSON_TITLE','?')}",
            f"**Lesson label:** {consts.get('LESSON_LABEL','?')}",
            "",
            "_This file captures the structural intent of the docx packet so a "
            "rewrite in another format (LaTeX, HTML, etc.) can preserve every "
            "anchor a teacher or evaluator would notice. Do not interpret — "
            "preserve._",
            "",
            "---",
            "",
            "## Objectives",
            "",
        ]
        for label, body in (consts.get("OBJECTIVES") or []):
            out_lines.append(f"- **{label}:** {body}")
        out_lines.append("")
        out_lines.append("## Framework Header (Topic Goals / Essential Q / Materials)")
        out_lines.append("")
        for label, body in (consts.get("FRAMEWORK_HEADER") or []):
            out_lines.append(f"- **{label}:** {body}")
        out_lines.append("")

        out_lines.append("## Operational ID lists (with builder annotations)")
        out_lines.append("")
        for key in ("DO_NOW_IDS", "DO_NOW_ID", "LAUNCH_IDS", "LAUNCH_ID",
                    "EXPLORE_IDS", "PRACTICE_IDS",
                    "REINFORCE_IDS", "DOK3_ID", "DOK3_PAIR_ID"):
            if key in ids:
                vals = ids[key]
                out_lines.append(f"- **{key}** ({len(vals)}):")
                for v in vals:
                    note = annotations.get(v)
                    if note:
                        out_lines.append(f"    - `{v}` — {note}")
                    else:
                        out_lines.append(f"    - `{v}`")
        out_lines.append("")

        if visuals:
            out_lines.append("## Visual requirements")
            out_lines.append("")
            out_lines.extend(visuals)
            out_lines.append("")

        out_lines.append("---")
        out_lines.append("")
        out_lines.append("# Packet body (in render order)")
        out_lines.append("")

        for fn_name in ("build_do_now", "build_student", "build_teacher"):
            calls = per_func.get(fn_name)
            if not calls:
                continue
            out_lines.extend(render_function_block(fn_name, calls))
            out_lines.append("---")
            out_lines.append("")

        out_lines.append("## Brief for rewriter (Codex / human)")
        out_lines.append("")
        out_lines.append("**Must preserve:**")
        out_lines.append("- All callout titles AND body lines verbatim (these are 'rules printed on the page').")
        out_lines.append("- All framework_phase_header content (DOK, minutes, teacher_does, students_do, questions_to_ask, adult_role) — evaluators look for these.")
        out_lines.append("- All sentence frames verbatim — ELL non-negotiable.")
        out_lines.append("- Bank-item ordering AND labels exactly as listed.")
        out_lines.append("- All visual placeholders (see Visual requirements above).")
        out_lines.append("- Section ordering: Do Now → Launch → Explore → Share/Summary → Exit → (back) Optional Reinforcement.")
        out_lines.append("- Period variant notes (look for 'Period F', 'Wed-F', '45-min', 'COMPRESSED' callouts).")
        out_lines.append("- Teacher-edition extras (PRE-FLIGHT pre-flight callouts, MODIFICATIONS / IEP / ELL support callouts, answer-key inclusion).")
        out_lines.append("")
        out_lines.append("**May restructure:**")
        out_lines.append("- Margin sizes, font choices, table styling — match docx visual hierarchy but format-native idioms are fine.")
        out_lines.append("- Table-vs-list rendering of objectives/framework header — preserve content, choose presentation.")
        out_lines.append("- Color hex values — use closest equivalent in target format's palette if exact hex isn't natural.")
        out_lines.append("")
        out_lines.append("**Reference rendering:** the existing `" + prefix + "_{Do_Now,Student_Packet,Teacher_Packet}.docx` files are the canonical visual reference.")
        out_lines.append("")

        out_path = OUT_DIR / f"{prefix}.md"
        out_path.write_text("\n".join(out_lines), encoding="utf-8")
        written.append(out_path.name)

    print(f"Wrote {len(written)} eye-check anchor briefs to {OUT_DIR.relative_to(ROOT)}/:")
    for f in written:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
