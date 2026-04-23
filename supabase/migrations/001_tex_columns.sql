-- Migration 001: add tex source columns to lesson_planning.lessons
--
-- Makes the lessons table the source of truth for tex source, enabling
-- web editing + Railway-triggered rebuild. Safe to re-run (idempotent).
--
-- Apply in Supabase SQL editor:
--   https://supabase.com/dashboard/project/bzqbhtrurzzavhqbgqrs/sql

-- tex columns themselves + the has_* flags schema.sql writes on seed.
-- Both needed on an already-seeded DB; schema.sql already defines has_*.
ALTER TABLE lesson_planning.lessons
  ADD COLUMN IF NOT EXISTS tex_student     TEXT,
  ADD COLUMN IF NOT EXISTS tex_teacher     TEXT,
  ADD COLUMN IF NOT EXISTS has_tex_student BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS has_tex_teacher BOOLEAN DEFAULT FALSE;

-- Storage bucket for rendered PDFs. Public read so the frontend can link
-- directly without a signed URL — PDFs aren't sensitive.
INSERT INTO storage.buckets (id, name, public)
VALUES ('lesson-pdfs', 'lesson-pdfs', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- Anyone can read from the lesson-pdfs bucket.
DROP POLICY IF EXISTS "lesson-pdfs public read" ON storage.objects;
CREATE POLICY "lesson-pdfs public read"
  ON storage.objects FOR SELECT
  TO anon, authenticated
  USING (bucket_id = 'lesson-pdfs');

-- Only service_role (Railway uploader) writes to the bucket.
-- service_role bypasses RLS by default; no INSERT/UPDATE policy needed for anon.
