-- Migration 005: per-period lesson phase mapping
--
-- Maps items (and unmatched labels) to phases (do_now, launch, explore,
-- share_summary, exit, reinforcement) within a lesson-period. Drives the
-- phase-grouped item list in the web app so teachers can quickly find e.g.
-- "the Do Now for L35_P2" without scanning all ~90 items for lesson 3-5.
--
-- Why a separate table (not items.role): items are reused across periods.
-- `3-5-savvas-q11` can be explore-practice in one period and Do Now in
-- another. role is a global property; phase membership is per-period.
--
-- Idempotent: safe to re-run. Seed script deletes all rows for a lesson_id
-- before inserting to avoid stale position leaks.

CREATE TABLE IF NOT EXISTS lesson_planning.lesson_phases (
  id          SERIAL PRIMARY KEY,
  lesson_id   TEXT NOT NULL REFERENCES lesson_planning.lessons(id) ON DELETE CASCADE,
  phase       TEXT NOT NULL CHECK (phase IN (
                 'do_now','launch','explore','share_summary','exit','reinforcement'
               )),
  position    INT NOT NULL,
  item_id     TEXT REFERENCES lesson_planning.items(id) ON DELETE SET NULL,
  label       TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (lesson_id, phase, position)
);

CREATE INDEX IF NOT EXISTS lesson_phases_lesson_idx ON lesson_planning.lesson_phases (lesson_id);
CREATE INDEX IF NOT EXISTS lesson_phases_item_idx   ON lesson_planning.lesson_phases (item_id);

-- RLS: public read, writes via service_role only (same pattern as schedule/items/lessons)
ALTER TABLE lesson_planning.lesson_phases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS lesson_phases_public_select ON lesson_planning.lesson_phases;
CREATE POLICY lesson_phases_public_select
  ON lesson_planning.lesson_phases
  FOR SELECT
  TO anon, authenticated
  USING (true);

DROP POLICY IF EXISTS lesson_phases_service_write ON lesson_planning.lesson_phases;
CREATE POLICY lesson_phases_service_write
  ON lesson_planning.lesson_phases
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

GRANT SELECT ON lesson_planning.lesson_phases TO anon, authenticated;
GRANT ALL    ON lesson_planning.lesson_phases TO service_role;
GRANT USAGE, SELECT ON SEQUENCE lesson_planning.lesson_phases_id_seq TO service_role;
