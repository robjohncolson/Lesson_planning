"""Seed the lesson_planning.lesson_phases table by parsing teacher .tex files.

Extracts per-period phase structure from each tex/L*_teacher.tex (and
tex/APStats_*_teacher.tex). For every phase section detected, finds the
\\bankitem occurrences in order and emits one row per bankitem:

    (lesson_id, phase, position, item_id, label)

Unmatched labels are emitted with item_id=NULL so the UI can still render
them as non-clickable rows (teacher sees what's there).

Usage:
    python supabase/seed_lesson_phases.py              # dry-run (default)
    python supabase/seed_lesson_phases.py --apply      # write to DB

--apply requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY. In apply mode,
all existing rows for each lesson_id are DELETEd before INSERT to avoid
stale position leaks from previous runs.

Idempotent: safe to re-run.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TEX_DIR = REPO / "tex"
REG_PATH = REPO / "questionbank" / "registry.jsonl"
SCHEMA = "lesson_planning"

PHASE_ORDER = ["do_now", "launch", "explore", "share_summary", "exit", "reinforcement"]


# ── Brace-balanced extractor (adapted from backfill_from_teacher_tex.py) ────

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


# ── Phase normalization ─────────────────────────────────────────────────────

RE_ICON_MACRO = re.compile(r"\\Icon[A-Za-z]+\s*")
RE_NONALNUM_SPACE = re.compile(r"[^a-z0-9 ]+")
RE_WS = re.compile(r"\s+")


def normalize_phase(raw: str) -> str | None:
    """Map raw phase string (possibly with icon macros / punctuation) to enum."""
    # Strip icon macros like \IconBolt, \IconStar
    s = RE_ICON_MACRO.sub(" ", raw)
    # Strip other backslash commands conservatively
    s = re.sub(r"\\[A-Za-z]+", " ", s)
    s = s.replace("---", " ").replace("--", " ")
    s = s.lower()
    s = RE_NONALNUM_SPACE.sub(" ", s)
    s = RE_WS.sub(" ", s).strip()

    # Some packets prefix with non-phase descriptors like
    # "explore think pair share 35 min" — look for the phase keyword.
    if not s:
        return None
    if "do now" in s or s.startswith("donow") or s == "do now":
        return "do_now"
    if "launch" in s:
        return "launch"
    if "explore" in s:
        return "explore"
    if "share" in s or "summary" in s:
        return "share_summary"
    if "exit" in s:
        return "exit"
    if "reinforcement" in s or "optional" in s or "back of packet" in s:
        return "reinforcement"
    return None


# ── Phase section detection ─────────────────────────────────────────────────
#
# Priority per plan:
#   1. \sectionbanner{<PHASE>}
#   2. \frameworkphaseheader{<PHASE>}{...}
#   3. \phasetag{<PHASE>}
#
# In practice, teacher packets use BOTH \sectionbanner and \frameworkphaseheader
# near each phase start (see L35_P2_teacher.tex: \sectionbanner{LAUNCH ---
# Multiplicity Rule} then \frameworkphaseheader{Launch}{2}{12}{...}). We scan
# all three macros, and if two fire close together we keep the first by
# position (so we don't double-count phases).


def find_phase_sections(tex: str) -> list[tuple[int, str]]:
    """Return list of (start_index, phase_enum) sorted by position.

    start_index is the character offset in tex where the phase section begins
    (right after the phase header macro ends). Later we scan bankitems until
    the next phase section.
    """
    out: list[tuple[int, str]] = []

    # 1. \sectionbanner{...}
    for m in re.finditer(r"\\sectionbanner\s*\{", tex):
        brace = m.end() - 1
        try:
            inside, end = find_brace_group(tex, brace)
        except ValueError:
            continue
        phase = normalize_phase(inside)
        if phase:
            out.append((end, phase))

    # 2. \frameworkphaseheader{PHASE}{...}{...}{...}
    for m in re.finditer(r"\\frameworkphaseheader\s*\{", tex):
        brace = m.end() - 1
        try:
            inside, end = find_brace_group(tex, brace)
        except ValueError:
            continue
        phase = normalize_phase(inside)
        if phase:
            # The macro has multiple subsequent brace groups; we want to
            # start scanning bankitems after the LAST group (the body).
            # Walk 3 more brace groups past the phase name.
            cur = end
            for _ in range(3):
                nxt = tex.find("{", cur)
                if nxt == -1:
                    break
                # only advance if whitespace-only between cur and nxt
                if tex[cur:nxt].strip():
                    break
                try:
                    _, cur = find_brace_group(tex, nxt)
                except ValueError:
                    break
            out.append((cur, phase))

    # 3. \phasetag{...}  (lower priority — often appears before
    # frameworkphaseheader; we use them as hints but they'll be dedup'd)
    for m in re.finditer(r"\\phasetag\s*\{", tex):
        brace = m.end() - 1
        try:
            inside, end = find_brace_group(tex, brace)
        except ValueError:
            continue
        phase = normalize_phase(inside)
        if phase:
            out.append((end, phase))

    # Sort by position, then dedupe: if two phase markers of the same phase
    # land within 200 chars of each other (e.g. sectionbanner + phasetag +
    # frameworkphaseheader for the same phase), keep the latest start position
    # so bankitem scanning starts AFTER the whole header block.
    out.sort(key=lambda t: t[0])
    deduped: list[tuple[int, str]] = []
    for pos, phase in out:
        if deduped and deduped[-1][1] == phase and pos - deduped[-1][0] < 1500:
            # same phase, close together — replace with later position
            deduped[-1] = (pos, phase)
        else:
            deduped.append((pos, phase))
    return deduped


# ── Bankitem extraction within a range ──────────────────────────────────────

def extract_bankitems_in_range(tex: str, start: int, end: int) -> list[str]:
    """Return labels of \\bankitem occurrences in tex[start:end], in order."""
    out = []
    for m in re.finditer(r"\\bankitem\s*\{", tex):
        if m.start() < start or m.start() >= end:
            continue
        label_start = m.end() - 1  # the '{'
        try:
            label, _ = find_brace_group(tex, label_start)
        except ValueError:
            continue
        out.append(label)
    return out


# ── Label → bank id (same heuristics as backfill script, slightly extended) ─

RE_ID_IN_PARENS = re.compile(r"\(([0-9a-zA-Z][\w\-]+)\)")
RE_TRYIT = re.compile(r"Try\s*It\s*(\d+[a-z]?)", re.IGNORECASE)
RE_PRACTICE = re.compile(r"Practice\s*\\?#\s*(\d+)", re.IGNORECASE)
RE_OPTIONAL = re.compile(r"Optional\s*\\?#\s*(\d+)", re.IGNORECASE)


def find_numbered_lesson_id(ids_by_lesson: dict[str, list[str]], lesson_code: str,
                            number: str, preferred_token: str | None = None) -> str | None:
    """Find a lesson-scoped item id containing q<number>, optionally preferring a phase token."""
    pattern = re.compile(rf"(^|[^0-9])q0*{re.escape(number)}(?!\d)", re.IGNORECASE)
    for cand in ids_by_lesson.get(lesson_code, ()):
        low = cand.lower()
        if preferred_token and preferred_token not in low:
            continue
        if pattern.search(low):
            return cand
    return None


def resolve_label_to_id(label: str, lesson_code: str, known_ids: set[str],
                        ids_by_lesson: dict[str, list[str]]) -> str | None:
    # 1. id in parens
    for m in RE_ID_IN_PARENS.finditer(label):
        cand = m.group(1)
        if cand in known_ids:
            return cand

    # 2. Try It N  → look for lesson-scoped id containing try-it-N or tryit-N
    tm = RE_TRYIT.search(label)
    if tm:
        n = tm.group(1).lower()
        direct = f"{lesson_code}-tryit-{n}"
        if direct in known_ids:
            return direct
        # Savvas-style variant: <lesson>-savvas-try-it-<n>-...
        for cand in ids_by_lesson.get(lesson_code, ()):
            low = cand.lower()
            if f"try-it-{n}" in low or f"tryit-{n}" in low:
                return cand

    # 3. Practice #N
    pm = RE_PRACTICE.search(label)
    if pm:
        cand = f"{lesson_code}-savvas-q{pm.group(1)}"
        if cand in known_ids:
            return cand
        fallback = find_numbered_lesson_id(ids_by_lesson, lesson_code, pm.group(1), "explore")
        if fallback:
            return fallback

    # 4. Optional #N
    om = RE_OPTIONAL.search(label)
    if om:
        cand = f"{lesson_code}-savvas-q{om.group(1)}"
        if cand in known_ids:
            return cand
        fallback = find_numbered_lesson_id(ids_by_lesson, lesson_code, om.group(1), "reinforcement")
        if fallback:
            return fallback

    return None


# ── Lesson id / code from filename ──────────────────────────────────────────

def parse_filename(tex_path: Path) -> tuple[str, str] | None:
    """Return (lesson_id, lesson_code) or None.

    L35_P2_teacher.tex → ('L35_P2', '3-5')
    APStats_6-4_P1_teacher.tex → ('APStats_6-4_P1', 'APStats-6-4')
    """
    name = tex_path.stem  # e.g. L35_P2_teacher
    m = re.match(r"(L(\d)(\d)_P\d+)_teacher$", name)
    if m:
        return m.group(1), f"{m.group(2)}-{m.group(3)}"
    m = re.match(r"(APStats_(\d+)-(\d+)_P\d+)_teacher$", name)
    if m:
        return m.group(1), f"APStats-{m.group(2)}-{m.group(3)}"
    return None


# ── Main ────────────────────────────────────────────────────────────────────

def env_or_exit(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"error: {name} not set")
    return v


def parse_all() -> tuple[list[dict], list[tuple[str, str, str]], dict[str, int]]:
    """Parse all teacher tex files. Return (rows, unmatched, per_lesson_counts)."""
    # Load registry
    known_ids: set[str] = set()
    ids_by_lesson: dict[str, list[str]] = {}
    for line in REG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = r.get("id")
        if not rid:
            continue
        known_ids.add(rid)
        lesson = r.get("lesson") or ""
        ids_by_lesson.setdefault(lesson, []).append(rid)

    teacher_files = sorted(TEX_DIR.glob("L*_teacher.tex")) + sorted(
        TEX_DIR.glob("APStats_*_teacher.tex"))
    teacher_files = [f for f in teacher_files if "_regen" not in f.stem]

    rows: list[dict] = []
    unmatched: list[tuple[str, str, str]] = []  # (label, lesson_id, filename)
    per_lesson_counts: dict[str, int] = {}

    for tp in teacher_files:
        parsed = parse_filename(tp)
        if not parsed:
            continue
        lesson_id, lesson_code = parsed
        tex = tp.read_text(encoding="utf-8")

        sections = find_phase_sections(tex)
        if not sections:
            continue

        # position-per-phase counter (a lesson can only have a phase once,
        # but if we see duplicate markers we concat; still position is
        # unique per (lesson_id, phase))
        phase_positions: dict[str, int] = {}

        # Iterate section ranges
        for i, (start, phase) in enumerate(sections):
            end = sections[i + 1][0] if i + 1 < len(sections) else len(tex)
            labels = extract_bankitems_in_range(tex, start, end)
            for label in labels:
                item_id = resolve_label_to_id(label, lesson_code, known_ids, ids_by_lesson)
                if item_id is None:
                    unmatched.append((label[:100], lesson_id, tp.name))
                pos = phase_positions.get(phase, 0)
                phase_positions[phase] = pos + 1
                rows.append({
                    "lesson_id": lesson_id,
                    "phase":     phase,
                    "position":  pos,
                    "item_id":   item_id,
                    "label":     label[:500],
                })
        per_lesson_counts[lesson_id] = sum(phase_positions.values())

    return rows, unmatched, per_lesson_counts


def delete_for_lesson(url: str, key: str, lesson_id: str) -> None:
    endpoint = f"{url}/rest/v1/lesson_phases?lesson_id=eq.{lesson_id}"
    headers = {
        "apikey":          key,
        "Authorization":   f"Bearer {key}",
        "Content-Profile": SCHEMA,
        "Accept-Profile":  SCHEMA,
        "Prefer":          "return=minimal",
    }
    import requests  # local import so dry-run doesn't require it
    r = requests.delete(endpoint, headers=headers, timeout=60)
    if r.status_code >= 300:
        print(f"  ERROR deleting {lesson_id}: {r.status_code} {r.text[:200]}")
        sys.exit(1)


def insert_rows(url: str, key: str, rows: list[dict]) -> None:
    endpoint = f"{url}/rest/v1/lesson_phases"
    headers = {
        "apikey":          key,
        "Authorization":   f"Bearer {key}",
        "Content-Type":    "application/json",
        "Content-Profile": SCHEMA,
        "Accept-Profile":  SCHEMA,
        "Prefer":          "return=minimal",
    }
    import requests
    r = requests.post(endpoint, headers=headers, data=json.dumps(rows), timeout=120)
    if r.status_code >= 300:
        print(f"  ERROR inserting: {r.status_code} {r.text[:500]}")
        sys.exit(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write to Supabase (default: dry-run parser report)")
    args = ap.parse_args()

    rows, unmatched, per_lesson = parse_all()

    # Report
    print(f"\n=== Lesson Phases Seed Report ===\n")
    print(f"total rows emitted:  {len(rows)}")
    print(f"lessons with phases: {len(per_lesson)}")
    print(f"unmatched labels:    {len(unmatched)}")

    # Per-lesson phase breakdown
    from collections import defaultdict
    by_lesson_phase: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        by_lesson_phase[r["lesson_id"]][r["phase"]] += 1

    print(f"\n-- Per-lesson phase counts --")
    for lid in sorted(by_lesson_phase):
        counts = by_lesson_phase[lid]
        parts = []
        for p in PHASE_ORDER:
            if counts.get(p):
                parts.append(f"{p}={counts[p]}")
        total = sum(counts.values())
        print(f"  {lid:20s} total={total:3d}  " + " ".join(parts))

    if unmatched:
        print(f"\n-- Sample unmatched (first 10 of {len(unmatched)}) --")
        for lab, lid, src in unmatched[:10]:
            print(f"  [{lid}] {lab!r}   ({src})")

    if not args.apply:
        print("\n(dry-run — pass --apply to write to Supabase)")
        return 0

    # ── Apply ─────────────────────────────────────────────────────────────
    url = env_or_exit("SUPABASE_URL")
    key = env_or_exit("SUPABASE_SERVICE_ROLE_KEY")

    # Delete all existing rows per lesson_id (avoids stale positions)
    lesson_ids = sorted({r["lesson_id"] for r in rows})
    print(f"\ndeleting existing rows for {len(lesson_ids)} lessons…")
    for lid in lesson_ids:
        delete_for_lesson(url, key, lid)

    # Insert in reasonable chunks
    CHUNK = 500
    print(f"inserting {len(rows)} rows in chunks of {CHUNK}…")
    for i in range(0, len(rows), CHUNK):
        insert_rows(url, key, rows[i:i + CHUNK])

    print(f"done: {len(rows)} rows applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
