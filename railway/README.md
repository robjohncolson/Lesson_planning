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
| `POST` | `/upload/topic-pdf/{topic}/{edition}` | Upload a topic-level PDF (e.g. `4-3`, edition `SE` or `TE`). Multipart field `file`. |
| `POST` | `/upload/docx/{lesson_id}/{kind}` | Upload a .docx or .pptx artifact. `kind` = `student`, `teacher`, or `slides`. Multipart field `file`. |
| `POST` | `/upload/screenshot/{item_id}` | Upload a PNG or JPG screenshot for a question-bank item (e.g. `4-1-savvas-q26`). Multipart field `file`. |

`lesson_id` must match `L##_P#` (e.g. `L41_P2`). All upload endpoints require `X-Passcode` AND `X-User-Name` headers.

### Upload response shape

```json
{"ok": true, "url": "<public_url>", "size": <bytes>, "uploaded_by": "<X-User-Name>"}
```

### Storage buckets

| Bucket | Public | Contents |
|---|---|---|
| `lesson-pdfs` | yes | Compiled lesson PDFs (managed by `/build`) |
| `topic-pdfs` | yes | Manually uploaded topic-level PDFs (`a2_{topic}_{edition}.pdf`) |
| `lesson-docx` | yes | Docx/pptx artifacts (`{lesson_id}_{kind}.{docx,pptx}`) |
| `item-screenshots` | yes | Question-bank screenshots (`{item_id}.{png,jpg}`) |

The three new buckets are created automatically at server startup if they don't exist (idempotent — 409 is treated as success).

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
