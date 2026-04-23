-- Migration 003: enable Postgres-change Realtime on lesson_planning.lessons
--
-- Phase 2 of the collaborative surface:
--   When teacher A saves tex, teacher B (with the same lesson open) receives
--   an UPDATE event over Supabase Realtime and the web app banners:
--     "Brian just saved teacher.tex — [Take their version] [Keep mine]"
--
-- Safe to re-run (idempotent).

-- The supabase_realtime publication is what the Realtime server tails.
-- We only need the lessons table — items/edges are not live-edited.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_publication_tables
    WHERE pubname = 'supabase_realtime'
      AND schemaname = 'lesson_planning'
      AND tablename = 'lessons'
  ) THEN
    ALTER PUBLICATION supabase_realtime
      ADD TABLE lesson_planning.lessons;
  END IF;
END $$;

-- REPLICA IDENTITY FULL so UPDATE events include the OLD row too; needed for
-- the web client to tell which column changed when many edits land at once.
ALTER TABLE lesson_planning.lessons REPLICA IDENTITY FULL;
