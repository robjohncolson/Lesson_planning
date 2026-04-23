-- Migration 002: add tex_slides + teach audit trigger to tolerate missing header
--
-- Phase 1 of the collaborative surface:
--   - Teachers can now edit slides .tex in the web app (parallel to student/teacher).
--   - Each save carries X-User-Name so the audit trigger records WHO edited.
--
-- Safe to re-run (idempotent).

ALTER TABLE lesson_planning.lessons
  ADD COLUMN IF NOT EXISTS tex_slides TEXT;

-- The audit trigger currently reads `request.header.x-user-name` via
-- current_setting('...', true). PostgREST exposes request headers only as
-- `request.headers` (a JSON object); the per-header `request.header.*` form
-- is available when PostgREST is configured with --role jwt, but Supabase
-- exposes all request headers. Handle both shapes gracefully.
CREATE OR REPLACE FUNCTION lesson_planning.log_audit() RETURNS TRIGGER AS $$
DECLARE
  actor TEXT;
BEGIN
  -- Prefer the explicit header setting; fall back to the JSON bag; null-safe.
  actor := NULLIF(current_setting('request.header.x-user-name', true), '');
  IF actor IS NULL THEN
    actor := NULLIF(current_setting('request.headers', true)::jsonb->>'x-user-name', '');
  END IF;

  IF TG_OP = 'INSERT' THEN
    INSERT INTO lesson_planning.audit (table_name, row_id, action, after, changed_by)
      VALUES (TG_TABLE_NAME, NEW.id::TEXT, 'insert', to_jsonb(NEW), actor);
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO lesson_planning.audit (table_name, row_id, action, before, after, changed_by)
      VALUES (TG_TABLE_NAME, NEW.id::TEXT, 'update', to_jsonb(OLD), to_jsonb(NEW), actor);
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO lesson_planning.audit (table_name, row_id, action, before, changed_by)
      VALUES (TG_TABLE_NAME, OLD.id::TEXT, 'delete', to_jsonb(OLD), actor);
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;
