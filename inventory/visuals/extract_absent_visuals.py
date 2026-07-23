"""
extract_absent_visuals.py

Read-only analysis script for WS2 (visual-asset classification + broken-path
repair prep). Reads questionbank/registry.jsonl (never writes to it) and
computes two row sets:

  (A) ABSENT set (the "137") — rows where has_visual is True AND the image
      field is empty/None. This is the inventory's authoritative
      `visuals_absent` definition.

  (B) BROKEN-PATH set (the "7") — rows where has_visual is True AND image is
      non-empty AND the referenced file does not exist on disk. All 7 are in
      lesson 3-5; the corrected path is
      questionbank/calibration/sources/<same basename>.

Also computes a SHA-256 of registry.jsonl before and after the run to prove
the registry file is byte-unchanged (this script only reads it).

This script performs NO writes to questionbank/. All output is printed to
stdout for review, and (when imported) the computed sets are made available
to the classification/build scripts in this directory.
"""

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGISTRY_PATH = os.path.join(REPO_ROOT, "questionbank", "registry.jsonl")

EXPECTED_ABSENT_BY_LESSON = {
    "4-3": 8,
    "4-4": 11,
    "4-5": 14,
    "5-1": 21,
    "5-4": 19,
    "5-5": 13,
    "6-3": 17,
    "6-4": 23,
    "6-5": 11,
}
EXPECTED_ABSENT_TOTAL = 137

EXPECTED_BROKEN_IDS = [
    "3-5-tryit-3a",
    "3-5-tryit-3b",
    "3-5-tryit-4",
    "3-5-tryit-5a",
    "3-5-tryit-5b",
    "3-5-tryit-6a",
    "3-5-tryit-6b",
]

QUIRK_IDS = {
    "6-3-ex-3",
    "6-3-tryit-3",
    "6-3-tryit-4",
    "6-3-tryit-5",
    "6-4-tryit-1",
}


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows(registry_path):
    """Return list of (registry_line, row_dict) — read-only."""
    rows = []
    with open(registry_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append((line_no, row))
    return rows


def is_absent(row):
    """ABSENT = has_visual True AND image field empty/None."""
    if not bool(row.get("has_visual")):
        return False
    image = row.get("image")
    return image is None or image == ""


def is_broken_path(row, repo_root):
    """BROKEN-PATH = has_visual True AND image non-empty AND file missing on disk."""
    if not bool(row.get("has_visual")):
        return False
    image = row.get("image")
    if not image:
        return False
    full_path = os.path.join(repo_root, image.replace("/", os.sep))
    return not os.path.exists(full_path)


def compute_sets(rows, repo_root):
    absent = []
    broken = []
    for line_no, row in rows:
        if is_absent(row):
            absent.append((line_no, row))
        elif is_broken_path(row, repo_root):
            broken.append((line_no, row))
    return absent, broken


def main():
    pre_hash = sha256_of_file(REGISTRY_PATH)

    rows = load_rows(REGISTRY_PATH)
    absent, broken = compute_sets(rows, REPO_ROOT)

    # ---- Report: ABSENT set ----
    by_lesson = {}
    for line_no, row in absent:
        lesson = row.get("lesson")
        by_lesson[lesson] = by_lesson.get(lesson, 0) + 1

    print("=" * 70)
    print("ABSENT set (has_visual=True, image empty/None)")
    print("=" * 70)
    print(f"Total ABSENT rows: {len(absent)}")
    print("Per-lesson breakdown:")
    for lesson in sorted(by_lesson):
        print(f"  {lesson}: {by_lesson[lesson]}")
    print()
    print("All ABSENT ids (registry_line, id, lesson):")
    for line_no, row in absent:
        print(f"  [{line_no}] {row.get('id')}  ({row.get('lesson')})")
    print()

    # Assertions for ABSENT set
    assert len(absent) == EXPECTED_ABSENT_TOTAL, (
        f"ABSENT total mismatch: got {len(absent)}, expected {EXPECTED_ABSENT_TOTAL}"
    )
    assert by_lesson == EXPECTED_ABSENT_BY_LESSON, (
        f"ABSENT per-lesson breakdown mismatch:\n  got={by_lesson}\n  expected={EXPECTED_ABSENT_BY_LESSON}"
    )
    assert set(by_lesson.keys()) == set(EXPECTED_ABSENT_BY_LESSON.keys()), (
        "ABSENT set spans unexpected lessons"
    )

    # Check the 5 quirk ids are present in the absent set
    absent_ids = {row.get("id") for _, row in absent}
    missing_quirks = QUIRK_IDS - absent_ids
    assert not missing_quirks, f"Quirk ids missing from ABSENT set: {missing_quirks}"
    print(f"Confirmed: all 5 quirk ids (visual_type==none) present in ABSENT set: {sorted(QUIRK_IDS)}")
    print()

    # ---- Report: BROKEN-PATH set ----
    print("=" * 70)
    print("BROKEN-PATH set (has_visual=True, image non-empty, file missing on disk)")
    print("=" * 70)
    print(f"Total BROKEN-PATH rows: {len(broken)}")
    print("All BROKEN-PATH ids (registry_line, id, lesson, image):")
    broken_ids = []
    for line_no, row in broken:
        print(f"  [{line_no}] {row.get('id')}  ({row.get('lesson')})  image={row.get('image')}")
        broken_ids.append(row.get("id"))
    print()

    assert len(broken) == 7, f"BROKEN-PATH total mismatch: got {len(broken)}, expected 7"
    assert set(broken_ids) == set(EXPECTED_BROKEN_IDS), (
        f"BROKEN-PATH id set mismatch:\n  got={sorted(broken_ids)}\n  expected={sorted(EXPECTED_BROKEN_IDS)}"
    )
    assert all(row.get("lesson") == "3-5" for _, row in broken), (
        "BROKEN-PATH set contains rows outside lesson 3-5"
    )

    # Verify corrected paths exist
    print("Verifying corrected paths (questionbank/calibration/sources/<basename>):")
    for line_no, row in broken:
        image = row.get("image")
        basename = os.path.basename(image)
        corrected_rel = os.path.join("questionbank", "calibration", "sources", basename)
        corrected_full = os.path.join(REPO_ROOT, corrected_rel)
        exists = os.path.exists(corrected_full)
        print(f"  {row.get('id')}: {corrected_rel}  exists={exists}")
        assert exists, f"Corrected path does not exist for {row.get('id')}: {corrected_rel}"
    print()

    # ---- Byte-unchanged check ----
    post_hash = sha256_of_file(REGISTRY_PATH)
    print("=" * 70)
    print("Registry byte-unchanged check")
    print("=" * 70)
    print(f"SHA-256 before: {pre_hash}")
    print(f"SHA-256 after:  {post_hash}")
    assert pre_hash == post_hash, "registry.jsonl changed during this run! (should never happen — read-only script)"
    print("MATCH — registry.jsonl is byte-unchanged.")
    print()

    print("All assertions passed.")
    return {
        "pre_hash": pre_hash,
        "post_hash": post_hash,
        "absent": absent,
        "broken": broken,
        "by_lesson": by_lesson,
    }


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("\nASSERTION FAILED — STOPPING (counts did not reconcile):", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(1)
