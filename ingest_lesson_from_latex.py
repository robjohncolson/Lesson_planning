"""Parse a Gemini-emitted Savvas-source LaTeX file into registry-ready JSON.

Upstream prompt: `gemini_prompts/savvas_lesson_to_latex.md` (or the inline
prompt in the continuation docs). Gemini wraps each structural block
(Example, Try It, Practice, TE addendum, etc.) in a custom environment so
this parser can extract them without a full LaTeX parser.

Workflow:
    python ingest_lesson_from_latex.py source/4-3_savvas_source.tex
    # writes:
    #   questionbank/calibration/4-3.json  (from lesson-meta + item-analysis)
    #   skeletons/4-3_from_latex.json       (batch JSON for qb_append.py)

    # user reviews the batch file, then:
    python qb_append.py --dry-run skeletons/4-3_from_latex.json
    python qb_append.py         skeletons/4-3_from_latex.json

The parser is deliberately forgiving: if a block is malformed it prints a
warning and skips, rather than aborting. Goal is to get 80%+ of a lesson
through the pipe without hand editing, then let the user clean up tails.

USAGE FLAGS
    --dry-run       Print extraction summary; don't write any files.
    --no-calibration Don't overwrite existing calibration file.
    --outdir DIR    Override output dir for skeletons (default: skeletons/).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
CALIBRATION_DIR = ROOT / "questionbank" / "calibration"
SKELETONS_DIR = ROOT / "skeletons"


# ─────────────────────────────────────────────────────────────────────────
# LaTeX → plain text helpers
# ─────────────────────────────────────────────────────────────────────────

MATH_SUBSTITUTIONS = [
    # Nested-brace \frac: repeatedly apply innermost-first
    (r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)"),
    (r"\\sqrt\{([^{}]+)\}", r"√(\1)"),
    # LaTeX escapes
    (r"\\&", r"&"),
    (r"\\%", r"%"),
    (r"\\\$", r"$"),
    (r"\\#", r"#"),
    (r"\\_", r"_"),
    # \left / \right are invisible delimiters
    (r"\\left\[", r"["),
    (r"\\right\]", r"]"),
    (r"\\left\(", r"("),
    (r"\\right\)", r")"),
    (r"\\left\|", r"|"),
    (r"\\right\|", r"|"),
    (r"\\left\\{", r"{"),
    (r"\\right\\}", r"}"),
    (r"\\cdot", r"·"),
    (r"\\times", r"×"),
    (r"\\pm", r"±"),
    (r"\\neq", r"≠"),
    (r"\\leq", r"≤"),
    (r"\\geq", r"≥"),
    (r"\\approx", r"≈"),
    (r"\\infty", r"∞"),
    (r"\\pi", r"π"),
    (r"\\to", r"→"),
    (r"\\rightarrow", r"→"),
    (r"\\leftarrow", r"←"),
    (r"\\ldots", r"..."),
    (r"\\dots", r"..."),
]

# Commands to strip entirely (structural, not content)
STRIP_COMMANDS = [
    r"\\textbf\{([^{}]*)\}",
    r"\\textit\{([^{}]*)\}",
    r"\\emph\{([^{}]*)\}",
    r"\\underline\{([^{}]*)\}",
    r"\\text\{([^{}]*)\}",
    r"\\mathrm\{([^{}]*)\}",
    r"\\mathbf\{([^{}]*)\}",
    r"\\phantom\{([^{}]*)\}",
]

# Commands to remove with their argument (not content-bearing)
DROP_COMMANDS = [
    r"\\label\{[^{}]*\}",
    r"\\hspace\{[^{}]*\}",
    r"\\vspace\{[^{}]*\}",
    r"\\quad",
    r"\\qquad",
    r"\\noindent",
    r"\\medskip",
    r"\\bigskip",
    r"\\smallskip",
    r"\\par",
    r"\\newline",
    r"\\\\",
]


def strip_answer_and_te(body: str) -> str:
    """Remove \\answer{} and \\te{} blocks — they're captured separately."""
    body = re.sub(r"\\answer\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "", body, flags=re.DOTALL)
    body = re.sub(r"\\te\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "", body, flags=re.DOTALL)
    return body


def resolve_uncertain(body: str) -> tuple[str, list[tuple[str, str]]]:
    """\\uncertain{best}{alts} → best + record (best, alts) for notes."""
    flags: list[tuple[str, str]] = []

    def collect(m: re.Match) -> str:
        best, alts = m.group(1).strip(), m.group(2).strip()
        flags.append((best, alts))
        return best

    body = re.sub(r"\\uncertain\{([^{}]*)\}\{([^{}]*)\}", collect, body)
    return body, flags


def strip_placeholders(body: str) -> tuple[str, list[tuple[str, str]]]:
    """\\placeholder{type}{description} → description + record type."""
    phs: list[tuple[str, str]] = []

    def collect(m: re.Match) -> str:
        vtype, desc = m.group(1).strip(), m.group(2).strip()
        phs.append((vtype, desc))
        return f"[IMAGE: {desc}]"

    body = re.sub(r"\\placeholder\{([^{}]*)\}\{([^{}]*)\}", collect, body, flags=re.DOTALL)
    return body, phs


def latex_body_to_text(body: str, *, preserve_tables: bool = True) -> str:
    """Convert a LaTeX block to reasonable plain text for the registry prompt."""
    # Remove answer / te blocks (captured elsewhere)
    body = strip_answer_and_te(body)

    # Protect escaped LaTeX characters before math-delimiter strip eats them
    PROTECT = [("\\$", "\x00DOL\x00"), ("\\&", "\x00AMP\x00"),
               ("\\%", "\x00PCT\x00"), ("\\#", "\x00HSH\x00")]
    for src, dst in PROTECT:
        body = body.replace(src, dst)

    # Math-mode delimiters — just strip them; content remains
    body = body.replace("\\(", "").replace("\\)", "")
    body = body.replace("\\[", "").replace("\\]", "")
    body = re.sub(r"\$\$([^$]*)\$\$", r"\1", body)
    body = re.sub(r"\$([^$]*)\$", r"\1", body)

    # Restore escaped chars
    for src, dst in PROTECT:
        body = body.replace(dst, src[1:])  # strip the backslash

    # Math substitutions — iterate \frac up to 4 times for nested fractions
    frac_pattern = r"\\frac\{([^{}]+)\}\{([^{}]+)\}"
    for _ in range(4):
        new_body = re.sub(frac_pattern, r"(\1)/(\2)", body)
        if new_body == body:
            break
        body = new_body
    for pattern, replacement in MATH_SUBSTITUTIONS:
        if pattern == r"\\frac\{([^{}]+)\}\{([^{}]+)\}":
            continue  # already iterated above
        body = re.sub(pattern, replacement, body)

    # Strip formatting commands (keep inner content)
    for pattern in STRIP_COMMANDS:
        body = re.sub(pattern, r"\1", body)

    # Drop empty / structural commands
    for pattern in DROP_COMMANDS:
        body = re.sub(pattern, " ", body)

    # Tabular environments: leave inline but simplify
    if preserve_tables:
        body = simplify_tabular(body)
    else:
        body = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", "[TABLE]", body, flags=re.DOTALL)

    # tikzpicture: summarize
    body = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
                  "[GRAPH / TIKZ figure]", body, flags=re.DOTALL)

    # Collapse whitespace
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def simplify_tabular(body: str) -> str:
    """Turn \\begin{tabular}{...}...\\end{tabular} into a compact text table."""
    def replace(m: re.Match) -> str:
        inner = m.group(1)
        # Drop the column spec — it's the {|c|c|} bit after \begin{tabular}
        inner = re.sub(r"^\{[^}]+\}", "", inner)
        # Rows delimited by \\
        rows = re.split(r"\\\\\s*", inner)
        cleaned = []
        for row in rows:
            row = re.sub(r"\\hline", "", row)
            cells = [c.strip() for c in row.split("&") if c.strip()]
            if cells:
                cleaned.append(" | ".join(cells))
        if not cleaned:
            return "[TABLE]"
        return "TABLE:\n  " + "\n  ".join(cleaned) + "\nEND_TABLE"

    return re.sub(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", replace, body, flags=re.DOTALL)


def detect_visual_type(body: str) -> tuple[str, bool]:
    """Return (visual_type, needs_cleanup). Detection order matters — placeholders win."""
    if re.search(r"\\placeholder\{photo\}", body):
        return "photo", True
    if re.search(r"\\placeholder\{map\}", body):
        return "map", True
    if re.search(r"\\placeholder\{diagram\}", body):
        return "diagram", True
    if re.search(r"\\placeholder\{illustration\}", body):
        return "photo", True
    if re.search(r"\\begin\{tikzpicture\}", body):
        return "graph", False
    if re.search(r"\\begin\{tabular\}", body):
        return "table", False
    return "none", False


def extract_answer(body: str) -> Optional[str]:
    """Return the \\answer{...} content from a block, or None if absent."""
    m = re.search(r"\\answer\{((?:[^{}]|\{[^{}]*\})*)\}", body, flags=re.DOTALL)
    if not m:
        return None
    inner = m.group(1).strip()
    return latex_body_to_text(inner)


# ─────────────────────────────────────────────────────────────────────────
# Environment extraction
# ─────────────────────────────────────────────────────────────────────────


def find_blocks(tex: str, env_name: str, arg_count: int = 0) -> list[tuple[list[str], str]]:
    """Find all \\begin{env}{arg1}{arg2}...body...\\end{env} blocks.

    Returns list of (args, body) tuples.
    """
    arg_pattern = r"\{([^{}]*)\}" * arg_count
    pattern = rf"\\begin\{{{re.escape(env_name)}\}}{arg_pattern}(.*?)\\end\{{{re.escape(env_name)}\}}"
    out = []
    for m in re.finditer(pattern, tex, flags=re.DOTALL):
        args = list(m.groups()[:arg_count])
        body = m.groups()[arg_count]
        out.append((args, body))
    return out


def expand_item_list(items_str: str) -> list[int]:
    """Parse '11, 14--16, 19' → [11, 14, 15, 16, 19]. Handles en-dash ranges."""
    # Normalize en-dash / em-dash variants to --
    items_str = items_str.replace("–", "--").replace("—", "--")
    items_str = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", items_str)
    out = []
    for chunk in items_str.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r"(\d+)\s*--\s*(\d+)", chunk)
        if m:
            out.extend(range(int(m.group(1)), int(m.group(2)) + 1))
        elif chunk.isdigit():
            out.append(int(chunk))
    return out


def parse_item_analysis_table(body: str) -> dict[str, dict[str, list[int]]]:
    """Find Example × DOK mapping in the transcribed table.

    Handles several formats:
    - Savvas tabular: rows ending in \\\\, cells separated by &
    - Text rows: 'Example N | items | DOK' or 'N | items | DOK'
    - En-dash ranges like '14--16' → expanded to [14, 15, 16]

    Returns dict: {"example_1": {"dok1": [9, 14, 15], "dok2": [10]}, ...}.
    """
    out: dict[str, dict[str, list[int]]] = {}

    def record(ex_num: int, items: list[int], dok: int) -> None:
        if not items:
            return
        key = f"example_{ex_num}"
        dok_key = f"dok{dok}"
        out.setdefault(key, {}).setdefault(dok_key, []).extend(items)

    # Strategy 1: parse as a Savvas tabular (rows end \\, cells sep by &)
    rows = re.split(r"\\\\\s*", body)
    for row in rows:
        # Strip rule commands and headers
        row = re.sub(r"\\(?:hline|toprule|midrule|bottomrule)\b", "", row)
        row = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", row)
        cells = [c.strip() for c in row.split("&")]
        if len(cells) < 3:
            continue
        # Skip header rows
        if any(re.search(r"Example|Items|DOK", c, re.I) and not re.search(r"\d", c) for c in cells):
            continue
        # Try to interpret as (ex_num, items, dok)
        first = cells[0].strip()
        last = cells[-1].strip()
        middle = " ".join(cells[1:-1])
        if first.isdigit() and last.isdigit() and int(last) in (1, 2, 3, 4):
            items = expand_item_list(middle)
            record(int(first), items, int(last))

    # Strategy 2 (fallback): text pattern "Example N | items | DOK"
    if not out:
        for m in re.finditer(r"Example\s+(\d+)[^\d\n]*?([\d, \-–]+)[^\d\n]+?([1-4])(?:\s|$)",
                             body, re.IGNORECASE):
            record(int(m.group(1)), expand_item_list(m.group(2)), int(m.group(3)))

    # Strategy 3 (fallback): pipe-delimited text rows
    if not out:
        for row in re.finditer(r"(\d+)\s*\|\s*([\d,\s\-–]+)\s*\|\s*([1-4])", body):
            record(int(row.group(1)), expand_item_list(row.group(2)), int(row.group(3)))

    return out


def anchor_example_for_practice(item_analysis: dict, practice_num: int) -> Optional[int]:
    """Given the item_analysis dict and a Practice item #, find which Example anchors it."""
    for ex_key, dok_map in item_analysis.items():
        if not ex_key.startswith("example_"):
            continue
        for _, items in dok_map.items():
            if practice_num in items:
                return int(ex_key.removeprefix("example_"))
    return None


def dok_for_practice(item_analysis: dict, practice_num: int) -> Optional[int]:
    """Find the DOK for a practice item # from the item_analysis table.
    Returns None if not found (caller falls back to inline-declared DOK)."""
    for _, dok_map in item_analysis.items():
        for dok_key, items in dok_map.items():
            if practice_num in items:
                return int(dok_key.removeprefix("dok"))
    return None


# ─────────────────────────────────────────────────────────────────────────
# Calibration generator
# ─────────────────────────────────────────────────────────────────────────


def parse_lesson_meta(body: str) -> dict:
    """Extract lesson code, title, objective, EQ, vocab from \\begin{lesson-meta}.

    Handles two formats:
    1. Explicit keys:   lesson: 4-3\\ntitle: ...\\nobjective: ...
    2. Natural Savvas:  \\textbf{4-3 Title}\\n\\textbf{I CAN...} ...\\n\\textbf{VOCABULARY}...
    """
    meta = {}

    def grab(pattern: str) -> Optional[str]:
        m = re.search(pattern, body, flags=re.DOTALL | re.IGNORECASE)
        return latex_body_to_text(m.group(1)).strip() if m else None

    # --- Format 1: explicit keys (lesson: X-Y, title: ...) ---
    meta["lesson"] = grab(r"(?:^|\n)\s*lesson\s*[:=]\s*([^\n]+)")
    meta["title"] = grab(r"(?:^|\n)\s*title\s*[:=]\s*([^\n]+)")
    meta["objective"] = grab(r"(?:^|\n)\s*objective\s*[:=]\s*(.*?)(?:\n\n|$)")
    meta["essential_question"] = grab(r"essential[\s-]*question\s*[:=]\s*(.*?)(?:\n\n|$)")

    # --- Format 2: natural Savvas formatting (fallback) ---
    # Lesson code + title from first \textbf{...} (e.g., "4-3 Multiplying and Dividing...")
    if not meta.get("title"):
        m = re.search(r"\\textbf\{\s*(\d+-\d+)?\s*([^{}]*)\}", body)
        if m:
            if not meta.get("lesson"):
                meta["lesson"] = m.group(1)
            meta["title"] = m.group(2).strip()

    # "I CAN..." as objective
    if not meta.get("objective"):
        m = re.search(r"I\s*CAN\.*\.*\s*\}?\s*(.*?)(?:\n\s*\\textbf|\n\n|$)",
                      body, flags=re.DOTALL | re.IGNORECASE)
        if m:
            obj = m.group(1).strip()
            obj = latex_body_to_text(obj).strip().rstrip(".")
            meta["objective"] = obj

    # ESSENTIAL QUESTION from \textbf block
    if not meta.get("essential_question"):
        m = re.search(r"ESSENTIAL\s+QUESTION\s*\}?\s*(.*?)(?:\n\s*\\textbf|\n\n|\\end|$)",
                      body, flags=re.DOTALL | re.IGNORECASE)
        if m:
            eq = latex_body_to_text(m.group(1)).strip()
            meta["essential_question"] = eq

    # Vocab from \textbf{VOCABULARY} block, picks up \item entries
    vocab_m = re.search(
        r"\\textbf\{\s*VOCABULARY[^{}]*\}(.*?)(?:\\textbf\{|\\end\{lesson-meta|\Z)",
        body, flags=re.DOTALL | re.IGNORECASE)
    if vocab_m:
        block = vocab_m.group(1)
        items = re.findall(r"\\item\s*([^\n\\]+)", block)
        items = [latex_body_to_text(i).strip().rstrip(",.;") for i in items]
        items = [i for i in items if i]
        if items:
            meta["lesson_vocabulary"] = items[:20]

    # Topic-wide vocab (if present)
    topic_m = re.search(
        r"\\textbf\{\s*TOPIC\s+VOCABULARY[^{}]*\}(.*?)(?:\\textbf\{|\\end\{lesson-meta|\Z)",
        body, flags=re.DOTALL | re.IGNORECASE)
    if topic_m:
        block = topic_m.group(1)
        items = re.findall(r"\\item\s*([^\n\\]+)", block)
        items = [latex_body_to_text(i).strip().rstrip(",.;") for i in items]
        items = [i for i in items if i]
        if items:
            meta["topic_vocabulary_unit"] = items[:30]

    return {k: v for k, v in meta.items() if v}


def build_calibration(lesson: str, meta: dict, item_analysis: dict) -> dict:
    """Build a calibration dict matching the 4-1.json structure."""
    cal = {
        "lesson": lesson,
        "title": meta.get("title", ""),
        "objective": meta.get("objective", ""),
        "essential_question": meta.get("essential_question", ""),
        "lesson_vocabulary": meta.get("lesson_vocabulary", []),
        "topic_vocabulary_unit": meta.get("topic_vocabulary_unit", []),
        "item_analysis": item_analysis,
        "notes": (
            "Auto-generated from LaTeX transcription via "
            "ingest_lesson_from_latex.py. Review item_analysis for completeness. "
            "Populate dok2_anchors / dok3_anchors by hand when the lesson's "
            "DOK-3 driver is picked."
        ),
        "dok2_anchors": [],
        "dok3_anchors": [],
        "topic_vocabulary": [],
    }
    return cal


# ─────────────────────────────────────────────────────────────────────────
# Registry stub builders
# ─────────────────────────────────────────────────────────────────────────


def build_stub(lesson: str, prompt_text: str, dok: int, *,
               source: str,
               image: Optional[str] = None,
               tags: list[str] | None = None,
               topics: list[str] | None = None,
               answer: Optional[str] = None,
               uncertainty: list[tuple[str, str]] | None = None,
               placeholders: list[tuple[str, str]] | None = None,
               explicit_id: Optional[str] = None,
               visual_type: str = "none",
               visual_needs_cleanup: bool = False) -> dict:
    """Assemble one registry JSON stub."""
    notes_parts = []
    if answer:
        notes_parts.append(f"Answer key (from source): {answer}")
    if uncertainty:
        for best, alts in uncertainty:
            notes_parts.append(f"TRANSCRIPTION UNCERTAIN: '{best}' — alternatives: {alts}")
    if placeholders:
        for vtype, desc in placeholders:
            notes_parts.append(f"IMAGE PLACEHOLDER [{vtype}]: {desc}")
    notes = " · ".join(notes_parts)

    stub = {
        "lesson": lesson,
        "source": source,
        "image": image,
        "has_visual": visual_type != "none",
        "visual_type": visual_type,
        "visual_needs_cleanup": visual_needs_cleanup,
        "visual_clean_asset": None,
        "prompt": prompt_text,
        "answers": [],
        "correct": None,
        "dok": dok,
        "dok_rationale": f"Auto-assigned DOK {dok} from source structure. Verify against Item Analysis.",
        "topics": topics or [],
        "tags": tags or [],
        "notes": notes,
    }
    if explicit_id:
        stub["id"] = explicit_id
    return stub


def dok_rationale_for_practice(dok: int, anchor_example: Optional[int]) -> str:
    ex_text = f" anchored to Example {anchor_example}" if anchor_example else ""
    if dok == 1:
        return f"Savvas-declared DOK-1 item{ex_text}. Single-step recall/recognition."
    if dok == 2:
        return f"Savvas-declared DOK-2 item{ex_text}. Routine multi-step procedure."
    if dok == 3:
        return f"Savvas-declared DOK-3 item{ex_text}. Strategic reasoning / modeling / non-routine application."
    return f"Savvas-declared DOK-{dok} item{ex_text}."


# ─────────────────────────────────────────────────────────────────────────
# Main extraction
# ─────────────────────────────────────────────────────────────────────────


def extract_all(tex: str, lesson: str) -> tuple[dict, list[dict]]:
    """Return (calibration_dict, list_of_stubs)."""
    stubs = []

    # Lesson meta + item analysis → calibration
    meta_blocks = find_blocks(tex, "lesson-meta", arg_count=0)
    meta = parse_lesson_meta(meta_blocks[0][1]) if meta_blocks else {}

    ia_blocks = find_blocks(tex, "item-analysis", arg_count=0)
    item_analysis = parse_item_analysis_table(ia_blocks[0][1]) if ia_blocks else {}

    calibration = build_calibration(lesson, meta, item_analysis)

    # Model & Discuss
    for _, body in find_blocks(tex, "model-discuss", arg_count=0):
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean)
        vt, nc = detect_visual_type(body)
        prompt = latex_body_to_text(body_clean)
        ans = extract_answer(body)
        stubs.append(build_stub(
            lesson, prompt, dok=3,
            source=f"Savvas Model & Discuss (lesson {lesson} Launch)",
            tags=[f"lesson-{lesson}", "launch", "model-discuss", "savvas-declared-launch"],
            answer=ans, uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        ))

    # Examples
    for args, body in find_blocks(tex, "example", arg_count=1):
        n = int(args[0])
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean)
        vt, nc = detect_visual_type(body)
        prompt = latex_body_to_text(body_clean)
        ans = extract_answer(body)
        stubs.append(build_stub(
            lesson, prompt, dok=2,
            source=f"Savvas Example {n} (lesson {lesson})",
            tags=[f"lesson-{lesson}", "savvas-example", f"example-{n}", "teacher-reference"],
            answer=ans, uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        ))

    # Try-Its
    for args, body in find_blocks(tex, "tryit", arg_count=1):
        n = int(args[0])
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean)
        vt, nc = detect_visual_type(body)
        prompt = latex_body_to_text(body_clean)
        ans = extract_answer(body)
        stubs.append(build_stub(
            lesson, prompt, dok=2,
            source=f"Savvas Try It {n} (lesson {lesson})",
            tags=[f"lesson-{lesson}", "try-it", f"try-it-{n}", "savvas-practice"],
            answer=ans, uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        ))

    # Practice items
    for args, body in find_blocks(tex, "practice", arg_count=2):
        n, dok_raw = int(args[0]), args[1]
        try:
            inline_dok = int(dok_raw.strip().replace("DOK", "").replace("dok", "").strip())
        except ValueError:
            print(f"WARN: practice #{n} has bad DOK {dok_raw!r} — defaulting to 2", file=sys.stderr)
            inline_dok = 2
        # Prefer DOK from Savvas Item Analysis table (authoritative) over inline arg
        ia_dok = dok_for_practice(item_analysis, n)
        dok = ia_dok if ia_dok is not None else inline_dok
        anchor = anchor_example_for_practice(item_analysis, n)
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean)
        vt, nc = detect_visual_type(body)
        prompt = latex_body_to_text(body_clean)
        ans = extract_answer(body)
        tags = [f"lesson-{lesson}", "savvas-practice"]
        if anchor:
            tags.append(f"example-{anchor}-anchor")
        if dok == 3:
            tags.extend(["savvas-declared-dok3", "dok-3-candidate"])
        stub = build_stub(
            lesson, prompt, dok=dok,
            source=f"Savvas Practice #{n} (lesson {lesson}"
                   + (f", anchors Example {anchor}" if anchor else "") + ")",
            tags=tags,
            answer=ans, uncertainty=uncert, placeholders=phs,
            explicit_id=f"{lesson}-savvas-q{n}",
            visual_type=vt, visual_needs_cleanup=nc,
        )
        stub["dok_rationale"] = dok_rationale_for_practice(dok, anchor)
        stubs.append(stub)

    # Concept box
    for _, body in find_blocks(tex, "concept-box", arg_count=0):
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean)
        vt, nc = detect_visual_type(body)
        prompt = latex_body_to_text(body_clean)
        stubs.append(build_stub(
            lesson, prompt, dok=1,
            source=f"Savvas Concept Box (lesson {lesson})",
            tags=[f"lesson-{lesson}", "savvas-concept", "reference", "quick-guide"],
            uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        ))

    # Concept summary
    for _, body in find_blocks(tex, "concept-summary", arg_count=0):
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean)
        vt, nc = detect_visual_type(body)
        prompt = latex_body_to_text(body_clean)
        stubs.append(build_stub(
            lesson, prompt, dok=2,
            source=f"Savvas Concept Summary (lesson {lesson})",
            tags=[f"lesson-{lesson}", "savvas-concept", "concept-summary", "share-summary", "reference"],
            uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        ))

    # TE addenda
    for args, body in find_blocks(tex, "te-addendum", arg_count=2):
        # Anchor can be numeric (Example N) or descriptive (e.g., "Explore & Reason").
        anchor_raw = args[0].strip()
        te_type = args[1].strip()
        try:
            anchor = int(anchor_raw)
        except ValueError:
            # Keep the descriptive string as anchor — we'll still tag appropriately.
            anchor = anchor_raw
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean)
        vt, nc = detect_visual_type(body)
        prompt = latex_body_to_text(body_clean)
        ans = extract_answer(body)
        type_slug = re.sub(r"([a-z])([A-Z])", r"\1-\2", te_type).lower()
        type_slug = re.sub(r"[^a-z0-9-]+", "-", type_slug).strip("-") or "te"
        anchor_tag = f"ex{anchor}-te" if isinstance(anchor, int) else (
            "lesson-te" if anchor == 0 else re.sub(r"[^a-z0-9-]+", "-", str(anchor).lower()).strip("-") + "-te"
        )
        anchor_desc = f"Example {anchor}" if isinstance(anchor, int) and anchor > 0 else (
            "lesson-level" if isinstance(anchor, int) and anchor == 0 else f"\"{anchor}\""
        )
        stubs.append(build_stub(
            lesson, prompt, dok=2,
            source=f"Savvas Teacher Edition — {te_type} (lesson {lesson}, anchor {anchor_desc})",
            tags=[f"lesson-{lesson}", "teacher-edition", anchor_tag, type_slug],
            answer=ans, uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        ))

    return calibration, stubs


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────


def infer_lesson(tex_path: Path, tex_content: str) -> str:
    # First try: lesson-meta block with `lesson: 4-3`
    m = re.search(r"lesson\s*[:=]\s*([\d-]+)", tex_content, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    # Fallback: filename like `4-3_savvas_source.tex`
    m = re.match(r"(\d+-\d+)", tex_path.stem)
    if m:
        return m.group(1)
    raise SystemExit("Could not infer lesson code; include `lesson: X-Y` in lesson-meta or name file like 4-3_...")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Parse Savvas-source LaTeX → registry stubs + calibration. "
                    "Accepts multiple .tex files (e.g. SE + TE); they are "
                    "concatenated in argument order before parsing."
    )
    ap.add_argument("tex_files", nargs="+",
                    help="One or more .tex files (SE, TE, assessment). "
                         "Order: SE first, then TE, then assessment.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-calibration", action="store_true",
                    help="Don't overwrite existing calibration file")
    ap.add_argument("--outdir", default=str(SKELETONS_DIR))
    args = ap.parse_args()

    # Read and concatenate all input files
    tex_parts = []
    for fpath in args.tex_files:
        p = Path(fpath)
        if not p.exists():
            sys.exit(f"ERROR: file not found: {p}")
        print(f"Reading: {p}")
        tex_parts.append(p.read_text(encoding="utf-8"))
    tex = "\n\n".join(tex_parts)

    # Infer lesson from the first file
    first_path = Path(args.tex_files[0])
    lesson = infer_lesson(first_path, tex)
    print(f"Lesson: {lesson}")
    print(f"Total input: {len(tex):,} chars from {len(args.tex_files)} file(s)")

    calibration, stubs = extract_all(tex, lesson)

    # Summary
    by_kind: dict[str, int] = {}
    flagged_uncertainty = 0
    flagged_placeholders = 0
    for s in stubs:
        src = s.get("source", "").split("(")[0].strip()
        by_kind[src] = by_kind.get(src, 0) + 1
        if "UNCERTAIN" in s.get("notes", ""):
            flagged_uncertainty += 1
        if "PLACEHOLDER" in s.get("notes", ""):
            flagged_placeholders += 1

    print(f"\nExtracted {len(stubs)} items:")
    for k, v in sorted(by_kind.items()):
        print(f"  {v:3d}  {k}")
    print(f"\nFlags:")
    print(f"  {flagged_uncertainty:3d} items with transcription uncertainty")
    print(f"  {flagged_placeholders:3d} items with image placeholders (needs manual visual work)")
    if calibration.get("item_analysis"):
        ex_count = sum(1 for k in calibration["item_analysis"] if k.startswith("example_"))
        item_count = sum(len(items) for ex in calibration["item_analysis"].values() for items in ex.values())
        print(f"  item_analysis: {ex_count} examples, {item_count} items mapped")
    else:
        print(f"  item_analysis: EMPTY — parser couldn't read the Savvas DOK table. Fill by hand.")

    if args.dry_run:
        print("\n(dry run — no files written)")
        return

    # Write calibration
    cal_path = CALIBRATION_DIR / f"{lesson}.json"
    if cal_path.exists() and args.no_calibration:
        print(f"\nSkipped calibration (--no-calibration): {cal_path} already exists")
    else:
        CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
        cal_path.write_text(json.dumps(calibration, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        print(f"\nWrote calibration: {cal_path}")

    # Write skeletons
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    skel_path = outdir / f"{lesson}_from_latex.json"
    skel_path.write_text(json.dumps(stubs, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    print(f"Wrote skeletons: {skel_path}")
    print(f"\nReview the skeleton file, then:")
    print(f"  python qb_append.py --dry-run {skel_path}")
    print(f"  python qb_append.py         {skel_path}")


if __name__ == "__main__":
    main()
