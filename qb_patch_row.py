"""Patch one registry row, preserving unrelated bytes and field order.

Usage: python qb_patch_row.py --from patch.json [--dry-run]
       python qb_patch_row.py --id ID --set field=value [--set field=value]

Patch files contain {"id": "...", "fields": {...}}. --set values are strings;
use a JSON patch file for typed values. CLI fields override file fields.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qb_patch_images import patch_line

REGISTRY = Path(__file__).resolve().parent / "questionbank/registry.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id")
    parser.add_argument("--from", dest="patch_file", type=Path)
    parser.add_argument("--set", dest="assignments", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        patch = json.loads(args.patch_file.read_text(encoding="utf-8-sig")) if args.patch_file else {}
        if not isinstance(patch, dict):
            raise ValueError("Patch file must be an object")
        pid = args.id or patch.get("id")
        if args.id and patch.get("id") and args.id != patch["id"]:
            raise ValueError("CLI and patch file IDs disagree")
        if not isinstance(pid, str) or not pid:
            raise ValueError("A nonempty registry ID is required")
        fields = patch.get("fields", {})
        if not isinstance(fields, dict):
            raise ValueError("fields must be an object")
        fields = dict(fields)
        for assignment in args.assignments:
            field, sep, value = assignment.partition("=")
            if not sep or not field:
                raise ValueError("--set requires field=value")
            fields[field] = value
        if not fields:
            raise ValueError("At least one field is required")
        if "id" in fields and fields["id"] != pid:
            raise ValueError("Changing the registry ID is not supported")
        original = REGISTRY.read_bytes()
        bom = b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b""
        lines = original[len(bom):].decode("utf-8").splitlines(keepends=True)
        matches = [(i, json.loads(line)) for i, line in enumerate(lines)
                   if line.strip() and json.loads(line).get("id") == pid]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one row for {pid}; found {len(matches)}")
        index, before = matches[0]
        lines[index] = patch_line(lines[index], fields)
        if args.dry_run:
            print(json.dumps({"id": pid,
                              "before": {key: before.get(key) for key in fields},
                              "after": fields}, ensure_ascii=False, indent=2))
            print("Dry run: 1 matching row; no file written.")
        else:
            if REGISTRY.read_bytes() != original:
                raise ValueError("Registry changed during validation; refusing to overwrite")
            REGISTRY.write_bytes(bom + "".join(lines).encode("utf-8"))
            print(f"Patched {pid} ({len(fields)} fields).")
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
