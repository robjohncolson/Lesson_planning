"""Question-bank accessor module.

Load the registry, filter by lesson/DOK/topics, and resolve image paths for
packet/slide builders.

Usage:
    from qb import select, get
    questions = select(lesson="3-5", dok=2, topics=["multiplicity"])

Merged-alias exclusion (rc-merge-auth-5-4-2026-07-23, STUDENT-FACING
selector -- the critical exclusion point): 22 of the 900 registry rows
(lesson 5-4) now carry status=="merged-alias" + alias_of (the survivor
row's item_uid), written by a Fable-authorized merge of 22 of the 85
ambiguous-legacy-id duplicate pairs. This module NEVER returns a
merged-alias row's own content from get() / select() / get_for_packet():
every one of those three public entry points resolves a merged-alias row
DELIBERATELY to its survivor via alias_of (never by legacy-id ambiguity --
never first-match, never dict-last-wins on a duplicate id) and fails loudly
(KeyError/ValueError) if the alias_of target is missing or is itself an
alias (a chain). The uid used for that resolution is computed independently
here via the SAME published algorithm as
inventory/dedup/build_item_uid_map.py (item_uid = 'iu_' +
sha1(f'{lesson}|{source}|{prompt_sha1}')[:12], prompt_sha1 = sha1(prompt) --
see _item_uid_for_row below) rather than reading
inventory/dedup/item_uid_alias_map.json, which is out of this module's
ownership. Public API signatures (get/select/get_for_packet/stats) are
unchanged -- only their internal resolution logic is deliberate now.
stats() reports the dual denominators: raw registry rows (900), active
canonical items (878), and merged-alias rows (22).

Deliberately OUT OF SCOPE: the other 63 (of 85) ambiguous-legacy-id groups
that this merge did NOT resolve keep their EXACT pre-merge tie-break
behavior -- get() returns the FIRST matching row (its original loop-and-
return-on-match behavior, unchanged); get_for_packet() returns the LAST
matching row (its original {id: row} dict-comprehension's dict-last-wins
behavior, unchanged) -- for these 63, no error, no resolution attempt.
Deliberate survivor resolution (via alias_of) and fail-loud (KeyError/
ValueError) apply ONLY to a legacy id whose group actually contains a
merged-alias row, i.e. one of the 22 RC-authorized pairs. RC's
authorization (rc-merge-auth-5-4-2026-07-23) covers only those 22; silently
changing the tie-break behavior for the remaining 63 -- even to make it
"more correct" -- would be unauthorized scope creep on a question-bank
content decision, not a code-correctness fix, and would regress every
existing caller (legacy packet/slide builders) that already depends on the
old tie-break for those ids.

Optional-catalog exclusion (nt14-ingest-4-1-2026-07-23): registry rows
carrying a top-level "availability": "optional-catalog" field (Lesson 4-1,
19 rows ingested under this record id) are OPTIONAL CATALOG CONTENT --
deliberately never auto-scheduled, placed in pacing, counted toward
completion, or emitted by any default selection path that could feed
required sequencing. select() drops these rows by default; pass the
explicit keyword-only `include_optional=True` to opt in. get() and
get_for_packet() are UNCHANGED -- explicit by-id access is deliberate
teacher access and still returns optional-catalog rows regardless of the
flag (there is no flag on those two). stats() reports the triple
denominators: raw registry rows == active/required-active rows +
optional-catalog rows + merged-alias rows.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "questionbank" / "registry.jsonl"
CALIBRATION_DIR = ROOT / "questionbank" / "calibration"
IMAGES_DIR = ROOT / "questionbank" / "images"


def load() -> list[dict]:
    if not REGISTRY.exists():
        return []
    out = []
    with REGISTRY.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Bad JSON on registry line {i}: {e}") from e
    return out


def append(entry: dict) -> None:
    # registry's dominant convention is LF; historical text-mode appends on
    # Windows produced 4 stray CRLF lines; new appends are LF
    # (nt14-ingest-4-1-2026-07-23) -- newline="\n" disables Windows' default
    # text-mode "\n" -> "\r\n" translation so every appended line ends in a
    # bare "\n", matching the rest of the file.
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ----------------------------------------------------------------------
# Merged-alias resolution (rc-merge-auth-5-4-2026-07-23). See module
# docstring's "Merged-alias exclusion" section.
# ----------------------------------------------------------------------

def _sha1_hex(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _item_uid_for_row(row: dict) -> str:
    """Compute item_uid via the published algorithm -- BYTE-IDENTICAL to
    inventory/dedup/build_item_uid_map.py's compute_item_uid(): item_uid =
    'iu_' + sha1(f'{lesson}|{source}|{prompt_sha1}')[:12], where
    prompt_sha1 = sha1(prompt) and a missing/None prompt counts as ''.
    Computed independently from the row itself -- this module never reads
    inventory/dedup/item_uid_alias_map.json (out of its ownership)."""
    lesson = row.get("lesson")
    source = row.get("source")
    prompt = row.get("prompt")
    if prompt is None:
        prompt = ""
    prompt_sha1 = _sha1_hex(prompt)
    basis = f"{lesson}|{source}|{prompt_sha1}"
    return "iu_" + _sha1_hex(basis)[:12]


def _build_uid_index(items: list[dict]) -> dict[str, dict]:
    """item_uid -> row, one entry per registry row (900 distinct uids for
    900 rows in the current registry -- see item_uid_alias_map.json's own
    meta.distinct_item_uids -- so this dict is 1:1, never overwritten by a
    collision in practice)."""
    return {_item_uid_for_row(row): row for row in items}


def _resolve_alias(row: dict, uid_index: dict[str, dict]) -> dict:
    """Resolve a merged-alias `row` DELIBERATELY to its survivor via
    row['alias_of'] -- NEVER by falling back to legacy-id ambiguity. Fails
    loudly if alias_of is missing/empty, does not resolve to any known
    item_uid, or itself points at another merged-alias row (an alias
    chain) -- a data-integrity problem a student-facing selector must
    never paper over silently."""
    alias_of = row.get("alias_of")
    if not alias_of:
        raise ValueError(
            f"registry row id={row.get('id')!r} has status=='merged-alias' "
            "but no (or empty) alias_of -- cannot resolve"
        )
    survivor = uid_index.get(alias_of)
    if survivor is None:
        raise KeyError(
            f"registry row id={row.get('id')!r} alias_of={alias_of!r} does "
            "not resolve to any item_uid in the registry -- dangling alias"
        )
    if survivor.get("status") == "merged-alias":
        raise ValueError(
            f"registry row id={row.get('id')!r} alias_of={alias_of!r} is "
            "itself a merged-alias row -- alias chains are not supported"
        )
    return survivor


def get(qid: str) -> dict | None:
    items = load()
    for q in items:
        if q.get("id") == qid:
            if q.get("status") == "merged-alias":
                return _resolve_alias(q, _build_uid_index(items))
            return q
    return None


def lessons() -> list[str]:
    return sorted({q["lesson"] for q in load() if q.get("lesson")})


def select(
    *,
    lesson: str | None = None,
    dok: int | Iterable[int] | None = None,
    topics: Iterable[str] | None = None,
    topics_mode: str = "any",  # "any" or "all"
    tags: Iterable[str] | None = None,
    has_visual: bool | None = None,
    limit: int | None = None,
    include_optional: bool = False,
) -> list[dict]:
    items = load()
    # Merged-alias rows are never a selectable copy (rc-merge-auth-5-4-
    # 2026-07-23) -- their content lives on, and is reachable only through,
    # their survivor row. Dropped first, before any other filter, so this
    # holds regardless of which other filters are applied.
    items = [q for q in items if q.get("status") != "merged-alias"]
    # Optional-catalog exclusion (nt14-ingest-4-1-2026-07-23): select() is
    # the surface that could feed required sequencing (pacing, auto-
    # scheduling, completion counts) -- so any row explicitly marked
    # "availability": "optional-catalog" (currently Lesson 4-1's 19 rows) is
    # dropped here by default, same as the merged-alias drop above and for
    # the same reason: no filter combination below should be able to
    # resurface it. A caller performing a DELIBERATE, explicit lookup of
    # optional-catalog content must opt in with include_optional=True --
    # there is no other way in from this function. get() / get_for_packet()
    # are untouched by this and always return optional-catalog rows by
    # explicit id, since by-id access is deliberate teacher access, not
    # default sequencing.
    if not include_optional:
        items = [q for q in items if q.get("availability") != "optional-catalog"]
    # Source-gap exclusion (nt14-ingest-4-1-2026-07-23, RC acceptance rule):
    # a row carrying a top-level "source_gap" marker (currently 4-1-savvas-
    # q16 "given-illegible" and q18 "answer-truncated") is KNOWN-INCOMPLETE
    # source material. Explicit optional inclusion must not mean "include
    # broken items", so this drop is UNCONDITIONAL -- include_optional=True
    # does not bypass it, and no filter below can resurface such a row.
    # The repair workflow reaches these rows by explicit id via get()/
    # get_for_packet(), which remain unchanged.
    items = [q for q in items if not q.get("source_gap")]
    if lesson is not None:
        items = [q for q in items if q.get("lesson") == lesson]
    if dok is not None:
        doks = {dok} if isinstance(dok, int) else set(dok)
        items = [q for q in items if q.get("dok") in doks]
    if topics:
        topic_set = set(topics)
        if topics_mode == "all":
            items = [q for q in items if topic_set.issubset(set(q.get("topics", [])))]
        else:
            items = [q for q in items if topic_set & set(q.get("topics", []))]
    if tags:
        tag_set = set(tags)
        items = [q for q in items if tag_set & set(q.get("tags", []))]
    if has_visual is not None:
        items = [q for q in items if bool(q.get("has_visual")) == has_visual]
    if limit is not None:
        items = items[:limit]
    return items


def image_path(qid: str) -> Path | None:
    q = get(qid)
    if not q or not q.get("image"):
        return None
    p = ROOT / q["image"]
    return p if p.exists() else None


def load_calibration(lesson: str) -> dict | None:
    f = CALIBRATION_DIR / f"{lesson}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------
# Summary / inspection helpers
# ----------------------------------------------------------------------

TEACHER_PROMPTS_DIR = ROOT / "questionbank" / "teacher_prompts"


def teacher_prompts(lesson: str, *, anchor_example: int | None = None,
                    types: list[str] | None = None) -> list[dict]:
    """Load Savvas teacher-edition prompts (ETP, Habits of Mind, ELL) for a lesson.

    Filter by anchor_example number and/or prompt type. Returns a list of
    dicts with keys: source, anchor_example, type, prompt, expected_response,
    use, image.
    """
    f = TEACHER_PROMPTS_DIR / f"{lesson}.jsonl"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        q = json.loads(line)
        if q.get("lesson") != lesson:
            continue
        if anchor_example is not None and q.get("anchor_example") != anchor_example:
            continue
        if types is not None and q.get("type") not in types:
            continue
        out.append(q)
    return out


def _resolve_id_group(qid: str, rows: list[dict], uid_index: dict[str, dict]) -> dict:
    """Resolve every registry row sharing legacy id `qid` to exactly one row.

    Two regimes, drawn EXACTLY at RC's authorization boundary (Codex review
    C1 fix -- the merge-authorized 22 vs. the untouched 63):

      - NONE of `rows` carries status=='merged-alias' (true for every
        non-merged id, including the 63 still-unresolved ambiguous legacy
        ids among the 85): this is UNAUTHORIZED-for-resolution territory --
        preserve the EXACT pre-merge tie-break, LAST row in registry/file
        order wins (the old {id: row} dict-comprehension's dict-last-wins
        behavior), no error, no resolution attempt. This is a deliberate,
        unconditional behavior match with pre-merge qb.py, not merely "a
        reasonable default" -- existing callers (legacy packet/slide
        builders requesting one of these ids) must see byte-identical rows
        to what they saw before this module ever existed.
      - At least one row carries status=='merged-alias' (true only for the
        22 RC-authorized pairs): resolve DELIBERATELY via alias_of -- never
        by position/ambiguity -- and raise ValueError if more than one
        distinct item_uid remains afterward (would mean a merge-authorized
        group somehow still resolves ambiguously -- a data-integrity bug,
        never something to silently pick one of).
    """
    if not any(row.get("status") == "merged-alias" for row in rows):
        return rows[-1]

    resolved_by_uid: dict[str, dict] = {}
    for row in rows:
        if row.get("status") == "merged-alias":
            survivor = _resolve_alias(row, uid_index)
        else:
            survivor = row
        resolved_by_uid[_item_uid_for_row(survivor)] = survivor
    if len(resolved_by_uid) > 1:
        raise ValueError(
            f"id {qid!r} contains a merged-alias row but still resolves to "
            f"{len(resolved_by_uid)} distinct items after resolution -- "
            "unexpected data-integrity problem in an RC-authorized merge "
            "group, refusing to guess which copy is intended"
        )
    return next(iter(resolved_by_uid.values()))


def get_for_packet(ids: list[str]) -> list[dict]:
    """Look up a fixed ordered list of registry entries for a packet builder.

    Raises KeyError if any id is missing from the registry, so a packet
    build fails loudly rather than silently rendering placeholder text.
    Raises ValueError if an id resolves to more than one distinct item even
    after merged-alias resolution (see _resolve_id_group).

    A merged-alias row is never returned here (rc-merge-auth-5-4-2026-07-23)
    -- resolution to its survivor is deliberate (via alias_of), never the
    old dict-comprehension's dict-last-wins accident.
    """
    items = load()
    id_set = set(ids)
    rows_by_id: dict[str, list[dict]] = {}
    for q in items:
        rid = q.get("id")
        if rid in id_set:
            rows_by_id.setdefault(rid, []).append(q)

    missing = [qid for qid in ids if qid not in rows_by_id]
    if missing:
        raise KeyError(f"Bank IDs not in registry: {missing}")

    uid_index = _build_uid_index(items)
    resolved = {qid: _resolve_id_group(qid, rows_by_id[qid], uid_index) for qid in rows_by_id}
    return [resolved[qid] for qid in ids]


def visuals_for(qids: list[str]) -> list[dict]:
    """For a packet's ordered IDs, return a visuals manifest.

    Each row: id, visual_type, source_image, needs_cleanup, clean_asset, has_visual.
    Useful for a pre-print checklist so the teacher can verify every embedded
    asset (photo, graph, table, map, diagram) before sending to the printer.
    """
    items = {q["id"]: q for q in load()}
    out = []
    for qid in qids:
        q = items.get(qid)
        if q is None:
            continue
        vt = q.get("visual_type", "none")
        if vt == "none":
            continue  # nothing to print-verify
        out.append({
            "id": qid,
            "visual_type": vt,
            "source_image": q.get("image"),
            "needs_cleanup": bool(q.get("visual_needs_cleanup", False)),
            "clean_asset": q.get("visual_clean_asset"),
            "has_visual": bool(q.get("has_visual", False)),
            "source_label": q.get("source", ""),
        })
    return out


def write_visuals_checklist(qids: list[str], path: str | Path, *, title: str = "Visuals Checklist") -> None:
    """Emit a Markdown checklist of every visual asset a packet needs.

    The teacher reviews this before print to confirm each photo/graph/table
    is embedded cleanly (not cropped from an answer key, no answer leak, etc.).
    """
    rows = visuals_for(qids)
    path = Path(path)
    lines = [
        f"# {title}",
        "",
        f"Generated from {len(qids)} packet items; {len(rows)} carry visuals.",
        "",
        "| # | ID | Type | Needs cleanup? | Clean asset | Source image | Source label |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        flag = "**YES**" if r["needs_cleanup"] else "no"
        clean = r["clean_asset"] or "—"
        lines.append(
            f"| {i} | `{r['id']}` | {r['visual_type']} | {flag} | `{clean}` | `{r['source_image']}` | {r['source_label']} |"
        )
    lines.append("")
    lines.append("**Legend:** `needs_cleanup=YES` means the source image contains an answer key leak or combines multiple items — create or paste a clean version before print.")
    path.write_text("\n".join(lines), encoding="utf-8")


def stats() -> dict:
    """Reports the TRIPLE denominators: raw registry rows split three ways
    -- raw == active(required) + optional_catalog + merged_alias.

    The dual-denominator split (rc-merge-auth-5-4-2026-07-23) is now a triple
    split (nt14-ingest-4-1-2026-07-23): this is an AUDIT-style view
    (raw_total counts every registry row, alias rows AND optional-catalog
    rows included) alongside active_total / optional_catalog_total /
    merged_alias_total so none of the three ever get silently conflated.
    active_total is now required-active only: len(items) -
    merged_alias_total - optional_catalog_total. by_lesson stays a raw,
    per-row breakdown (audit-style, alias rows and optional-catalog rows
    included and marked via `merged_alias` / `optional_catalog`) -- a
    lesson's 'total' here is its raw registry row count, NOT its
    active-item count; student-facing selection (get/select/get_for_packet)
    is what actually excludes/resolves merged-alias rows and excludes
    optional-catalog rows by default, not this reporting helper."""
    items = load()
    by_lesson: dict[str, dict] = {}
    merged_alias_total = 0
    optional_catalog_total = 0
    source_gap_total = 0
    for q in items:
        L = q.get("lesson", "?")
        d = q.get("dok", 0)
        by_lesson.setdefault(
            L, {"total": 0, "dok1": 0, "dok2": 0, "dok3": 0, "dok4": 0, "visual": 0,
                "merged_alias": 0, "optional_catalog": 0, "source_gap": 0}
        )
        by_lesson[L]["total"] += 1
        by_lesson[L][f"dok{d}"] = by_lesson[L].get(f"dok{d}", 0) + 1
        if q.get("source_gap"):
            by_lesson[L]["source_gap"] += 1
            source_gap_total += 1
        if q.get("has_visual"):
            by_lesson[L]["visual"] += 1
        if q.get("status") == "merged-alias":
            by_lesson[L]["merged_alias"] += 1
            merged_alias_total += 1
        if q.get("availability") == "optional-catalog":
            by_lesson[L]["optional_catalog"] += 1
            optional_catalog_total += 1
    return {
        "total": len(items),
        "raw_total": len(items),
        "active_total": len(items) - merged_alias_total - optional_catalog_total,
        "optional_catalog_total": optional_catalog_total,
        # Sub-split of optional_catalog_total (RC acceptance rule,
        # nt14-ingest-4-1-2026-07-23): 19 = 17 selectable + 2 source-gap.
        # source_gap rows are select()-excluded even with
        # include_optional=True; reachable only by explicit id (repair path).
        "optional_catalog_selectable_total": optional_catalog_total - sum(
            1 for q in items
            if q.get("availability") == "optional-catalog" and q.get("source_gap")
        ),
        "source_gap_total": source_gap_total,
        "merged_alias_total": merged_alias_total,
        "by_lesson": by_lesson,
    }


if __name__ == "__main__":
    import pprint
    pprint.pp(stats())
