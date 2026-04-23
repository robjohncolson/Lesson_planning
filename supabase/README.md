# supabase/

Teacher Console web-app backend: schema + one-time seed.

Project: `bzqbhtrurzzavhqbgqrs.supabase.co` (shared with curriculum_render).
All tables live in a dedicated `lesson_planning` schema to avoid collision
with the existing curriculum_render tables (`answers`, `identity_claims`,
`teacher_notifications`, `users`).

## Prerequisites

- `SUPABASE_SERVICE_ROLE_KEY` from Supabase dashboard → Project Settings → API.
  This bypasses RLS; keep it off your machine in plain files. Put it in
  `.env.local` (gitignored) or export it each shell session.
- Repo's existing `requests` + `pyyaml` Python packages.

## First-run workflow

1. **Apply the schema**

   Open the SQL editor in the Supabase dashboard
   (https://supabase.com/dashboard/project/bzqbhtrurzzavhqbgqrs/sql) and paste
   the entire contents of `schema.sql`. Run it once.

   It drops and recreates the `lesson_planning` schema — destructive only
   within that schema, no effect on curriculum_render tables.

2. **Seed the data**

   ```powershell
   $env:SUPABASE_URL = "https://bzqbhtrurzzavhqbgqrs.supabase.co"
   $env:SUPABASE_SERVICE_ROLE_KEY = "<paste service role key>"
   python supabase/seed.py --dry-run    # preview
   python supabase/seed.py              # apply
   ```

   Expected output:
   ```
   Loading local data...
     registry.jsonl:         1057 rows
     assessment_shells.jsonl:  34 rows
     → items: 1091  edges: 210  lessons: 18
   Upserting items...
     lesson_planning.items: 200/1091
     ...
   Done.
   ```

3. **Verify from the Supabase SQL editor**

   ```sql
   select count(*) from lesson_planning.items;       -- 1091
   select count(*) from lesson_planning.edges;       -- ~210
   select count(*) from lesson_planning.lessons;     -- 18
   select count(*) filter (where is_shell) from lesson_planning.items;  -- 34
   ```

## Schema at a glance

| Table | Row count (seed) | Purpose |
|---|---|---|
| `items` | 1091 | Registry + assessment shells, flat columns + JSONB for arrays |
| `edges` | ~210 | prereq / rehearses / echoes relationships |
| `lessons` | 18 | Per-period shell + the lesson's YAML spec text |
| `audit` | grows on writes | Before/after snapshots for every items/edges mutation |

## RLS (row-level security)

- **Read**: `anon` and `authenticated` can SELECT everything.
- **Write**: `anon` has no write policies. All writes must go through a
  server-side endpoint (Vercel API route or Railway service) that holds
  the `service_role` key and gates on a shared passcode — see the web app
  README once it exists.

## Re-seeding later

Safe — `seed.py` uses PostgREST upsert (`resolution=merge-duplicates`).
Existing rows are replaced by the local-file version. Writes made through
the web UI that haven't been exported back will be **lost**. Don't re-seed
once the web app is live without exporting first.

## Exporting Supabase → JSONL (not yet written)

Future script `supabase/export.py` will:
- Pull every row from `lesson_planning.items` and `edges`
- Reconstruct `questionbank/registry.jsonl` + `assessment_shells.jsonl`
- Optionally `git commit` the result so the repo stays authoritative for
  tex/build code while the DB owns teacher-authored metadata.

Design this before the web app starts writing to Supabase, not after.
