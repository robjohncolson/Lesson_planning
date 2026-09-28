"""Patch registry visual fields without reserializing unrelated JSON values.

Usage: python qb_patch_images.py [map_file] [--dry-run]
Image paths are relative to the repository root. Multi-image arrays are retained
verbatim as data in ``images``; their first path becomes the primary ``image``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "questionbank/registry.jsonl"
FIELDS = ("image", "has_visual", "visual_type", "visual_needs_cleanup")


def value_spans(line: str) -> tuple[dict[str, tuple[int, int]], int]:
    """Locate top-level value tokens and the closing brace in a valid JSON row."""
    decoder = json.JSONDecoder()
    pos = len(line) - len(line.lstrip()) + 1
    spans = {}
    while True:
        while line[pos].isspace():
            pos += 1
        if line[pos] == "}":
            return spans, pos
        key, pos = decoder.raw_decode(line, pos)
        while line[pos].isspace():
            pos += 1
        pos += 1  # colon
        while line[pos].isspace():
            pos += 1
        start = pos
        _, pos = decoder.raw_decode(line, pos)
        if key in spans:
            raise ValueError(f"Duplicate registry field: {key}")
        spans[key] = (start, pos)
        while line[pos].isspace():
            pos += 1
        if line[pos] == ",":
            pos += 1


def patch_line(line: str, patch: dict) -> str:
    spans, end = value_spans(line)
    edits = []
    additions = []
    for field, value in patch.items():
        encoded = json.dumps(value, ensure_ascii=False)
        if field in spans:
            start, stop = spans[field]
            # Keep an already equal value's original spelling/escaping.
            if json.loads(line[start:stop]) != value:
                edits.append((start, stop, encoded))
        else:
            additions.append(f"{json.dumps(field)}: {encoded}")
    if additions:
        edits.append((end, end, (", " if spans else "") + ", ".join(additions)))
    for start, stop, replacement in sorted(edits, reverse=True):
        line = line[:start] + replacement + line[stop:]
    return line


def load_patches(path: Path) -> dict[str, dict]:
    source = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(source, dict):
        raise ValueError("Image map must be an object keyed by registry ID")
    patches = {}
    for pid, entry in source.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{pid}: map entry must be an object")
        patch = {field: entry[field] for field in FIELDS if field in entry}
        paths = []
        if "images" in entry:
            items = entry["images"]
            if not isinstance(items, list) or not items:
                raise ValueError(f"{pid}: images must be a nonempty array")
            for item in items:
                path_value = item.get("image") if isinstance(item, dict) else item
                if not isinstance(path_value, str) or not path_value:
                    raise ValueError(f"{pid}: each image must contain a nonempty path")
                paths.append(path_value)
            if "image" not in entry:
                patch["image"] = paths[0]
                patch["images"] = items
        if entry.get("image") is not None:
            paths.append(entry["image"])
        for image_path in paths:
            if not isinstance(image_path, str) or not image_path or not (ROOT / image_path).is_file():
                raise ValueError(f"{pid}: image path does not exist: {image_path!r}")
        patches[pid] = patch
    return patches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_file", nargs="?", type=Path, default=ROOT / "skeletons/1-1_image_map.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        patches = load_patches(args.map_file)
        original = REGISTRY.read_bytes()
        lines = original.decode("utf-8").splitlines(keepends=True)
        rows = [json.loads(line) if line.strip() else None for line in lines]
        by_id = {}
        for row in rows:
            if row is not None:
                by_id[row["id"]] = row
        missing = patches.keys() - by_id.keys()
        if missing:
            raise ValueError("Map IDs missing from registry: " + ", ".join(sorted(missing)))
        output = "".join(
            patch_line(line, patches[row["id"]])
            if row is not None and row["id"] in patches else line
            for line, row in zip(lines, rows)
        ).encode("utf-8")
        if args.dry_run:
            print("id\t" + "\t".join(f"{field} (before -> after)" for field in FIELDS))
            for pid, patch in patches.items():
                before = by_id[pid]
                after = {**before, **patch}
                print(pid + "\t" + "\t".join(
                    f"{json.dumps(before.get(field), ensure_ascii=False)} -> "
                    f"{json.dumps(after.get(field), ensure_ascii=False)}" for field in FIELDS
                ))
            print(f"Dry run: {len(patches)} matching rows; no file written.")
        else:
            if REGISTRY.read_bytes() != original:
                raise ValueError("Registry changed during validation; refusing to overwrite")
            REGISTRY.write_bytes(output)
            print(f"Patched {len(patches)} matching rows in {REGISTRY}.")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
