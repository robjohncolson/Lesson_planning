"""Railway pdflatex build service for the Teacher Console.

Endpoints:
  GET  /health                                  — smoke test
  POST /build/{lesson_id}                       — read tex from Supabase, compile, upload PDFs
  PUT  /tex/{lesson_id}/{edition}               — write tex source back to Supabase
  POST /upload/topic-pdf/{topic}/{edition}      — Savvas chapter PDF (SE/TE) -> topic-pdfs bucket
  POST /upload/docx/{lesson_id}/{kind}          — externally-converted DOCX/PPTX -> lesson-docx bucket
  POST /upload/screenshot/{item_id}             — registry-item textbook source PNG/JPG -> item-screenshots bucket

Auth: X-Passcode header must match REBUILD_PASSCODE env var.

Uses `requests` (HTTP/1.1) directly against Supabase REST + Storage APIs,
not supabase-py. supabase-py's httpx-based HTTP/2 client intermittently
trips StreamReset errors against Supabase's Cloudflare edge.

Deployed via Railway GitHub integration: pushes to main auto-build + deploy
(no manual `railway up` needed). Service root dir = railway/.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import FastAPI, Header, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
REBUILD_PASSCODE = os.environ["REBUILD_PASSCODE"]

LESSON_ID_RE = re.compile(r"^L\d{2}_P\d(?:_[a-z][a-z0-9_]*)?$")  # e.g. L41_P2 or L35_P3_obs
EDITIONS = {"student", "teacher", "slides", "do_now"}

HERE = Path(__file__).parent
PREAMBLE_STY = HERE / "preamble.sty"
BEAMER_STY = HERE / "beamer_preamble.sty"
YAML_BUILDER = HERE / "build_lesson_from_yaml.py"

SCHEMA = "lesson_planning"
BUCKET = "lesson-pdfs"

_REST_HEADERS_BASE = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Accept-Profile": SCHEMA,
    "Content-Profile": SCHEMA,
}


def _rest_headers(user_name: str | None = None) -> dict:
    h = dict(_REST_HEADERS_BASE)
    if user_name:
        h["x-user-name"] = user_name
    return h

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["Content-Type", "X-Passcode", "X-User-Name", "If-Match-Sha"],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
)


# ---------------------------------------------------------------------------
# Supabase REST helpers (plain requests — HTTP/1.1)
# ---------------------------------------------------------------------------

def _rest_get_lesson(lesson_id: str, user_name: str | None = None) -> dict | None:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/lessons",
        headers=_rest_headers(user_name),
        params={"id": f"eq.{lesson_id}",
                "select": "tex_student,tex_teacher,tex_slides,tex_do_now,yaml_text"},
        timeout=15,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


def _rest_update_lesson(lesson_id: str, patch: dict, user_name: str | None = None) -> None:
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/lessons",
        headers={**_rest_headers(user_name), "Content-Type": "application/json",
                 "Prefer": "return=minimal"},
        params={"id": f"eq.{lesson_id}"},
        json=patch,
        timeout=15,
    )
    r.raise_for_status()


def _rest_last_audit_changed_by(lesson_id: str) -> str | None:
    """Return the most recent changed_by for a lessons row, or None on any error."""
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/audit",
            headers=_rest_headers(),
            params={
                "table_name": "eq.lessons",
                "row_id": f"eq.{lesson_id}",
                "select": "changed_by",
                "order": "changed_at.desc",
                "limit": "1",
            },
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return None
        return rows[0].get("changed_by")
    except Exception:
        return None


def _storage_upload(object_path: str, body: bytes, content_type: str) -> None:
    """Upload (or replace) an object in Supabase Storage. x-upsert: true so a
    previous PDF is overwritten cleanly."""
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{object_path}",
        headers={
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY,
            "Content-Type": content_type,
            "x-upsert": "true",
        },
        data=body,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"storage upload {object_path}: {r.status_code} {r.text[:200]}")


def _storage_public_url(object_path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{object_path}"


# ---------------------------------------------------------------------------
# Validation + auth helpers
# ---------------------------------------------------------------------------

def _check_passcode(x_passcode: str | None) -> None:
    if x_passcode != REBUILD_PASSCODE:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Passcode")


def _validate_lesson_id(lesson_id: str) -> None:
    if not LESSON_ID_RE.match(lesson_id):
        raise HTTPException(status_code=400, detail="lesson_id must match L##_P# (e.g. L41_P2)")


def _validate_edition(edition: str) -> None:
    if edition not in EDITIONS:
        raise HTTPException(status_code=400, detail="edition must be 'student', 'teacher', 'slides', or 'do_now'")


# ---------------------------------------------------------------------------
# pdflatex runner
# ---------------------------------------------------------------------------

def _run_pdflatex(tex_name: str, work_dir: Path) -> tuple[bool, str]:
    """Run pdflatex twice on tex_name inside work_dir. Returns (ok, log_tail).

    TimeoutExpired is caught and treated as a build failure with a log tail —
    an uncaught exception 500s the request and skips the last_build_log write.
    """
    for _ in range(2):
        try:
            r = subprocess.run(
                ["pdflatex", "-halt-on-error", "-interaction=nonstopmode", tex_name],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            captured = (exc.stdout or "") + (exc.stderr or "")
            return False, (captured[-4096:] if captured else f"{tex_name}: pdflatex timed out after 60s")
        if r.returncode != 0:
            combined = r.stdout + r.stderr
            return False, (combined[-4096:] if len(combined) > 4096 else combined)
    return True, ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _write_build_status(
    lesson_id: str,
    *,
    ok: bool,
    log_tail: str,
    has_pdf_student: bool = False,
    has_pdf_teacher: bool = False,
    has_slides: bool = False,
    user_name: str | None = None,
) -> None:
    payload: dict = {
        "last_build_at": datetime.now(timezone.utc).isoformat(),
        "last_build_ok": ok,
        "last_build_log": log_tail if not ok else "",
    }
    if has_pdf_student or has_pdf_teacher:
        payload["has_pdf_student"] = has_pdf_student
        payload["has_pdf_teacher"] = has_pdf_teacher
    if has_slides:
        payload["has_slides_pdf"] = True
    try:
        _rest_update_lesson(lesson_id, payload, user_name)
    except Exception as exc:
        log.error("Failed to write build status for %s: %s", lesson_id, exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    r = subprocess.run(
        ["pdflatex", "--version"],
        capture_output=True,
        text=True,
    )
    first_line = r.stdout.splitlines()[0] if r.stdout else "pdflatex not found"
    return {"ok": True, "tex": first_line}


@app.post("/build/{lesson_id}")
def build(
    lesson_id: str,
    x_passcode: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
) -> dict:
    _validate_lesson_id(lesson_id)
    _check_passcode(x_passcode)

    row = _rest_get_lesson(lesson_id, x_user_name)
    if not row:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

    tex_student = row.get("tex_student")
    tex_teacher = row.get("tex_teacher")
    tex_slides = row.get("tex_slides")
    tex_do_now = row.get("tex_do_now")
    yaml_text = row.get("yaml_text")

    if not yaml_text and not tex_student and not tex_teacher and not tex_slides and not tex_do_now:
        raise HTTPException(
            status_code=422,
            detail="Lesson has no yaml_text and no tex sources; nothing to build",
        )

    log_tail = ""
    student_ok = False
    teacher_ok = False
    slides_ok = False
    do_now_ok = False
    pdf_student_url = None
    pdf_teacher_url = None
    pdf_slides_url = None
    pdf_do_now_url = None

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # Shared style files into temp dir so pdflatex finds them
        if PREAMBLE_STY.exists():
            (tmp / "preamble.sty").write_bytes(PREAMBLE_STY.read_bytes())
        if BEAMER_STY.exists():
            (tmp / "beamer_preamble.sty").write_bytes(BEAMER_STY.read_bytes())

        # Source-of-truth policy:
        #   - Stored tex wins when present; web edits persist through rebuilds.
        #   - Only regenerate from YAML when neither tex edition is stored.
        if tex_student or tex_teacher:
            if tex_student:
                (tmp / f"{lesson_id}_student.tex").write_text(tex_student, encoding="utf-8")
            if tex_teacher:
                (tmp / f"{lesson_id}_teacher.tex").write_text(tex_teacher, encoding="utf-8")
        elif yaml_text:
            try:
                import yaml as _yaml
                parsed = _yaml.safe_load(yaml_text) or {}
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f"Invalid YAML: {exc}")
            yaml_lid = (parsed.get("lesson_id") or "").strip()
            if yaml_lid and yaml_lid != lesson_id:
                raise HTTPException(
                    status_code=422,
                    detail=f"YAML lesson_id ({yaml_lid!r}) must match route lesson_id ({lesson_id!r})",
                )

            yaml_path = tmp / f"{lesson_id}.yaml"
            yaml_path.write_text(yaml_text, encoding="utf-8")

            gen_result = subprocess.run(
                [sys.executable, str(YAML_BUILDER), str(yaml_path)],
                cwd=str(HERE),
                capture_output=True,
                text=True,
                timeout=60,
            )
            gen_out = gen_result.stdout + gen_result.stderr
            if gen_result.returncode != 0:
                log.error("build_lesson_from_yaml failed for %s", lesson_id)
                _write_build_status(lesson_id, ok=False, log_tail=gen_out[-4096:],
                                    user_name=x_user_name)
                return {"ok": False, "log_tail": gen_out[-4096:],
                        "pdf_student_url": None, "pdf_teacher_url": None,
                        "pdf_slides_url": None, "pdf_do_now_url": None}

            gen_student = HERE / "tex" / f"{lesson_id}_student.tex"
            gen_teacher = HERE / "tex" / f"{lesson_id}_teacher.tex"
            if gen_student.exists():
                (tmp / f"{lesson_id}_student.tex").write_bytes(gen_student.read_bytes())
            if gen_teacher.exists():
                (tmp / f"{lesson_id}_teacher.tex").write_bytes(gen_teacher.read_bytes())

        # --- student ---
        student_tex = tmp / f"{lesson_id}_student.tex"
        if student_tex.exists():
            student_ok, student_log = _run_pdflatex(student_tex.name, tmp)
            if not student_ok:
                log_tail = student_log
        else:
            student_ok = False
            log_tail = f"{lesson_id}_student.tex not found"

        # --- teacher ---
        teacher_tex = tmp / f"{lesson_id}_teacher.tex"
        if teacher_tex.exists():
            teacher_ok, teacher_log = _run_pdflatex(teacher_tex.name, tmp)
            if not teacher_ok and not log_tail:
                log_tail = teacher_log
        else:
            teacher_ok = False
            if not log_tail:
                log_tail = f"{lesson_id}_teacher.tex not found"

        # --- slides (independent: missing tex_slides is not a failure) ---
        if tex_slides:
            slides_tex_path = tmp / f"{lesson_id}_slides.tex"
            slides_tex_path.write_text(tex_slides, encoding="utf-8")
            slides_ok, slides_log = _run_pdflatex(slides_tex_path.name, tmp)
            if not slides_ok:
                log.warning("slides build failed for %s: %s", lesson_id, slides_log[-500:])
                if not log_tail:
                    log_tail = slides_log

        # --- do_now (independent: missing tex_do_now is not a failure) ---
        if tex_do_now:
            do_now_tex_path = tmp / f"{lesson_id}_do_now.tex"
            do_now_tex_path.write_text(tex_do_now, encoding="utf-8")
            do_now_ok, do_now_log = _run_pdflatex(do_now_tex_path.name, tmp)
            if not do_now_ok:
                log.warning("do_now build failed for %s: %s", lesson_id, do_now_log[-500:])
                if not log_tail:
                    log_tail = do_now_log

        # --- upload ---
        if student_ok:
            pdf_path = tmp / f"{lesson_id}_student.pdf"
            if pdf_path.exists():
                obj = f"{lesson_id}_student.pdf"
                _storage_upload(obj, pdf_path.read_bytes(), "application/pdf")
                pdf_student_url = _storage_public_url(obj)

        if teacher_ok:
            pdf_path = tmp / f"{lesson_id}_teacher.pdf"
            if pdf_path.exists():
                obj = f"{lesson_id}_teacher.pdf"
                _storage_upload(obj, pdf_path.read_bytes(), "application/pdf")
                pdf_teacher_url = _storage_public_url(obj)

        if slides_ok:
            pdf_path = tmp / f"{lesson_id}_slides.pdf"
            if pdf_path.exists():
                obj = f"{lesson_id}_slides.pdf"
                _storage_upload(obj, pdf_path.read_bytes(), "application/pdf")
                pdf_slides_url = _storage_public_url(obj)

        if do_now_ok:
            pdf_path = tmp / f"{lesson_id}_do_now.pdf"
            if pdf_path.exists():
                obj = f"{lesson_id}_do_now.pdf"
                _storage_upload(obj, pdf_path.read_bytes(), "application/pdf")
                pdf_do_now_url = _storage_public_url(obj)

    # overall_ok: only editions that were attempted must succeed; slides are
    # independent — a slides failure doesn't poison the overall flag when
    # student/teacher both succeeded (or weren't attempted).
    attempted_packet = bool(tex_student or tex_teacher or yaml_text)
    overall_ok = (not attempted_packet or (student_ok and teacher_ok))
    if tex_slides and not slides_ok:
        overall_ok = False
    if tex_do_now and not do_now_ok:
        overall_ok = False

    built_editions = [e for e, flag in [("student", student_ok),
                                         ("teacher", teacher_ok),
                                         ("slides", slides_ok),
                                         ("do_now", do_now_ok)] if flag]
    log.info("%s build done — built: %s", lesson_id,
             ", ".join(built_editions) if built_editions else "none")

    _write_build_status(
        lesson_id,
        ok=overall_ok,
        log_tail="" if overall_ok else log_tail,
        has_pdf_student=bool(pdf_student_url),
        has_pdf_teacher=bool(pdf_teacher_url),
        has_slides=bool(pdf_slides_url),
        user_name=x_user_name,
    )

    return {
        "ok": overall_ok,
        "pdf_student_url": pdf_student_url,
        "pdf_teacher_url": pdf_teacher_url,
        "pdf_slides_url": pdf_slides_url,
        "pdf_do_now_url": pdf_do_now_url,
        "log_tail": "" if overall_ok else log_tail,
    }


@app.put("/tex/{lesson_id}/{edition}")
async def put_tex(
    lesson_id: str,
    edition: str,
    request: Request,
    x_passcode: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
    if_match_sha: str | None = Header(default=None, alias="if-match-sha"),
) -> dict:
    _validate_lesson_id(lesson_id)
    _validate_edition(edition)
    _check_passcode(x_passcode)

    body = await request.body()
    tex_text = body.decode("utf-8")

    if if_match_sha:
        row = _rest_get_lesson(lesson_id)
        col = f"tex_{edition}"
        current_tex = (row.get(col) or "") if row else ""
        server_sha = hashlib.sha256(current_tex.encode("utf-8")).hexdigest()
        if server_sha != if_match_sha:
            changed_by = _rest_last_audit_changed_by(lesson_id)
            return JSONResponse(
                status_code=409,
                content={
                    "conflict": True,
                    "current_tex": current_tex,
                    "current_sha": server_sha,
                    "changed_by": changed_by,
                },
            )

    _rest_update_lesson(lesson_id, {f"tex_{edition}": tex_text}, x_user_name)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Upload-endpoint constants
# ---------------------------------------------------------------------------

TOPIC_PDF_RE = re.compile(r"^\d-\d$")
ITEM_ID_RE   = re.compile(r"^[a-zA-Z0-9-]+(?:-[a-zA-Z0-9]+)*$")

DOCX_KINDS = {"student", "teacher", "slides"}

# MIME types for upload validation
MIME_PDF   = "application/pdf"
MIME_DOCX  = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_PPTX  = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
MIME_PNG   = "image/png"
MIME_JPG   = "image/jpeg"

# Bucket names for the three new upload families
BUCKET_TOPIC_PDF    = "topic-pdfs"
BUCKET_LESSON_DOCX  = "lesson-docx"
BUCKET_SCREENSHOTS  = "item-screenshots"


# ---------------------------------------------------------------------------
# Bucket-creation helper
# ---------------------------------------------------------------------------

def _ensure_bucket(name: str, *, public_read: bool = True) -> None:
    """Create bucket if it doesn't already exist. Idempotent — 409 is success."""
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/bucket",
        headers={
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json",
        },
        json={"name": name, "public": public_read},
        timeout=10,
    )
    if r.status_code not in (200, 201, 409):
        log.warning("_ensure_bucket(%s): unexpected response %s %s", name, r.status_code, r.text[:200])


def _storage_upload_to(bucket: str, object_path: str, body: bytes, content_type: str) -> None:
    """Upload (or replace) an object in the given Supabase Storage bucket."""
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{bucket}/{object_path}",
        headers={
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY,
            "Content-Type": content_type,
            "x-upsert": "true",
        },
        data=body,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"storage upload {bucket}/{object_path}: {r.status_code} {r.text[:200]}")


def _storage_public_url_bucket(bucket: str, object_path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{object_path}"


# Ensure the three new buckets exist at startup (idempotent).
try:
    _ensure_bucket(BUCKET_TOPIC_PDF)
    _ensure_bucket(BUCKET_LESSON_DOCX)
    _ensure_bucket(BUCKET_SCREENSHOTS)
except Exception as _e:
    log.warning("startup _ensure_bucket failed (non-fatal): %s", _e)


# ---------------------------------------------------------------------------
# Upload auth helper
# ---------------------------------------------------------------------------

def _check_upload_auth(x_passcode: str | None, x_user_name: str | None) -> str:
    """Check passcode + require non-empty X-User-Name. Returns user_name."""
    _check_passcode(x_passcode)
    if not x_user_name or not x_user_name.strip():
        raise HTTPException(status_code=401, detail="X-User-Name header is required for uploads")
    return x_user_name.strip()


# ---------------------------------------------------------------------------
# A. POST /upload/topic-pdf/{topic}/{edition}
# ---------------------------------------------------------------------------
#
# Smoke-test (curl):
#   curl -X POST http://localhost:8080/upload/topic-pdf/4-3/SE \
#        -H "X-Passcode: changeme123" \
#        -H "X-User-Name: testuser" \
#        -F "file=@a2_4-3_SE.pdf"

@app.post("/upload/topic-pdf/{topic}/{edition}")
async def upload_topic_pdf(
    topic: str,
    edition: str,
    file: UploadFile = File(...),
    x_passcode: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
) -> dict:
    user = _check_upload_auth(x_passcode, x_user_name)

    if not TOPIC_PDF_RE.match(topic):
        raise HTTPException(status_code=400, detail="topic must match digit-digit (e.g. 4-3)")
    if edition not in ("SE", "TE"):
        raise HTTPException(status_code=400, detail="edition must be SE or TE")

    # Content-Type validation: allow application/pdf OR filename ending in .pdf
    ct = (file.content_type or "").lower()
    fname = (file.filename or "").lower()
    if ct != MIME_PDF and not fname.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF (application/pdf or .pdf extension)")

    body = await file.read()
    object_path = f"a2_{topic}_{edition}.pdf"

    try:
        _storage_upload_to(BUCKET_TOPIC_PDF, object_path, body, MIME_PDF)
    except RuntimeError as exc:
        log.error("upload/topic-pdf %s/%s failed: %s", topic, edition, exc)
        raise HTTPException(status_code=502, detail=str(exc))

    url = _storage_public_url_bucket(BUCKET_TOPIC_PDF, object_path)
    log.info("upload/topic-pdf topic=%s edition=%s user=%s size=%d ok", topic, edition, user, len(body))
    return {"ok": True, "url": url, "size": len(body), "uploaded_by": user}


# ---------------------------------------------------------------------------
# B. POST /upload/docx/{lesson_id}/{kind}
# ---------------------------------------------------------------------------
#
# Smoke-test (curl):
#   curl -X POST http://localhost:8080/upload/docx/L41_P2/student \
#        -H "X-Passcode: changeme123" \
#        -H "X-User-Name: testuser" \
#        -F "file=@L41_P2_student.docx"
#
#   curl -X POST http://localhost:8080/upload/docx/L41_P2/slides \
#        -H "X-Passcode: changeme123" \
#        -H "X-User-Name: testuser" \
#        -F "file=@L41_P2_slides.pptx"

_DOCX_KIND_META = {
    # kind -> (expected_mime, expected_ext, storage_ext)
    "student": (MIME_DOCX, ".docx", ".docx"),
    "teacher": (MIME_DOCX, ".docx", ".docx"),
    "slides":  (MIME_PPTX, ".pptx", ".pptx"),
}


@app.post("/upload/docx/{lesson_id}/{kind}")
async def upload_docx(
    lesson_id: str,
    kind: str,
    file: UploadFile = File(...),
    x_passcode: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
) -> dict:
    user = _check_upload_auth(x_passcode, x_user_name)
    _validate_lesson_id(lesson_id)

    if kind not in DOCX_KINDS:
        raise HTTPException(status_code=400, detail="kind must be student, teacher, or slides")

    expected_mime, expected_ext, storage_ext = _DOCX_KIND_META[kind]
    ct = (file.content_type or "").lower()
    fname = (file.filename or "").lower()

    if ct != expected_mime and not fname.endswith(expected_ext):
        raise HTTPException(
            status_code=400,
            detail=f"kind={kind!r} requires {expected_ext} file (MIME {expected_mime}); got content-type={ct!r}, filename={file.filename!r}",
        )

    body = await file.read()
    object_path = f"{lesson_id}_{kind}{storage_ext}"

    try:
        _storage_upload_to(BUCKET_LESSON_DOCX, object_path, body, expected_mime)
    except RuntimeError as exc:
        log.error("upload/docx %s/%s failed: %s", lesson_id, kind, exc)
        raise HTTPException(status_code=502, detail=str(exc))

    url = _storage_public_url_bucket(BUCKET_LESSON_DOCX, object_path)
    log.info("upload/docx lesson=%s kind=%s user=%s size=%d ok", lesson_id, kind, user, len(body))
    return {"ok": True, "url": url, "size": len(body), "uploaded_by": user}


# ---------------------------------------------------------------------------
# C. POST /upload/screenshot/{item_id}
# ---------------------------------------------------------------------------
#
# Smoke-test (curl):
#   curl -X POST http://localhost:8080/upload/screenshot/4-1-savvas-q26 \
#        -H "X-Passcode: changeme123" \
#        -H "X-User-Name: testuser" \
#        -F "file=@question_screenshot.png"
#
#   curl -X POST http://localhost:8080/upload/screenshot/3-5-savvas-q12 \
#        -H "X-Passcode: changeme123" \
#        -H "X-User-Name: testuser" \
#        -F "file=@question_screenshot.jpg"

_SCREENSHOT_MIMES = {MIME_PNG, MIME_JPG}
_SCREENSHOT_EXTS  = {".png", ".jpg", ".jpeg"}
_SCREENSHOT_EXT_MAP = {
    MIME_PNG: ".png",
    MIME_JPG: ".jpg",
    # fallback by filename extension
    ".png": ".png",
    ".jpg": ".jpg",
    ".jpeg": ".jpg",
}


@app.post("/upload/screenshot/{item_id}")
async def upload_screenshot(
    item_id: str,
    file: UploadFile = File(...),
    x_passcode: str | None = Header(default=None),
    x_user_name: str | None = Header(default=None),
) -> dict:
    user = _check_upload_auth(x_passcode, x_user_name)

    if not ITEM_ID_RE.match(item_id):
        raise HTTPException(
            status_code=400,
            detail="item_id must be alphanumeric+dashes (e.g. 4-1-savvas-q26)",
        )

    ct = (file.content_type or "").lower()
    fname = (file.filename or "").lower()

    # Determine storage extension: prefer MIME, fall back to filename ext
    if ct in _SCREENSHOT_MIMES:
        storage_ext = _SCREENSHOT_EXT_MAP[ct]
    else:
        # Try filename extension
        for ext in (".png", ".jpg", ".jpeg"):
            if fname.endswith(ext):
                storage_ext = _SCREENSHOT_EXT_MAP[ext]
                break
        else:
            raise HTTPException(
                status_code=400,
                detail="Screenshot must be PNG or JPG (image/png, image/jpeg, or .png/.jpg extension)",
            )

    body = await file.read()
    object_path = f"{item_id}{storage_ext}"
    upload_mime = MIME_PNG if storage_ext == ".png" else MIME_JPG

    try:
        _storage_upload_to(BUCKET_SCREENSHOTS, object_path, body, upload_mime)
    except RuntimeError as exc:
        log.error("upload/screenshot %s failed: %s", item_id, exc)
        raise HTTPException(status_code=502, detail=str(exc))

    url = _storage_public_url_bucket(BUCKET_SCREENSHOTS, object_path)
    log.info("upload/screenshot item=%s user=%s size=%d ok", item_id, user, len(body))
    return {"ok": True, "url": url, "size": len(body), "uploaded_by": user}
