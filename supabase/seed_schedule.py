"""Seed the lesson_planning.schedule table with known + best-guess dates.

Run once after migration 004 is applied. Idempotent via (class_date, period)
unique key — subsequent runs overwrite lesson_id/day_of_lesson/minutes/notes.

Usage:
    export SUPABASE_URL=https://bzqbhtrurzzavhqbgqrs.supabase.co
    export SUPABASE_SERVICE_ROLE_KEY=<service role>
    python supabase/seed_schedule.py [--dry-run]

Weeks seeded: 4/27 through 6/19 (end of school 2026-06-20).

RE-BASELINED 2026-04-30 (v2): The 5/8 observation lesson is the canonical P3
(L35_P3_obs), not P2 — corrected from earlier mislabel. Topic 3 assessment
collapses onto a single Thursday (5/14) for both periods. New pacing:
  - L35_P2 stretches through Thu 5/7
  - Fri 5/8 = TEACHER OBSERVATION (L35_P3_obs — canonical P3, gradual-release
    Launch + DOK-3 Mystery Graph in Explore + DOK-1 cool-down Exit)
  - L35_P3 continuation (Storage Box DOK-3 follow-up): Mon-Wed 5/11–5/13
  - Topic 3 Assessment: Thu 5/14 (F + A simultaneous)
  - L41 (full 3-period, LEHS-critical): F starts 5/15, A starts 5/18 → ~5/27
  - Everything else (4-3, 4-4, 4-5, 5-1, 5-4, 5-5, 6-3, 6-4): single-period
    quick. 6-5 dropped per realistic cuts (see roadmap memory).
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
    # ── Week of 4/27 — L35_P2 stretch (re-baselined 2026-04-30) ─────────────
    # Reality: still on L35_P2 on 4/30. Stretch P2 through 5/7. Observation 5/8.
    ("2026-04-27", "A", "L35_P1", "P1",     65, "L35_P1 close-out"),
    ("2026-04-28", "F", "L35_P2", "P2",     65, None),
    ("2026-04-28", "A", "L35_P2", "P2",     55, None),
    ("2026-04-29", "A", "L35_P2", "P2",     65, "Re-baselined: P2 stretched"),
    ("2026-04-29", "F", "L35_P2", "P2",     45, "Wed F compressed — P2 stretched"),
    ("2026-04-30", "F", "L35_P2", "P2",     65, "P2 continues"),
    ("2026-04-30", "A", "L35_P2", "P2",     55, "P2 continues"),
    ("2026-05-01", "F", "L35_P2", "P2",     65, "P2 continues"),

    # ── Week of 5/4 — Finish L35_P2 + OBSERVATION (5/8) ─────────────────────
    ("2026-05-04", "A", "L35_P2", "P2", 65, "P2 continues"),
    ("2026-05-05", "F", "L35_P2", "P2", 65, "P2 continues"),
    ("2026-05-05", "A", "L35_P2", "P2", 55, "P2 continues"),
    ("2026-05-06", "A", "L35_P2", "P2", 65, "P2 continues"),
    ("2026-05-06", "F", "L35_P2", "P2", 45, "Wed F compressed"),
    ("2026-05-07", "F", "L35_P2", "P2", 65, "P2 continues (A: no class)"),
    ("2026-05-07", "A", "L35_P2", "P2", 55, "P2 last day before obs"),
    ("2026-05-08", "F", "L35_P3", "P3", 65, "★ TEACHER OBSERVATION (L35_P3_obs — canonical P3)"),

    # ── Week of 5/11 — L35_P3 (Storage Box DOK-3) ───────────────────────────
    ("2026-05-11", "A", "L35_P3", "P3", 65, "Storage Box DOK-3 (A starts)"),
    ("2026-05-12", "F", "L35_P3", "P3", 65, "Storage Box DOK-3"),
    ("2026-05-12", "A", "L35_P3", "P3", 55, "Storage Box DOK-3"),
    ("2026-05-13", "A", "L35_P3", "P3", 65, "P3 close"),
    ("2026-05-13", "F", "L35_P3", "P3", 45, "Wed F compressed — P3 close"),
    ("2026-05-14", "F", None,     "ASSESS", 65, "Topic 3 Assessment (F)"),
    ("2026-05-14", "A", None,     "ASSESS", 55, "Topic 3 Assessment (A)"),
    ("2026-05-15", "F", "L41_P1", "P1", 65, "F starts 4-1"),

    # ── Week of 5/18 — A starts L41 + L41 P1/P2 ────────────────────────────
    ("2026-05-18", "A", "L41_P1", "P1", 65, "A starts 4-1"),
    ("2026-05-19", "F", "L41_P1", "P1", 65, "4-1 P1 (F)"),
    ("2026-05-19", "A", "L41_P1", "P1", 55, "4-1 P1 (A)"),
    ("2026-05-20", "A", "L41_P1", "P1", 65, "4-1 P1 continues"),
    ("2026-05-20", "F", "L41_P2", "P2", 45, "Wed F compressed — 4-1 P2"),
    ("2026-05-21", "F", "L41_P2", "P2", 65, "4-1 P2"),
    ("2026-05-21", "A", "L41_P2", "P2", 55, "4-1 P2"),
    ("2026-05-22", "F", "L41_P3", "P3", 65, "4-1 P3 (LEHS-critical)"),

    # ── Week of 5/25 — Memorial Day + L41 finish + start single-period quicks
    ("2026-05-25", "A", None,     "BUFFER", 0,  "Memorial Day (holiday)"),
    ("2026-05-26", "F", "L41_P3", "P3", 65, "4-1 P3 finish"),
    ("2026-05-26", "A", "L41_P3", "P3", 55, "4-1 P3"),
    ("2026-05-27", "A", "L41_P3", "P3", 65, "4-1 P3 finish (A)"),
    ("2026-05-27", "F", "L43_P1", "P1", 45, "Wed F — 4-3 single-period quick"),
    ("2026-05-28", "F", "L43_P1", "P1", 65, "4-3 (F)"),
    ("2026-05-28", "A", "L43_P1", "P1", 55, "4-3 (A)"),
    ("2026-05-29", "F", "L44_P1", "P1", 65, "4-4 single-period quick (F)"),

    # ── Week of 6/1 — Finish Unit 4 + Topic 4 Assess + start Unit 5 ─────────
    ("2026-06-01", "A", "L44_P1", "P1", 65, "4-4 (A)"),
    ("2026-06-02", "F", "L45_P1", "P1", 65, "4-5 single-period quick (F)"),
    ("2026-06-02", "A", "L45_P1", "P1", 55, "4-5 (A)"),
    ("2026-06-03", "A", None,     "ASSESS", 65, "Topic 4 LEHS Assessment (A)"),
    ("2026-06-03", "F", None,     "ASSESS", 45, "Topic 4 LEHS Assessment (F, Wed compressed)"),
    ("2026-06-04", "F", "L51_P1", "P1", 65, "5-1 single-period quick (F)"),
    ("2026-06-04", "A", "L51_P1", "P1", 55, "5-1 (A)"),
    ("2026-06-05", "F", "L54_P1", "P1", 65, "5-4 single-period quick (F)"),

    # ── Week of 6/8 — Unit 5 finish + start Unit 6 ──────────────────────────
    ("2026-06-08", "A", "L54_P1", "P1", 65, "5-4 (A)"),
    ("2026-06-09", "F", "L55_P1", "P1", 65, "5-5 single-period quick (F)"),
    ("2026-06-09", "A", "L55_P1", "P1", 55, "5-5 (A)"),
    ("2026-06-10", "A", "L63_P1", "P1", 65, "6-3 single-period quick (A)"),
    ("2026-06-10", "F", "L63_P1", "P1", 45, "Wed F — 6-3"),
    ("2026-06-11", "F", "L64_P1", "P1", 65, "6-4 single-period quick (F)"),
    ("2026-06-11", "A", "L64_P1", "P1", 55, "6-4 (A)"),
    ("2026-06-12", "F", None,     "REVIEW", 65, "Final review (6-5 dropped per realistic cuts)"),

    # ── Week of 6/15 — Finals / end of year ─────────────────────────────────
    ("2026-06-15", "A", None, "REVIEW", 65, "Finals week — review"),
    ("2026-06-16", "F", None, "REVIEW", 65, "Finals week — review"),
    ("2026-06-16", "A", None, "REVIEW", 55, "Finals week — review"),
    ("2026-06-17", "A", None, "REVIEW", 65, "Finals week"),
    ("2026-06-17", "F", None, "REVIEW", 45, "Finals week (Wed F compressed)"),
    ("2026-06-18", "A", None, "REVIEW", 55, "Finals week"),
    ("2026-06-18", "F", None, "REVIEW", 65, "Finals week"),
    ("2026-06-19", "F", None, "BUFFER", 65, "Last day"),
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
