# Railway pdflatex service

Receives a lesson ID, reads tex source from Supabase, compiles with pdflatex, and uploads the resulting PDFs back to the `lesson-pdfs` Storage bucket.

## Environment variables

| Variable | Required | Notes |
|---|---|---|
| `SUPABASE_URL` | yes | Project URL from Settings > API |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | Service role key (secret). Has write access; keep out of client code. |
| `REBUILD_PASSCODE` | yes | Shared secret sent as `X-Passcode` header. **Change from default `changeme123` before deploying.** |
| `PORT` | no | Railway sets this automatically. Default 8080. |

Copy `.env.example` to `.env` for local development.

## Deploy to Railway

The Dockerfile must be built from the repo root (it copies `build_lesson_from_yaml.py` and `tex/*.sty` files from sibling directories). Railway's context is the directory you link, so link the **repo root**, not `railway/`.

```bash
# From repo root — Railway CLI picks up railway/railway.toml
railway up
```

Or connect the GitHub repo in the Railway dashboard and set the root directory to `/` with `railway/Dockerfile` as the Dockerfile path.

Set the three required environment variables in Railway > Variables before the first deploy.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"ok": true, "tex": "<pdflatex version>"}` |
| `POST` | `/build/{lesson_id}` | Compile and upload PDFs. Auth: `X-Passcode` header. |
| `PUT` | `/tex/{lesson_id}/{edition}` | Write tex source to Supabase. Body: raw text. Auth: `X-Passcode` header. `edition` = `student` or `teacher`. |

`lesson_id` must match `L##_P#` (e.g. `L41_P2`).

## Storage CDN cache invalidation

The `lesson-pdfs` bucket is public-read. After a successful build, the PDF URL is stable (`{SUPABASE_URL}/storage/v1/object/public/lesson-pdfs/{lesson_id}_{edition}.pdf`). Supabase Storage does not cache at the CDN layer by default — a fresh GET always retrieves the latest object. If you add a CDN in front, purge by path: `/{lesson_id}_student.pdf` and `/{lesson_id}_teacher.pdf`.

## Local development

Run from the **repo root** so `server.py` can find `build_lesson_from_yaml.py` and `tex/*.sty` as siblings:

```bash
# from repo root
cp railway/.env.example .env   # populate with real values
pip install -r railway/requirements.txt
uvicorn railway.server:app --reload --port 8080
```

Or copy `server.py` into the repo root temporarily and run there. The key requirement is that `build_lesson_from_yaml.py`, `tex/preamble.sty`, and `tex/beamer_preamble.sty` exist in `Path(__file__).parent` at runtime — which is `/app` in the container.

Smoke-test after starting:

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/build/L41_P2 \
     -H "X-Passcode: changeme123"
```
