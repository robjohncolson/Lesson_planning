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


def balanced_command_blocks(body: str, command: str):
    """Yield (start, end, content) for complete braced command arguments.

    Count every brace, including escaped braces; incomplete blocks are left alone.
    """
    marker = "\\" + command + "{"
    pos = 0
    while (start := body.find(marker, pos)) != -1:
        inner_start = start + len(marker)
        depth = 1
        for index in range(inner_start, len(body)):
            if body[index] == "{":
                depth += 1
            elif body[index] == "}":
                depth -= 1
                if depth == 0:
                    yield start, index + 1, body[inner_start:index]
                    pos = index + 1
                    break
        else:
            pos = inner_start


def strip_answer_and_te(body: str) -> str:
    """Remove \\answer{} and \\te{} blocks — they're captured separately."""
    for command in ("answer", "te"):
        for start, end, _ in reversed(list(balanced_command_blocks(body, command))):
            body = body[:start] + body[end:]
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


# An answer figure is labelled as one at the START of its description ("Practice 21 answer:",
# "Answer on page 108:", "Sample Student Work Store A:"); the word later in the text
# ("source answer identifies ...", "Check Answer button", "no solution lines") does not count.
ANSWER_FIGURE_RE = re.compile(r"\banswers?\b|\bsolution\b|\bsample (?:student )?(?:work|graph|sketch|answer)", re.IGNORECASE)


def figure_label(desc: str) -> str:
    """The label of a figure description: the text before an early colon, else its first four words."""
    head, colon, _ = desc.partition(":")
    return head if colon and len(head) <= 60 else " ".join(desc.split()[:4])
# Per-lesson figure-role overrides: {"1-3": {"tryit{5}#1": "answer", ...}}; key = block + "#" + nth placeholder in it.
FIGURE_ROLES_PATH = Path(__file__).resolve().parent / "te-transcription" / "figure_roles.json"
FIGURE_ROLES = json.loads(FIGURE_ROLES_PATH.read_text(encoding="utf-8")) if FIGURE_ROLES_PATH.exists() else {}


def student_safe_description(desc: str) -> str:
    """Drop function formulas (rendering instructions such as "(y=-2(x+3)^2+4)") from a figure description
    shown to students. Only equations whose right side uses x go; tick ranges like "y=10 on (0,3]" stay.
    Square brackets become parentheses so the [IMAGE: ...] marker stays well-formed."""
    paren = r"\((?:[^()]|\((?:[^()]|\([^()]*\))*\))*\)"
    def formula(m: re.Match) -> str:
        inner = m.group(0)[1:-1]
        lhs, _, rhs = inner.partition("=")
        return "" if "=" in inner and re.search(r"x", rhs) and re.fullmatch(r"\s*[a-zA-Z](?:\(x\))?\s*", lhs) else m.group(0)
    desc = re.sub(paren, formula, desc)
    desc = re.sub(r"\b(?:for|of)\s+(?=[,;.]|$)", "", desc)
    desc = re.sub(r"(?<![\w(])[a-zA-Z](?:\(x\))?=\S*x\S*?(?=[,;]?(?:\s|$))", "", desc)
    return brackets_to_parens(desc)


# The question asks the student for the formula itself (not, e.g., "find the zeros of the function").
ASKS_FOR_FORMULA_RE = re.compile(
    r"\b(?:write|determine|give)\b[^.?\n]{0,60}?\b(?:equation|function|rule|formula)s?\b"
    r"|\bfind (?:an?|the) (?:equation|function|rule|formula)\b"
    r"|\bwhat (?:is the )?(?:equation|function|rule|formula)\b"
    r"|\bmodel the graph\b", re.IGNORECASE)
STUDENT_BLOCKS = ("practice{", "tryit{", "model-discuss")


def brackets_to_parens(desc: str) -> str:
    """Keep the [IMAGE: ...] marker well-formed; fullwidth brackets keep closed-interval meaning.

    Clauses that annotate the answer ("source answer identifies f(x)=|x-8| ...") are dropped from
    the prompt copy; the full description stays in notes."""
    clauses = re.split(r"(?<=[;.])\s+", desc)
    desc = " ".join(c for c in clauses if not re.search(r"\b(?:answers?|solutions?)\b", c, re.IGNORECASE)
                    or re.search(r"\bcheck answer\b|\bno solution\b", c, re.IGNORECASE))
    desc = desc.replace("[", "［").replace("]", "］")
    return re.sub(r"\s{2,}", " ", re.sub(r"\s+([,.;:])", r"\1", desc)).strip()


def strip_placeholders(body: str, *, lesson: str = "", block: str = "") -> tuple[str, list[tuple[str, str]]]:
    """\\placeholder{type}{description} → [IMAGE: description] for question figures, removed for answer figures.

    Both arguments are brace-balanced. A figure is an answer figure when its description says so
    (ANSWER_FIGURE_RE) or te-transcription/figure_roles.json marks it; answer figures stay in the
    returned list (and so in notes) with type "answer:<type>".
    """
    phs: list[tuple[str, str]] = []
    out, pos, nth = [], 0, 0
    overrides = FIGURE_ROLES.get(lesson, {})
    # Formulas in a figure description are a give-away only when the question asks for that formula.
    asks_formula = block.startswith(STUDENT_BLOCKS) and bool(ASKS_FOR_FORMULA_RE.search(strip_answer_and_te(body)))
    describe = student_safe_description if asks_formula else brackets_to_parens
    for start, end, vtype in balanced_command_blocks(body, "placeholder"):
        if not body.startswith("{", end):
            continue
        depth, k = 1, end + 1
        while k < len(body) and depth:
            depth += {"{": 1, "}": -1}.get(body[k], 0)
            k += 1
        if depth:
            continue
        desc = " ".join(body[end + 1:k - 1].split())
        nth += 1
        role = overrides.get(f"{block}#{nth}") or ("answer" if ANSWER_FIGURE_RE.search(figure_label(desc)) else "question")
        out.append(body[pos:start])
        note_desc = latex_body_to_text(desc)
        if role == "answer":
            phs.append((f"answer:{vtype.strip()}", note_desc))
        else:
            phs.append((vtype.strip(), note_desc))
            out.append(f"[IMAGE: {describe(desc)}]")
        pos = k
    out.append(body[pos:])
    return "".join(out), phs


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

    # Transcription comments (% FIG: ..., % Source page ...) never reach the text
    body = re.sub(r"(?<!\\)%[^\n]*", "", body)

    # Structures whose rows are delimited by \\ must be handled before \\ is dropped
    # (escaped characters stay protected so a literal \& is not a cell separator)
    body = convert_cases(body)
    if preserve_tables:
        body = simplify_tabular(body)
    else:
        body = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", "[TABLE]", body, flags=re.DOTALL)

    # Restore escaped chars
    for src, dst in PROTECT:
        body = body.replace(dst, src[1:])  # strip the backslash

    # Fractions and radicals, brace-balanced and nested in any order
    body = convert_frac_sqrt(body)
    body = re.sub(r"\\[cl]dots(?![a-zA-Z])", "...", body)
    for pattern, replacement in MATH_SUBSTITUTIONS:
        if pattern.startswith((r"\\frac", r"\\sqrt")):
            continue  # handled by convert_frac_sqrt
        body = re.sub(pattern + r"(?![a-zA-Z])" if pattern[-1].isalpha() else pattern, replacement, body)

    # Strip formatting commands (keep inner content)
    for pattern in STRIP_COMMANDS:
        body = re.sub(pattern, r"\1", body)

    # Drop empty / structural commands
    for pattern in DROP_COMMANDS:
        body = re.sub(pattern, " ", body)

    # tikzpicture: summarize
    body = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
                  "[GRAPH / TIKZ figure]", body, flags=re.DOTALL)

    # Collapse whitespace
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def _arg(s: str, i: int) -> tuple[str, int]:
    """Read one TeX argument at s[i:] (braced group or single token); return (content, next index)."""
    while i < len(s) and s[i].isspace():
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "{":
        depth, k = 1, i + 1
        while k < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[k], 0)
            k += 1
        return s[i + 1:k - 1], k
    if s[i] == "\\":
        m = re.match(r"\\[a-zA-Z]+", s[i:])
        if m:
            return m.group(0), i + len(m.group(0))
    return s[i], i + 1


def convert_frac_sqrt(s: str) -> str:
    """\\frac{a}{b} → (a)/(b), \\frac12 → (1)/(2), \\sqrt{x} → √(x), \\sqrt[3]{x} → ∛(x), innermost first."""
    out, i = [], 0
    while i < len(s):
        m = re.match(r"\\[dt]?frac(?![a-zA-Z])", s[i:])
        if m:
            a, j = _arg(s, i + len(m.group(0)))
            b, j = _arg(s, j)
            out.append(f"({convert_frac_sqrt(a)})/({convert_frac_sqrt(b)})")
            i = j
            continue
        m = re.match(r"\\sqrt(?![a-zA-Z])", s[i:])
        if m:
            j, index = i + len(m.group(0)), ""
            if j < len(s) and s[j] == "[":
                close = s.find("]", j)
                index, j = s[j + 1:close].strip(), close + 1
            a, j = _arg(s, j)
            root = {"": "√", "2": "√", "3": "∛", "4": "∜"}.get(index, f"{index}√")
            out.append(f"{root}({convert_frac_sqrt(a)})")
            i = j
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


def convert_cases(body: str) -> str:
    """\\begin{cases} e1 & c1 \\\\ e2 & c2 \\end{cases} → { e1, c1; e2, c2 } (rows kept apart)."""
    def replace(m: re.Match) -> str:
        rows = [r.strip() for r in re.split(r"\\\\", m.group(1)) if r.strip()]
        parts = []
        for r in rows:
            cells = [c.strip().rstrip(",").strip() for c in r.split("&")]
            parts.append(", ".join(c for c in cells if c))
        return "{ " + "; ".join(parts) + " }"
    return re.sub(r"\\begin\{cases\}(.*?)\\end\{cases\}", replace, body, flags=re.DOTALL)


def simplify_tabular(body: str) -> str:
    """Turn \\begin{tabular}{...}...\\end{tabular} into a compact text table (empty cells kept)."""
    def replace(m: re.Match) -> str:
        inner = m.group(1)
        # Drop the column spec — it's the {|c|c|} bit after \begin{tabular}
        inner = re.sub(r"^\{[^}]+\}", "", inner)
        # Rows delimited by \\
        rows = re.split(r"\\\\\s*", inner)
        cleaned = []
        for row in rows:
            row = re.sub(r"\\(?:hline|toprule|midrule|bottomrule)\b", "", row)
            cells = [c.strip() for c in row.split("&")]
            if any(cells):
                cleaned.append(" | ".join(c if c else "___" for c in cells))
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
    """Return every \\answer{...} in a block, in order, joined with " | " (None if there are none).

    Repeated values ("Yes", "No") are kept: each answer belongs to its own part.
    """
    answers = [latex_body_to_text(inner.strip()) for _, _, inner in balanced_command_blocks(body, "answer")]
    answers = [a for a in answers if a]
    return " | ".join(answers) if answers else None


VISUAL_TYPES = {"graph": "graph", "diagram": "diagram", "photo": "photo", "illustration": "photo",
                "map": "map", "table-image": "table"}


def visual_from_placeholders(phs: list[tuple[str, str]], body: str) -> tuple[str, bool]:
    """(visual_type, needs_cleanup) from the question figures left in the prompt; falls back to the body scan."""
    for vtype, _ in phs:
        if not vtype.startswith("answer:"):
            return VISUAL_TYPES.get(vtype, "graph"), True
    vt, nc = detect_visual_type(re.sub(r"\\placeholder\{[^{}]*\}", "", body))
    return vt, nc


def selftest() -> bool:
    """Check extraction and both removals at increasing brace depths."""
    cases = [
        ("no nesting", "42"),
        ("two-level", r"{\{x\mid x\}}"),
        ("three-level", r"{outer {middle {inner}}}"),
    ]
    passed = True
    for name, inner in cases:
        body = "Q\\answer{" + inner + "}\\te{" + inner + "}Z"
        ok = (extract_answer(body) == latex_body_to_text(inner)
              and strip_answer_and_te(body) == "QZ")
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
        passed = passed and ok
    return passed


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
    items_str = re.sub(r"\\te\{([^{}]*)\}", r"\1", items_str)  # annotated items still count
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
        body_clean, phs = strip_placeholders(body_clean, lesson=lesson, block="model-discuss")
        vt, nc = visual_from_placeholders(phs, body)
        prompt = latex_body_to_text(body_clean)
        ans = extract_answer(body)
        stubs.append(build_stub(
            lesson, prompt, dok=3,
            source=f"Savvas Model & Discuss (lesson {lesson} Launch)",
            tags=[f"lesson-{lesson}", "launch", "model-discuss", "savvas-declared-launch"],
            answer=ans, uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        ))

    # Examples — dedupe by number (SE and TE both contain Example N blocks).
    example_groups: dict[int, list[str]] = {}
    for args, body in find_blocks(tex, "example", arg_count=1):
        example_groups.setdefault(int(args[0]), []).append(body)
    for n in sorted(example_groups.keys()):
        # Richest body (typically TE has added teacher commentary) as prompt source.
        body = max(example_groups[n], key=len)
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean, lesson=lesson, block=f"example{{{n}}}")
        vt, nc = visual_from_placeholders(phs, body)
        prompt = latex_body_to_text(body_clean)
        ans = extract_answer(body)
        stubs.append(build_stub(
            lesson, prompt, dok=2,
            source=f"Savvas Example {n} (lesson {lesson})",
            tags=[f"lesson-{lesson}", "savvas-example", f"example-{n}", "teacher-reference"],
            answer=ans, uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        ))

    # Try-Its — dedupe by number (SE and TE both contain Try-It N blocks).
    tryit_groups: dict[int, list[str]] = {}
    for args, body in find_blocks(tex, "tryit", arg_count=1):
        tryit_groups.setdefault(int(args[0]), []).append(body)
    for n in sorted(tryit_groups.keys()):
        body = max(tryit_groups[n], key=len)
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean, lesson=lesson, block=f"tryit{{{n}}}")
        vt, nc = visual_from_placeholders(phs, body)
        prompt = latex_body_to_text(body_clean)
        ans = extract_answer(body)
        stub = build_stub(
            lesson, prompt, dok=2,
            source=f"Savvas Try It {n} (lesson {lesson})",
            # Try It N continues Example N and may rely on its givens (a rate, a model, a graph).
            tags=[f"lesson-{lesson}", "try-it", f"try-it-{n}", "savvas-practice", f"linked-example-{n}"],
            answer=ans, uncertainty=uncert, placeholders=phs,
            visual_type=vt, visual_needs_cleanup=nc,
        )
        context = f"Context: continues Savvas Example {n} (lesson {lesson}); deliver with that example."
        stub["notes"] = context + (" · " + stub["notes"] if stub["notes"] else "")
        stubs.append(stub)

    # Practice items — dedupe by item number when SE+TE both contain the block.
    # SE typically declares DOK as '?' (unknown, defaults to 2); TE declares the
    # authoritative DOK. For each item number, pick the block with a real inline
    # DOK over a '?'-defaulted one, and prefer the longer body as the prompt
    # source when both are real (richer TE annotations won't clobber a fuller SE
    # body if the SE body is longer).
    practice_groups: dict[int, list[tuple[list[str], str, int, bool]]] = {}
    for args, body in find_blocks(tex, "practice", arg_count=2):
        n = int(args[0])
        dok_raw = args[1]
        raw_stripped = dok_raw.strip().replace("DOK", "").replace("dok", "").strip()
        try:
            inline_dok = int(raw_stripped)
            dok_is_real = True
        except ValueError:
            inline_dok = 2
            dok_is_real = False
        practice_groups.setdefault(n, []).append((args, body, inline_dok, dok_is_real))

    for n in sorted(practice_groups.keys()):
        blocks = practice_groups[n]
        # Pick DOK source: any block with a real declaration wins over defaulted ones.
        real_doks = [b for b in blocks if b[3]]
        if real_doks:
            # If multiple TE blocks declare DOK, take the highest (declared-DOK-3 wins).
            inline_dok = max(b[2] for b in real_doks)
            if len(set(b[2] for b in real_doks)) > 1:
                print(f"WARN: practice #{n} has conflicting declared DOKs across SE/TE — using max={inline_dok}",
                      file=sys.stderr)
        else:
            print(f"WARN: practice #{n} has no real DOK declaration (all '?') — defaulting to 2",
                  file=sys.stderr)
            inline_dok = 2
        # Pick body source: longest body (richest prompt text).
        _, body, _, _ = max(blocks, key=lambda b: len(b[1]))
        # Prefer DOK from Savvas Item Analysis table (authoritative) over inline arg
        ia_dok = dok_for_practice(item_analysis, n)
        dok = ia_dok if ia_dok is not None else inline_dok
        anchor = anchor_example_for_practice(item_analysis, n)
        body_clean, uncert = resolve_uncertain(body)
        body_clean, phs = strip_placeholders(body_clean, lesson=lesson, block=f"practice{{{n}}}")
        vt, nc = visual_from_placeholders(phs, body)
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
        body_clean, phs = strip_placeholders(body_clean, lesson=lesson, block="concept-box")
        vt, nc = visual_from_placeholders(phs, body)
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
        body_clean, phs = strip_placeholders(body_clean, lesson=lesson, block="concept-summary")
        vt, nc = visual_from_placeholders(phs, body)
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
        body_clean, phs = strip_placeholders(body_clean, lesson=lesson, block=f"te-addendum{{{anchor_raw}}}{{{te_type}}}")
        vt, nc = visual_from_placeholders(phs, body)
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
    ap.add_argument("tex_files", nargs="*",
                    help="One or more .tex files (SE, TE, assessment). "
                         "Order: SE first, then TE, then assessment.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="Run inline brace scanner tests")
    ap.add_argument("--no-calibration", action="store_true",
                    help="Don't overwrite existing calibration file")
    ap.add_argument("--outdir", default=str(SKELETONS_DIR))
    args = ap.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    if not args.tex_files:
        ap.error("at least one tex file is required unless --selftest is used")

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
