# Teacher Console — web frontend

Read-only web mirror of the local Flask console, deployed on Vercel, reading
from Supabase (`bzqbhtrurzzavhqbgqrs`, `lesson_planning` schema).

**Phase A step 2**: lesson list, YAML viewer, item browser, DAG view, all read-only.
Writes, regenerate, and tagging land in Phase A step 3 and Phase B.

## Local dev

Any static file server works. No build step:

```powershell
# 1. Create config.js from the template — this file is gitignored.
cp web\config.example.js web\config.js
# edit web\config.js and paste the anon key from
#   Supabase Dashboard > Project Settings > API > anon / public

# 2. Serve the web/ dir over http (not file://, because of ESM CORS)
python -m http.server 5175 --directory web
# open http://127.0.0.1:5175
```

## Vercel deploy (CLI)

Vercel serves `web/` as a static site. There's no build step — the client
imports `/config.js` directly as a plain ES module, so **`config.js` must
be present in the deployed bundle**.

Two options:

**Option 1 — Commit config.js (simpler, recommended for Phase A).**
The Supabase anon key is designed to be publicly embedded in clients;
row-level security protects data access. Commit `web/config.js` with real
values, add an exception to `web/.gitignore`:

```gitignore
# web/.gitignore
# (remove the config.js line to allow commit)
```

**Option 2 — Keep config.js gitignored, inject via Vercel build.**
Set env vars in the Vercel dashboard and add a `build` command in
`vercel.json` that writes `config.js` from the environment at deploy time.
Out of scope for Phase A; do this if/when the project goes private.

### CLI deploy

```powershell
# First time: install CLI and log in
npm install -g vercel
vercel login

# From repo root
cd web
vercel           # answer "Y" to link, accept defaults
# ...later...
vercel --prod
```

## Data dependencies

Relies on the `lesson_planning` schema in Supabase — populate it first:

```bash
# see supabase/README.md for full details
python supabase/seed.py
```

PDF URLs point at GitHub raw in this repo (`tex/L*_{student,teacher,slides}.pdf`).
Until the Railway pdflatex service is wired up, clicking "Regenerate" in a
future phase won't do anything; the buttons just link out.

## File layout — read `SPEC.md` before editing

Everything else is in `SPEC.md` — DOM IDs, API surface, routing, styling
conventions. JS modules expect those contracts to hold.
