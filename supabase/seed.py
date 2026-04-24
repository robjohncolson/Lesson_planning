"""Seed the lesson_planning.* tables from local JSONL + YAML.

Usage:
    set SUPABASE_URL=https://bzqbhtrurzzavhqbgqrs.supabase.co
    set SUPABASE_SERVICE_ROLE_KEY=<from Supabase dashboard: Settings > API>
    python supabase/seed.py [--dry-run] [--batch-size 200]

One-time population. Safe to re-run: uses PostgREST upsert so existing rows
are replaced. Schema must exist first (run supabase/schema.sql).

This script talks to PostgREST directly — no pip install required beyond
`requests` and `pyyaml` which the repo already uses.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

import requests
import yaml

# Windows console is cp1252 by default — force UTF-8 so arrows/emojis don't crash.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
REG_PATH    = REPO / "questionbank" / "registry.jsonl"
SHELL_PATH  = REPO / "questionbank" / "assessment_shells.jsonl"
LESSONS_DIR = REPO / "lessons"
TEX_DIR     = REPO / "tex"

SCHEMA = "lesson_planning"


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"error: {name} not set")
    return v


def load_jsonl(p: Path) -> list[dict]:
    rows = []
    if not p.exists():
        return rows
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _as_list(v) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [v] if v else []
    return list(v)


def registry_to_row(r: dict, is_shell: bool) -> dict:
    """Flatten a registry / shell record into the items-table shape."""
    return {
        "id":                    r["id"],
        "lesson":                r.get("lesson") or (r.get("lesson_covered") or [None])[0] if is_shell else r.get("lesson"),
        "source":                r.get("source"),
        "prompt":                r.get("prompt"),
        "dok":                   r.get("dok"),
        "dok_rationale":         r.get("dok_rationale"),
        "role":                  r.get("role"),
        "correct":               r.get("correct"),
        "teacher_answer":        r.get("teacher_answer"),
        "notes":                 r.get("notes"),
        "has_visual":            bool(r.get("has_visual", False)),
        "image":                 r.get("image"),
        "visual_type":           r.get("visual_type"),
        "visual_needs_cleanup":  r.get("visual_needs_cleanup"),
        "visual_clean_asset":    r.get("visual_clean_asset"),
        "page":                  r.get("page"),
        "topics":                _as_list(r.get("topics")),
        "tags":                  _as_list(r.get("tags")),
        "skill_tokens":          _as_list(r.get("skill_tokens")),
        "standards":             _as_list(r.get("standards")),
        "answers":               _as_list(r.get("answers")),
        "used_in":               _as_list(r.get("used_in")),
        "is_shell":              is_shell,
    }


def extract_edges(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """Walk prereq_ids / rehearses / echoes into the edges table shape.

    Returns (valid_edges, dropped_edges). Dropped = endpoints that aren't in
    the items set (usually retired-lesson references still hanging around).
    """
    known_ids = {r["id"] for r in items}
    valid, dropped = [], []
    for r in items:
        rid = r["id"]
        for target in _as_list(r.get("prereq_ids")):
            e = {"from_id": target, "to_id": rid, "kind": "prereq"}
            (valid if (target in known_ids) else dropped).append(e)
        for target in _as_list(r.get("rehearses")):
            e = {"from_id": rid, "to_id": target, "kind": "rehearses"}
            (valid if (target in known_ids) else dropped).append(e)
        for target in _as_list(r.get("echoes")):
            e = {"from_id": rid, "to_id": target, "kind": "echoes"}
            (valid if (target in known_ids) else dropped).append(e)
    return valid, dropped


def collect_lessons() -> list[dict]:
    """Every L*_P*_student.tex becomes a row; tex_student/tex_teacher/yaml_text
    carry the full source text — the lessons table is now the source of truth
    for tex, not the filesystem."""
    rows: dict[str, dict] = {}

    def base_row(lid: str) -> dict:
        return {
            "id": lid, "cadence": None, "title": None, "yaml_text": None,
            "tex_student": None, "tex_teacher": None, "tex_slides": None,
            "has_tex_student": False, "has_tex_teacher": False,
            "has_pdf_student": False, "has_pdf_teacher": False,
            "has_slides_pdf":  False,
        }

    # Glob both Algebra 2 (L{NN}_P{N}_*) and APStats (APStats_{U}-{L}_P{N}_*) artifacts.
    def _globs(suffix: str) -> list[Path]:
        return sorted(TEX_DIR.glob(f"L*_P*_{suffix}")) + sorted(TEX_DIR.glob(f"APStats_*_P*_{suffix}"))

    for tex in _globs("student.tex"):
        lid = tex.stem.removesuffix("_student")
        row = rows.setdefault(lid, base_row(lid))
        row["has_tex_student"] = True
        row["tex_student"]     = tex.read_text(encoding="utf-8")

    for tex in _globs("teacher.tex"):
        lid = tex.stem.removesuffix("_teacher")
        row = rows.setdefault(lid, base_row(lid))
        row["has_tex_teacher"] = True
        row["tex_teacher"]     = tex.read_text(encoding="utf-8")

    for tex in _globs("slides.tex"):
        lid = tex.stem.removesuffix("_slides")
        row = rows.setdefault(lid, base_row(lid))
        row["tex_slides"]      = tex.read_text(encoding="utf-8")

    for pdf in _globs("student.pdf"):
        rows.setdefault(pdf.stem.removesuffix("_student"), base_row(pdf.stem.removesuffix("_student")))["has_pdf_student"] = True
    for pdf in _globs("teacher.pdf"):
        rows.setdefault(pdf.stem.removesuffix("_teacher"), base_row(pdf.stem.removesuffix("_teacher")))["has_pdf_teacher"] = True
    for pdf in _globs("slides.pdf"):
        rows.setdefault(pdf.stem.removesuffix("_slides"), base_row(pdf.stem.removesuffix("_slides")))["has_slides_pdf"] = True

    yaml_globs = sorted(LESSONS_DIR.glob("L*_P*.yaml")) + sorted(LESSONS_DIR.glob("APStats_*_P*.yaml"))
    for y in yaml_globs:
        lid = y.stem
        txt = y.read_text(encoding="utf-8")
        try:
            meta = yaml.safe_load(txt) or {}
        except yaml.YAMLError:
            meta = {}
        row = rows.setdefault(lid, base_row(lid))
        row["yaml_text"] = txt
        row["cadence"]   = (meta or {}).get("cadence")
        row["title"]     = (meta or {}).get("title")

    return list(rows.values())


def upsert(url: str, key: str, table: str, rows: list[dict], batch_size: int, dry_run: bool) -> int:
    if not rows:
        return 0
    endpoint = f"{url}/rest/v1/{table}"
    headers = {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        # PostgREST resolves `table` against the `Accept-Profile` / `Content-Profile` header
        "Content-Profile": SCHEMA,
        "Accept-Profile":  SCHEMA,
        # `resolution=merge-duplicates` = upsert-on-pk
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        if dry_run:
            print(f"  [dry-run] would upsert {len(batch)} rows to {SCHEMA}.{table}")
            total += len(batch)
            continue
        r = requests.post(endpoint, headers=headers, data=json.dumps(batch), timeout=60)
        if r.status_code >= 300:
            print(f"  ERROR on batch {i}-{i+len(batch)}: {r.status_code} {r.text[:400]}")
            sys.exit(1)
        total += len(batch)
        print(f"  {SCHEMA}.{table}: {total}/{len(rows)}")
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--batch-size", type=int, default=200)
    args = ap.parse_args()

    url = env("SUPABASE_URL").rstrip("/")
    key = env("SUPABASE_SERVICE_ROLE_KEY")

    print("Loading local data...")
    reg    = load_jsonl(REG_PATH)
    shells = load_jsonl(SHELL_PATH)
    print(f"  registry.jsonl:         {len(reg)} rows")
    print(f"  assessment_shells.jsonl:{len(shells)} rows")

    raw_items = (
        [registry_to_row(r, is_shell=False) for r in reg]
        + [registry_to_row(r, is_shell=True) for r in shells]
    )
    # Dedupe by id (last-seen wins). Registry has 85 "-2 suffix" duplicates
    # — matches the in-repo by_id dict-lookup behavior.
    seen, items = {}, []
    dup_count = 0
    for r in raw_items:
        if r["id"] in seen:
            dup_count += 1
            items[seen[r["id"]]] = r  # replace earlier entry
        else:
            seen[r["id"]] = len(items)
            items.append(r)
    if dup_count:
        print(f"  -> {dup_count} duplicate-id items collapsed (last-seen wins)")

    edges, dropped = extract_edges(reg + shells)
    # Dedupe edges (identical tuples are fine to collapse)
    edges = list({(e["from_id"], e["to_id"], e["kind"]): e for e in edges}.values())
    lessons = collect_lessons()

    print(f"\n  -> items: {len(items)}  edges: {len(edges)}  lessons: {len(lessons)}")
    if dropped:
        print(f"  -> dropped {len(dropped)} edges pointing to unknown ids (retired lessons):")
        for e in dropped[:5]:
            print(f"       {e['from_id']} -[{e['kind']}]-> {e['to_id']}")
        if len(dropped) > 5:
            print(f"       ... and {len(dropped) - 5} more")
    print()

    print("Upserting items...")
    upsert(url, key, "items",   items,   args.batch_size, args.dry_run)
    print("Upserting lessons...")
    upsert(url, key, "lessons", lessons, args.batch_size, args.dry_run)
    print("Upserting edges (references must already exist)...")
    upsert(url, key, "edges",   edges,   args.batch_size, args.dry_run)

    print("\nDone." if not args.dry_run else "\nDry-run complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
