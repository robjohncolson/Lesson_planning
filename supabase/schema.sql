-- Teacher Console · Supabase schema
-- Project: bzqbhtrurzzavhqbgqrs  (shares project with curriculum_render)
--
-- All tables live in the `lesson_planning` schema so they don't collide with
-- existing curriculum_render tables (answers, identity_claims, teacher_notifications, users).
--
-- Run order:
--   1. psql / Supabase SQL editor: this file
--   2. python supabase/seed.py    (one-time populate from local JSONL + YAML)
--
-- Idempotent: re-running this file drops and recreates the schema. Use with care.

DROP SCHEMA IF EXISTS lesson_planning CASCADE;
CREATE SCHEMA lesson_planning;
GRANT USAGE ON SCHEMA lesson_planning TO anon, authenticated, service_role;

-- ── items ──────────────────────────────────────────────────────────────────
-- The combined registry (regular items) + assessment shells. `is_shell` flags
-- shells so queries can filter them in/out.
CREATE TABLE lesson_planning.items (
  id                    TEXT PRIMARY KEY,
  lesson                TEXT,
  source                TEXT,
  prompt                TEXT,
  dok                   INT,
  dok_rationale         TEXT,
  role                  TEXT,
  correct               TEXT,
  teacher_answer        TEXT,
  notes                 TEXT,
  has_visual            BOOLEAN DEFAULT FALSE,
  image                 TEXT,
  visual_type           TEXT,
  visual_needs_cleanup  BOOLEAN,
  visual_clean_asset    TEXT,
  page                  INT,

  topics                JSONB NOT NULL DEFAULT '[]'::jsonb,
  tags                  JSONB NOT NULL DEFAULT '[]'::jsonb,
  skill_tokens          JSONB NOT NULL DEFAULT '[]'::jsonb,
  standards             JSONB NOT NULL DEFAULT '[]'::jsonb,
  answers               JSONB NOT NULL DEFAULT '[]'::jsonb,
  used_in               JSONB NOT NULL DEFAULT '[]'::jsonb,

  is_shell              BOOLEAN DEFAULT FALSE,
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX items_lesson_idx    ON lesson_planning.items (lesson);
CREATE INDEX items_role_idx      ON lesson_planning.items (role);
CREATE INDEX items_is_shell_idx  ON lesson_planning.items (is_shell);
CREATE INDEX items_skills_idx    ON lesson_planning.items USING GIN (skill_tokens);
CREATE INDEX items_standards_idx ON lesson_planning.items USING GIN (standards);
CREATE INDEX items_topics_idx    ON lesson_planning.items USING GIN (topics);
CREATE INDEX items_tags_idx      ON lesson_planning.items USING GIN (tags);

-- ── edges ──────────────────────────────────────────────────────────────────
-- Typed curriculum relationships. Seed populates these from registry fields:
-- prereq_ids / rehearses / echoes. The tagging UI adds new ones.
CREATE TABLE lesson_planning.edges (
  from_id     TEXT NOT NULL REFERENCES lesson_planning.items(id) ON DELETE CASCADE,
  to_id       TEXT NOT NULL REFERENCES lesson_planning.items(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL CHECK (kind IN ('prereq', 'rehearses', 'echoes')),
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  created_by  TEXT,
  PRIMARY KEY (from_id, to_id, kind)
);
CREATE INDEX edges_from_idx ON lesson_planning.edges (from_id);
CREATE INDEX edges_to_idx   ON lesson_planning.edges (to_id);
CREATE INDEX edges_kind_idx ON lesson_planning.edges (kind);

-- ── lessons ────────────────────────────────────────────────────────────────
-- Lesson YAML specs. yaml_text is the full YAML file contents; the web editor
-- writes back to this field, triggering the Railway pdflatex service.
CREATE TABLE lesson_planning.lessons (
  id              TEXT PRIMARY KEY,       -- e.g. 'L41_P2'
  cadence         TEXT,
  title           TEXT,
  yaml_text       TEXT,
  tex_student     TEXT,                    -- source of truth for student tex
  tex_teacher     TEXT,                    -- source of truth for teacher tex
  tex_slides      TEXT,                    -- source of truth for slides tex
  has_tex_student BOOLEAN DEFAULT FALSE,
  has_tex_teacher BOOLEAN DEFAULT FALSE,
  has_pdf_student BOOLEAN DEFAULT FALSE,
  has_pdf_teacher BOOLEAN DEFAULT FALSE,
  has_slides_pdf  BOOLEAN DEFAULT FALSE,
  last_build_at   TIMESTAMPTZ,
  last_build_ok   BOOLEAN,
  last_build_log  TEXT,
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX lessons_updated_idx ON lesson_planning.lessons (updated_at DESC);

-- ── audit ──────────────────────────────────────────────────────────────────
-- Lightweight audit log. Triggers below fire on item/edge writes.
CREATE TABLE lesson_planning.audit (
  id          BIGSERIAL PRIMARY KEY,
  table_name  TEXT NOT NULL,
  row_id      TEXT,
  action      TEXT NOT NULL CHECK (action IN ('insert','update','delete')),
  before      JSONB,
  after       JSONB,
  changed_at  TIMESTAMPTZ DEFAULT NOW(),
  changed_by  TEXT
);
CREATE INDEX audit_table_row_idx ON lesson_planning.audit (table_name, row_id);
CREATE INDEX audit_changed_idx   ON lesson_planning.audit (changed_at DESC);

-- Trigger: keep items.updated_at current
CREATE OR REPLACE FUNCTION lesson_planning.touch_updated_at() RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER items_touch    BEFORE UPDATE ON lesson_planning.items
  FOR EACH ROW EXECUTE FUNCTION lesson_planning.touch_updated_at();
CREATE TRIGGER lessons_touch  BEFORE UPDATE ON lesson_planning.lessons
  FOR EACH ROW EXECUTE FUNCTION lesson_planning.touch_updated_at();

-- Trigger: audit writes to items + edges
CREATE OR REPLACE FUNCTION lesson_planning.log_audit() RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO lesson_planning.audit (table_name, row_id, action, after, changed_by)
      VALUES (TG_TABLE_NAME, NEW.id::TEXT, 'insert', to_jsonb(NEW), current_setting('request.header.x-user-name', true));
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO lesson_planning.audit (table_name, row_id, action, before, after, changed_by)
      VALUES (TG_TABLE_NAME, NEW.id::TEXT, 'update', to_jsonb(OLD), to_jsonb(NEW), current_setting('request.header.x-user-name', true));
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO lesson_planning.audit (table_name, row_id, action, before, changed_by)
      VALUES (TG_TABLE_NAME, OLD.id::TEXT, 'delete', to_jsonb(OLD), current_setting('request.header.x-user-name', true));
    RETURN OLD;
  END IF;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER items_audit AFTER INSERT OR UPDATE OR DELETE ON lesson_planning.items
  FOR EACH ROW EXECUTE FUNCTION lesson_planning.log_audit();
-- No audit trigger on edges: they have a composite PK (from_id, to_id, kind)
-- which doesn't fit the generic `NEW.id` shape, and edges are trivially
-- reconstructable from items' prereq_ids/rehearses/echoes fields anyway.

-- ── RLS: public read, writes via service_role only ─────────────────────────
-- MVP auth: no per-user accounts. The Vercel frontend uses the anon key for
-- reads; writes go through a small API (Vercel route or Railway endpoint)
-- that validates a shared passcode and uses the service_role key.
ALTER TABLE lesson_planning.items   ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_planning.edges   ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_planning.lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_planning.audit   ENABLE ROW LEVEL SECURITY;

CREATE POLICY items_read    ON lesson_planning.items   FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY edges_read    ON lesson_planning.edges   FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY lessons_read  ON lesson_planning.lessons FOR SELECT TO anon, authenticated USING (true);
-- audit visible to anyone for transparency; redact if this is undesirable later
CREATE POLICY audit_read    ON lesson_planning.audit   FOR SELECT TO anon, authenticated USING (true);

-- service_role bypasses RLS by default — no write policies for anon.

GRANT SELECT ON ALL TABLES IN SCHEMA lesson_planning TO anon, authenticated;
GRANT ALL    ON ALL TABLES IN SCHEMA lesson_planning TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA lesson_planning TO anon, authenticated, service_role;

COMMENT ON SCHEMA lesson_planning IS 'Teacher Console: registry items, edges, lessons. See Lesson_planning repo.';
