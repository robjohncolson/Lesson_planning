"""Generate pre-filled registry stubs for all Savvas Practice items in a lesson.

Reads the lesson's calibration file (item_analysis table), skips any items
already in the registry, and emits JSON stubs that fill in every field
except the actual prompt text and answer key. Intended workflow:

    python generate_practice_skeletons.py 4-1
    # -> writes skeletons/4-1_practice_skeletons.json with N stubs

    # Edit the file as each screenshot comes in:
    #   - paste the transcribed prompt into "prompt"
    #   - paste the answer key into "notes"
    #   - set has_visual / visual_type if the item has a figure/graph/table
    # then pipe through qb_append.py.

    python generate_practice_skeletons.py 4-1 --item 17
    # -> prints a single stub to stdout

Skips item numbers whose id already exists as `{lesson}-savvas-q{N}` in the
registry, so this is safe to re-run after partial ingest.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import qb

ROOT = Path(__file__).resolve().parent


def invert_item_analysis(cal: dict) -> dict[int, tuple[int, int]]:
    """Map item_num -> (example_num, dok) from calibration.item_analysis."""
    out: dict[int, tuple[int, int]] = {}
    ia = cal.get("item_analysis", {})
    for ex_key, dok_map in ia.items():
        if not ex_key.startswith("example_"):
            continue
        ex_num = int(ex_key.removeprefix("example_"))
        for dok_key, items in dok_map.items():
            dok = int(dok_key.removeprefix("dok"))
            for n in items:
                out[int(n)] = (ex_num, dok)
    return out


def stub_for(lesson: str, item_num: int, example_num: int, dok: int) -> dict:
    qid = f"{lesson}-savvas-q{item_num}"
    tags = [
        f"lesson-{lesson}",
        "savvas-practice",
        f"example-{example_num}-anchor",
    ]
    if dok == 3:
        tags.append("savvas-declared-dok3")
        tags.append("dok-3-candidate")

    dok_rationales = {
        1: f"Savvas-declared DOK-1 item anchored to Example {example_num}. Single-step recall/recognition matching the skill modeled in that example.",
        2: f"Savvas-declared DOK-2 item anchored to Example {example_num}. Routine multi-step procedure applying the pattern from that example.",
        3: f"Savvas-declared DOK-3 item anchored to Example {example_num}. Strategic reasoning / modeling / non-routine application. One of the lesson's DOK-3 driver candidates.",
    }

    image_path = f"questionbank/images/{lesson}_savvas_q{item_num}_question.png"

    return {
        "id": qid,
        "lesson": lesson,
        "source": f"Savvas Practice #{item_num} (lesson {lesson}, anchors Example {example_num})",
        "image": image_path,
        "has_visual": False,
        "visual_type": "none",
        "visual_needs_cleanup": False,
        "visual_clean_asset": None,
        "prompt": f"TODO: transcribe Savvas Practice #{item_num} prompt from screenshot.",
        "answers": [],
        "correct": None,
        "dok": dok,
        "dok_rationale": dok_rationales[dok],
        "topics": cal_topics_hint(example_num),
        "tags": tags,
        "notes": f"TODO: add answer key from TE. Anchored to Example {example_num}.",
    }


# Rough topic hints by example — user can override per-item as needed.
# For Lesson 4-1 specifically.
_TOPIC_BY_EXAMPLE_4_1 = {
    1: ["inverse-variation", "constant-of-variation"],
    2: ["inverse-variation", "equation-writing"],
    3: ["inverse-variation", "modeling", "application"],
    4: ["reciprocal-function", "asymptote", "domain", "range"],
    5: ["reciprocal-function", "translation", "asymptote"],
}


def cal_topics_hint(example_num: int) -> list[str]:
    return _TOPIC_BY_EXAMPLE_4_1.get(example_num, [])


def load_existing_ids(lesson: str) -> set[str]:
    return {q["id"] for q in qb.select(lesson=lesson)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson", help="Lesson code, e.g. 4-1")
    ap.add_argument("--item", type=int, help="Emit only one item number to stdout")
    ap.add_argument("--out", help="Output file (default: skeletons/<lesson>_practice_skeletons.json)")
    args = ap.parse_args()

    cal = qb.load_calibration(args.lesson)
    if not cal:
        sys.exit(f"ERROR: no calibration at questionbank/calibration/{args.lesson}.json")

    inverted = invert_item_analysis(cal)
    if not inverted:
        sys.exit("ERROR: calibration.item_analysis is empty — populate it first.")

    existing = load_existing_ids(args.lesson)

    if args.item:
        spec = inverted.get(args.item)
        if not spec:
            sys.exit(f"ERROR: item #{args.item} not in item_analysis table for lesson {args.lesson}")
        ex, dok = spec
        stub = stub_for(args.lesson, args.item, ex, dok)
        print(json.dumps(stub, indent=2, ensure_ascii=False))
        return

    stubs = []
    skipped = []
    for n in sorted(inverted):
        ex, dok = inverted[n]
        qid = f"{args.lesson}-savvas-q{n}"
        if qid in existing:
            skipped.append(n)
            continue
        stubs.append(stub_for(args.lesson, n, ex, dok))

    out_path = Path(args.out) if args.out else ROOT / "skeletons" / f"{args.lesson}_practice_skeletons.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stubs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {len(stubs)} stubs to {out_path}")
    if skipped:
        print(f"Skipped {len(skipped)} items already in registry: {skipped}")
    print(f"By DOK: " + ", ".join(
        f"DOK-{d}={sum(1 for s in stubs if s['dok']==d)}" for d in (1, 2, 3)
    ))


if __name__ == "__main__":
    main()
