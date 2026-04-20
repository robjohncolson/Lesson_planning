"""Question-bank accessor module.

Load the registry, filter by lesson/DOK/topics, export to Blooket CSV, and
resolve image paths for packet/slide builders.

Usage:
    from qb import select, to_blooket_csv, get
    questions = select(lesson="3-5", dok=2, topics=["multiplicity"])
    to_blooket_csv([q["id"] for q in questions], "Blooket_Day3_Multiplicity.csv")
"""
from __future__ import annotations

import csv
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
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get(qid: str) -> dict | None:
    for q in load():
        if q.get("id") == qid:
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
) -> list[dict]:
    items = load()
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
# Blooket CSV export — matches Blooket_Import_Template row shape:
# 26 columns: Q#, Text, A1, A2, A3, A4, Time, Correct, then 18 trailing empties.
# ----------------------------------------------------------------------

BLOOKET_HEADER_ROWS = [
    ['"Blooket\nImport Template"'] + [""] * 25,
]


def to_blooket_csv(ids: list[str], path: str | Path) -> None:
    """Emit a Blooket-importable CSV from registry IDs.

    Skips questions that have no `answers` or no integer `correct`
    (Blooket format requires multiple choice).
    """
    path = Path(path)
    qs = [get(qid) for qid in ids]
    missing = [qid for qid, q in zip(ids, qs) if q is None]
    if missing:
        raise KeyError(f"IDs not in registry: {missing}")

    # Write with UTF-8 BOM so Blooket parses em-dashes / unicode math cleanly.
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        # Blooket's own header block (two lines).
        w.writerow(['Blooket\nImport Template'] + [""] * 25)
        w.writerow([
            "Question #", "Question Text",
            "Answer 1", "Answer 2",
            "Answer 3\n(Optional)", "Answer 4\n(Optional)",
            "Time Limit (sec)\n(Max: 300 seconds)",
            "Correct Answer(s)\n(Only include Answer #)",
        ] + [""] * 18)

        for i, q in enumerate(qs, 1):
            answers = q.get("answers") or []
            if len(answers) < 2 or not isinstance(q.get("correct"), int):
                continue
            a1 = answers[0] if len(answers) > 0 else ""
            a2 = answers[1] if len(answers) > 1 else ""
            a3 = answers[2] if len(answers) > 2 else ""
            a4 = answers[3] if len(answers) > 3 else ""
            time_limit = q.get("time_limit", _default_time(q.get("dok", 2)))
            w.writerow([
                i, q["prompt"], a1, a2, a3, a4,
                time_limit, q["correct"],
            ] + [""] * 18)


def _default_time(dok: int) -> int:
    return {1: 15, 2: 20, 3: 25, 4: 30}.get(dok, 20)


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


def get_for_packet(ids: list[str]) -> list[dict]:
    """Look up a fixed ordered list of registry entries for a packet builder.

    Raises KeyError if any id is missing from the registry, so a packet
    build fails loudly rather than silently rendering placeholder text.
    """
    found = {q["id"]: q for q in load() if q.get("id") in set(ids)}
    missing = [qid for qid in ids if qid not in found]
    if missing:
        raise KeyError(f"Bank IDs not in registry: {missing}")
    return [found[qid] for qid in ids]


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
    items = load()
    by_lesson: dict[str, dict] = {}
    for q in items:
        L = q.get("lesson", "?")
        d = q.get("dok", 0)
        by_lesson.setdefault(L, {"total": 0, "dok1": 0, "dok2": 0, "dok3": 0, "dok4": 0, "visual": 0})
        by_lesson[L]["total"] += 1
        by_lesson[L][f"dok{d}"] = by_lesson[L].get(f"dok{d}", 0) + 1
        if q.get("has_visual"):
            by_lesson[L]["visual"] += 1
    return {"total": len(items), "by_lesson": by_lesson}


if __name__ == "__main__":
    import pprint
    pprint.pp(stats())
