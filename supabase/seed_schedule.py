"""Seed the lesson_planning.schedule table with known + best-guess dates.

Run once after migration 004 is applied. Idempotent via (class_date, period)
unique key — subsequent runs overwrite lesson_id/day_of_lesson/minutes/notes.

Usage:
    export SUPABASE_URL=https://bzqbhtrurzzavhqbgqrs.supabase.co
    export SUPABASE_SERVICE_ROLE_KEY=<service role>
    python supabase/seed_schedule.py [--dry-run]

Weeks seeded: 4/27 through 6/19 (end of school 2026-06-20).

Week-of-4/27 data is CONFIRMED (from memory, owner-provided). Subsequent weeks
are BEST-GUESS based on the Topic 4/5/6 roadmap + the Klimsara 3-period cadence
+ F-one-period-ahead-by-Friday pattern. Rows with notes='TBD — confirm' need
owner review.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import date

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCHEMA = "lesson_planning"


def env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"error: {name} not set")
    return v


# (class_date, period, lesson_id, day_of_lesson, minutes, notes)
# Period A gets Mon/Tue/Wed/Thu; Period F gets Tue/Wed/Thu/Fri.
# Wed F = 45 min (compressed); all others 55 or 65 min per memory.
ROWS = [
    # ── Week of 4/27 — L35 close-out + Topic 3 assessment (CONFIRMED) ───────
    ("2026-04-27", "A", "L35_P1", "P1",     65, "Finish Day 1"),
    ("2026-04-28", "F", "L35_P2", "P2",     65, None),
    ("2026-04-28", "A", "L35_P2", "P2",     55, None),
    ("2026-04-29", "A", "L35_P3", "P3",     65, "DOK-3: Storage Box #27"),
    ("2026-04-29", "F", "L35_P3", "P3",     45, "Compressed — Wed F short"),
    ("2026-04-30", "A", "L35_P4", "ASSESS", 55, "Topic 3 Assessment"),
    ("2026-04-30", "F", "L35_P4", "ASSESS", 65, "Topic 3 Assessment"),
    ("2026-05-01", "F", "L41_P1", "P1",     65, "F starts 4-1"),

    # ── Week of 5/4 — Lesson 4-1 (BEST-GUESS) ───────────────────────────────
    ("2026-05-04", "A", "L41_P1", "P1", 65, "A starts 4-1 — TBD confirm"),
    ("2026-05-05", "F", "L41_P2", "P2", 65, "TBD — confirm"),
    ("2026-05-05", "A", "L41_P2", "P2", 55, "TBD — confirm"),
    ("2026-05-06", "A", "L41_P3", "P3", 65, "TBD — confirm"),
    ("2026-05-06", "F", "L41_P3", "P3", 45, "Wed F compressed — TBD"),
    ("2026-05-07", "A", "L43_P1", "P1", 55, "TBD — confirm"),
    ("2026-05-07", "F", "L43_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-08", "F", "L43_P1", "P1", 65, "TBD — F one ahead"),

    # ── Week of 5/11 — Lesson 4-3 (BEST-GUESS) ──────────────────────────────
    ("2026-05-11", "A", "L43_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-12", "F", "L43_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-12", "A", "L43_P1", "P1", 55, "TBD — confirm"),
    ("2026-05-13", "A", "L44_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-13", "F", "L44_P1", "P1", 45, "Wed F compressed — TBD"),
    ("2026-05-14", "A", "L44_P1", "P1", 55, "TBD — confirm"),
    ("2026-05-14", "F", "L44_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-15", "F", "L45_P1", "P1", 65, "TBD — confirm"),

    # ── Week of 5/18 — Lesson 4-4 / 4-5 (BEST-GUESS) ────────────────────────
    ("2026-05-18", "A", "L45_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-19", "F", "L46",     "ASSESS", 65, "TBD — Topic 4 assessment"),
    ("2026-05-19", "A", "L46",     "ASSESS", 55, "TBD — Topic 4 assessment"),
    ("2026-05-20", "A", "L51_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-20", "F", "L51_P1", "P1", 45, "Wed F compressed — TBD"),
    ("2026-05-21", "A", "L51_P1", "P1", 55, "TBD — confirm"),
    ("2026-05-21", "F", "L51_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-22", "F", "L54_P1", "P1", 65, "TBD — confirm"),

    # ── Week of 5/25 — Memorial Day + Lesson 5-x ────────────────────────────
    ("2026-05-25", "A", None,     "BUFFER", 0,  "Memorial Day (holiday) — TBD confirm"),
    ("2026-05-26", "F", "L54_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-26", "A", "L54_P1", "P1", 55, "TBD — confirm"),
    ("2026-05-27", "A", "L54_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-27", "F", "L54_P1", "P1", 45, "Wed F compressed — TBD"),
    ("2026-05-28", "A", "L55_P1", "P1", 55, "TBD — confirm"),
    ("2026-05-28", "F", "L55_P1", "P1", 65, "TBD — confirm"),
    ("2026-05-29", "F", "L55_P1", "P1", 65, "TBD — confirm"),

    # ── Week of 6/1 — Lesson 6-3 (BEST-GUESS) ───────────────────────────────
    ("2026-06-01", "A", "L55_P1", "P1", 65, "TBD — confirm"),
    ("2026-06-02", "F", "L63_P1", "P1", 65, "TBD — confirm"),
    ("2026-06-02", "A", "L63_P1", "P1", 55, "TBD — confirm"),
    ("2026-06-03", "A", "L63_P1", "P1", 65, "TBD — confirm"),
    ("2026-06-03", "F", "L63_P1", "P1", 45, "Wed F compressed — TBD"),
    ("2026-06-04", "A", "L64_P1", "P1", 55, "TBD — confirm"),
    ("2026-06-04", "F", "L64_P1", "P1", 65, "TBD — confirm"),
    ("2026-06-05", "F", "L64_P1", "P1", 65, "TBD — confirm"),

    # ── Week of 6/8 — Lesson 6-4 / 6-5 (BEST-GUESS) ─────────────────────────
    ("2026-06-08", "A", "L64_P1", "P1", 65, "TBD — confirm"),
    ("2026-06-09", "F", "L65_P1", "P1", 65, "TBD — confirm"),
    ("2026-06-09", "A", "L65_P1", "P1", 55, "TBD — confirm"),
    ("2026-06-10", "A", "L65_P1", "P1", 65, "TBD — confirm"),
    ("2026-06-10", "F", "L65_P1", "P1", 45, "Wed F compressed — TBD"),
    ("2026-06-11", "A", None,     "REVIEW", 55, "Final review — TBD"),
    ("2026-06-11", "F", None,     "REVIEW", 65, "Final review — TBD"),
    ("2026-06-12", "F", None,     "REVIEW", 65, "Final review — TBD"),

    # ── Week of 6/15 — Finals / end of year ─────────────────────────────────
    ("2026-06-15", "A", None, "REVIEW", 65, "Finals week — TBD confirm"),
    ("2026-06-16", "F", None, "REVIEW", 65, "Finals week — TBD confirm"),
    ("2026-06-16", "A", None, "REVIEW", 55, "Finals week — TBD confirm"),
    ("2026-06-17", "A", None, "REVIEW", 65, "Finals week — TBD confirm"),
    ("2026-06-17", "F", None, "REVIEW", 45, "Finals week — TBD confirm"),
    ("2026-06-18", "A", None, "REVIEW", 55, "Finals week — TBD confirm"),
    ("2026-06-18", "F", None, "REVIEW", 65, "Finals week — TBD confirm"),
    ("2026-06-19", "F", None, "BUFFER", 65, "Last day — TBD confirm"),
]


def upsert(url: str, key: str, rows: list[dict], dry_run: bool) -> int:
    endpoint = f"{url}/rest/v1/schedule"
    headers = {
        "apikey":          key,
        "Authorization":   f"Bearer {key}",
        "Content-Type":    "application/json",
        "Content-Profile": SCHEMA,
        "Accept-Profile":  SCHEMA,
        "Prefer":          "resolution=merge-duplicates,return=minimal",
    }
    if dry_run:
        print(f"  [dry-run] would upsert {len(rows)} schedule rows")
        return len(rows)
    r = requests.post(endpoint, headers=headers, data=json.dumps(rows), timeout=60)
    if r.status_code >= 300:
        print(f"  ERROR: {r.status_code} {r.text[:500]}")
        sys.exit(1)
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    url = env("SUPABASE_URL")
    key = env("SUPABASE_SERVICE_ROLE_KEY")

    rows = []
    for class_date, period, lesson_id, day_of_lesson, minutes, notes in ROWS:
        rows.append({
            "class_date":    class_date,
            "period":        period,
            "lesson_id":     lesson_id,
            "day_of_lesson": day_of_lesson,
            "minutes":       minutes,
            "notes":         notes,
        })

    n = upsert(url, key, rows, args.dry_run)
    print(f"done: {n} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
