"""One-off backfill for lesson 3-5 visual metadata.

Infers visual_type from image filename, sets has_visual=True where an image is
linked, and marks visual_needs_cleanup=True on every touched row so they
surface in the DAG visual-bar for human review. Idempotent: only touches rows
where visual_type is currently unset.

Usage: python backfill_visuals_3-5.py [--apply]
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REG = Path("questionbank/registry.jsonl")


def infer_type(filename: str) -> str:
    """Best-guess visual_type from the image filename pattern."""
    f = filename.lower()
    # Teacher-side screenshots (addenda, ELL/RTI supports, habits-of-mind) = photo.
    if any(k in f for k in ("teacher-addendum", "ell-support", "rti-extend",
                             "rti-support", "habits-of-mind", "example-")):
        return "photo"
    # Answer-key screenshots = photo.
    if "_answer" in f:
        return "photo"
    # Lesson-quiz question screenshots = photo by default.
    if "_lq_" in f:
        return "photo"
    # 3-5 is polynomials — question images are almost always graphs of
    # factored-form polynomials, zero sets, or end-behavior sketches.
    if "_question" in f:
        return "graph"
    return "photo"


def main() -> int:
    apply = "--apply" in sys.argv
    rows = [json.loads(l) for l in REG.read_text(encoding="utf-8").splitlines() if l.strip()]
    touched = 0
    by_type: dict[str, int] = {}
    for r in rows:
        if r.get("lesson") != "3-5":
            continue
        if r.get("visual_type"):
            continue
        img = r.get("image")
        if not img:
            continue
        vt = infer_type(img.split("/")[-1])
        r["visual_type"] = vt
        r["has_visual"] = True
        r["visual_needs_cleanup"] = True
        by_type[vt] = by_type.get(vt, 0) + 1
        touched += 1
        print(f"  {vt:7} {r['id']:40} <- {img.split('/')[-1]}")

    print(f"\nWould touch {touched} rows: {by_type}")
    if not apply:
        print("(dry run — pass --apply to write)")
        return 0

    REG.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {REG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
