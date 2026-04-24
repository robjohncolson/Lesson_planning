-- Migration 006: Do Now .tex editing parity
--
-- Adds a tex_do_now column to lessons so the web app's Do Now .tex editor
-- can Save + Rebuild through the same Supabase column → Railway PUT →
-- pdflatex → Supabase Storage pipeline used for student/teacher/slides.
--
-- No RLS change (inherits from lessons). Idempotent.
--
-- After running this migration, reload the PostgREST schema cache
-- (Supabase dashboard → Settings → API → Reload schema) or wait ~60s so
-- `tex_do_now` becomes selectable via the REST API.

ALTER TABLE lesson_planning.lessons
  ADD COLUMN IF NOT EXISTS tex_do_now TEXT;
