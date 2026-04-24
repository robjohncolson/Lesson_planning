-- Migration 004: class schedule table
--
-- Maps concrete class-meeting dates to lesson days (P1/P2/P3) per period
-- (A or F). Drives the Schedule page in the web app:
--   - grid of the next ~7 weeks through end of school (2026-06-20)
--   - which packet must be ready by which date, for which period
--   - links to pacer + lesson detail
--
-- Idempotent: safe to re-run.

CREATE TABLE IF NOT EXISTS lesson_planning.schedule (
  id             SERIAL PRIMARY KEY,
  class_date     DATE NOT NULL,
  period         TEXT NOT NULL CHECK (period IN ('A','F')),
  lesson_id      TEXT REFERENCES lesson_planning.lessons(id) ON DELETE SET NULL,
  day_of_lesson  TEXT CHECK (day_of_lesson IN ('P1','P2','P3','P4','ASSESS','REVIEW','BUFFER')),
  minutes        INT,
  notes          TEXT,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  updated_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (class_date, period)
);

CREATE INDEX IF NOT EXISTS schedule_date_idx    ON lesson_planning.schedule (class_date);
CREATE INDEX IF NOT EXISTS schedule_lesson_idx  ON lesson_planning.schedule (lesson_id);

-- RLS: public read, writes via service_role only (same pattern as items/lessons)
ALTER TABLE lesson_planning.schedule ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS schedule_public_select ON lesson_planning.schedule;
CREATE POLICY schedule_public_select
  ON lesson_planning.schedule
  FOR SELECT
  TO anon, authenticated
  USING (true);

DROP POLICY IF EXISTS schedule_service_write ON lesson_planning.schedule;
CREATE POLICY schedule_service_write
  ON lesson_planning.schedule
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

GRANT SELECT ON lesson_planning.schedule TO anon, authenticated;
GRANT ALL    ON lesson_planning.schedule TO service_role;
GRANT USAGE, SELECT ON SEQUENCE lesson_planning.schedule_id_seq TO service_role;
