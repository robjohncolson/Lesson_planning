"""Backfill registry fields from hand-authored teacher .tex files.

Extracts two things from each tex/L*_teacher.tex:

  1. role='do-now' — for items referenced as `\\bankitem{Do Now (<id>)}{...}`.
     Only populates when the registry row has role empty/null.

  2. teacher_answer — the BODY of the `\\teacheranswerbox{TITLE}{BODY}` that
     immediately follows a `\\bankitem{LABEL}{...}`. LABEL → bank id via:
       - id in parens:   Do Now (<id>)                     → <id>
       - Try It N:        Try It 3                          → <lesson>-tryit-3
       - Practice #N:     Practice \\#32 ... DOK-3 TITLE    → <lesson>-savvas-q32
     Only populates when registry.teacher_answer is empty/null.

Usage:
    python backfill_from_teacher_tex.py              # dry-run (default)
    python backfill_from_teacher_tex.py --apply      # write to registry.jsonl

Safe to re-run: never overwrites existing values. Reports unmatched labels
for manual review.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent
TEX_DIR = REPO / "tex"
REG_PATH = REPO / "questionbank" / "registry.jsonl"

# ── Brace-balanced extractor ────────────────────────────────────────────────

def find_brace_group(s: str, start: int) -> tuple[str, int]:
    """Given s[start] == '{', return (inside_content, index_after_closing_brace)."""
    assert s[start] == "{", f"expected {{, got {s[start]!r} at {start}"
    depth = 0
    i = start
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1:i], i + 1
        i += 1
    raise ValueError(f"unterminated brace starting at {start}")


def extract_bankitem_pairs(tex: str) -> list[tuple[str, int, int]]:
    """Return list of (label, label_end_idx, body_end_idx) for each \\bankitem."""
    out = []
    for m in re.finditer(r"\\bankitem\s*\{", tex):
        label_start = m.end() - 1  # the '{'
        try:
            label, after_label = find_brace_group(tex, label_start)
        except ValueError:
            continue
        # next { is the body
        rest = tex[after_label:]
        brace = re.search(r"\{", rest)
        if not brace:
            continue
        body_start = after_label + brace.start()
        try:
            _, after_body = find_brace_group(tex, body_start)
        except ValueError:
            continue
        out.append((label, after_label, after_body))
    return out


def extract_teacher_answer_after(tex: str, start: int, search_window: int = 2000) -> str | None:
    """Find the next `\\teacheranswerbox{TITLE}{BODY}` within search_window of start.
    Return BODY, or None. Stops early if another \\bankitem starts first."""
    window_end = min(len(tex), start + search_window)
    slice_ = tex[start:window_end]

    tb = re.search(r"\\teacheranswerbox\s*\{", slice_)
    bi = re.search(r"\\bankitem\s*\{", slice_)

    # If bankitem appears before teacheranswerbox, no answer for this item
    if bi and (not tb or bi.start() < tb.start()):
        return None
    if not tb:
        return None

    title_start = start + tb.end() - 1  # the '{'
    try:
        _, after_title = find_brace_group(tex, title_start)
    except ValueError:
        return None
    # body { comes next
    rest = tex[after_title:]
    brace = re.search(r"\{", rest)
    if not brace:
        return None
    body_start = after_title + brace.start()
    try:
        body, _ = find_brace_group(tex, body_start)
    except ValueError:
        return None
    return body.strip()


# ── Label → bank id heuristics ──────────────────────────────────────────────

RE_ID_IN_PARENS = re.compile(r"\(([0-9a-zA-Z][\w\-]+)\)")
RE_TRYIT = re.compile(r"Try\s*It\s*(\d+[a-z]?)", re.IGNORECASE)
RE_PRACTICE = re.compile(r"Practice\s*\\?#\s*(\d+)", re.IGNORECASE)


def resolve_label_to_id(label: str, lesson: str, known_ids: set[str]) -> str | None:
    """Given a bankitem LABEL and its lesson code (e.g. '3-5'), return bank id."""
    # 1. id-in-parens — the most reliable signal
    for m in RE_ID_IN_PARENS.finditer(label):
        cand = m.group(1)
        if cand in known_ids:
            return cand

    # 2. Try It N → <lesson>-tryit-N
    tm = RE_TRYIT.search(label)
    if tm:
        cand = f"{lesson}-tryit-{tm.group(1).lower()}"
        if cand in known_ids:
            return cand

    # 3. Practice #N → <lesson>-savvas-qN
    pm = RE_PRACTICE.search(label)
    if pm:
        cand = f"{lesson}-savvas-q{pm.group(1)}"
        if cand in known_ids:
            return cand

    return None


# ── Lesson code from filename ───────────────────────────────────────────────

def lesson_code_from_path(tex_path: Path) -> str | None:
    """tex/L35_P2_teacher.tex → '3-5'. tex/APStats_6-4_P1_teacher.tex → 'APStats-6-4'."""
    name = tex_path.stem  # L35_P2_teacher
    m = re.match(r"L(\d)(\d)_P\d+_teacher$", name)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.match(r"APStats_(\d+)-(\d+)_P\d+_teacher$", name)
    if m:
        return f"APStats-{m.group(1)}-{m.group(2)}"
    return None


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write changes to registry.jsonl (default: dry-run)")
    ap.add_argument("--limit", type=int, default=0,
                    help="process only first N teacher files (for smoke test)")
    args = ap.parse_args()

    # Load registry
    rows: list[dict] = []
    for line in REG_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    by_id = {r["id"]: r for r in rows}
    known_ids = set(by_id)

    # Find teacher tex files
    teacher_files = sorted(TEX_DIR.glob("L*_teacher.tex")) + sorted(TEX_DIR.glob("APStats_*_teacher.tex"))
    teacher_files = [f for f in teacher_files if "_regen" not in f.stem]
    if args.limit:
        teacher_files = teacher_files[:args.limit]

    role_updates: list[tuple[str, str]] = []      # (id, source file)
    answer_updates: list[tuple[str, str, str]] = []  # (id, answer, source file)
    unmatched: list[tuple[str, str]] = []         # (label, source file)

    for tp in teacher_files:
        lesson = lesson_code_from_path(tp)
        if not lesson:
            print(f"skip: {tp.name} — cannot derive lesson code")
            continue

        tex = tp.read_text(encoding="utf-8")
        pairs = extract_bankitem_pairs(tex)

        for label, after_label, after_body in pairs:
            bank_id = resolve_label_to_id(label, lesson, known_ids)
            is_donow = label.strip().lower().startswith("do now")

            if not bank_id:
                if is_donow:
                    # Prose-only Do Now (no bank item); not an error
                    continue
                unmatched.append((label[:80], tp.name))
                continue

            r = by_id[bank_id]

            # Do Now role backfill
            if is_donow and not (r.get("role") or "").strip():
                role_updates.append((bank_id, tp.name))

            # Teacher answer backfill
            if not (r.get("teacher_answer") or "").strip():
                answer = extract_teacher_answer_after(tex, after_body)
                if answer:
                    answer_updates.append((bank_id, answer, tp.name))

    # ── Report ────────────────────────────────────────────────────────────
    print(f"\n=== Backfill Report ===\n")
    print(f"teacher tex files scanned: {len(teacher_files)}")
    print(f"registry items total: {len(rows)}")
    print(f"role='do-now' to add: {len(role_updates)}")
    print(f"teacher_answer to add: {len(answer_updates)}")
    print(f"unmatched bankitem labels: {len(unmatched)}")

    if role_updates[:5]:
        print("\n-- Sample role updates --")
        for id_, src in role_updates[:8]:
            print(f"  {id_}   ({src})")
    if answer_updates[:3]:
        print("\n-- Sample answer updates --")
        for id_, ans, src in answer_updates[:3]:
            print(f"  {id_}   ({src})")
            print(f"    answer: {ans[:120]}{'...' if len(ans) > 120 else ''}")
    if unmatched[:5]:
        print("\n-- Sample unmatched --")
        for lab, src in unmatched[:8]:
            print(f"  {lab!r}   ({src})")

    if not args.apply:
        print("\n(dry-run — pass --apply to write)")
        return 0

    # ── Apply ─────────────────────────────────────────────────────────────
    # De-dup: one entry per id (last-writer-wins per id — answer_updates already
    # checks empty; role_updates are idempotent).
    role_ids = {id_ for id_, _ in role_updates}
    answer_map: dict[str, str] = {}
    for id_, ans, _ in answer_updates:
        answer_map.setdefault(id_, ans)  # first-wins

    changed = 0
    for r in rows:
        touched = False
        if r["id"] in role_ids and not (r.get("role") or "").strip():
            r["role"] = "do-now"
            touched = True
        if r["id"] in answer_map and not (r.get("teacher_answer") or "").strip():
            r["teacher_answer"] = answer_map[r["id"]]
            touched = True
        if touched:
            changed += 1

    # Write atomically
    tmp = REG_PATH.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(REG_PATH)
    print(f"\napplied: {changed} rows updated in {REG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
