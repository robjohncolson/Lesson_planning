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
