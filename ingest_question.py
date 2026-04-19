"""Ingest textbook screenshots into the question-bank registry.

Reads image(s), calls Claude vision with that lesson's calibration anchors
as reference, and appends one JSONL entry per screenshot to
questionbank/registry.jsonl.

The calibration anchors are cached (prompt caching) so re-ingesting many
images for the same lesson only pays the anchor-read cost once per 5 minutes.

Usage:
    python ingest_question.py images/3-5_ex4.png
    python ingest_question.py images/*.png --lesson 3-5
    python ingest_question.py img.png --dry-run       # print JSON, don't append
    python ingest_question.py img.png --edit          # open JSON in $EDITOR before append

Env:
    ANTHROPIC_API_KEY   required
    INGEST_MODEL        optional, defaults to claude-sonnet-4-6
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import qb

try:
    import anthropic
except ImportError:
    sys.stderr.write("Missing dependency: pip install anthropic\n")
    sys.exit(2)

MODEL = os.environ.get("INGEST_MODEL", "claude-sonnet-4-6")
ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "questionbank" / "images"


SYSTEM_PROMPT = """You are a math curriculum assistant classifying textbook
questions for an Algebra 2 question bank. You must:

1. Transcribe the question prompt exactly. Preserve math notation in plain
   text: use ^ for exponents, √ for square roots, · for multiplication when
   needed, proper minus signs (−), and subscripts spelled out.
2. Transcribe multiple-choice answers in order if present. If the question
   is open-response, leave `answers` as an empty list.
3. Identify the correct answer if it is visible or marked. Otherwise set
   `correct` to null.
4. Propose a Depth of Knowledge (DOK) level by calibrating against the
   anchors provided. Pick the anchor your question most resembles in
   cognitive demand, and write a one-sentence rationale citing it.
5. Propose topic tags drawn from the provided topic vocabulary. Add new
   tags only if none in the vocabulary fit.
6. Set has_visual=true ONLY if solving the question requires reading a
   graph or figure. A question that merely shows a decorative icon is
   has_visual=false.

Return a single JSON object with these fields and NO other text:
{
  "prompt": string,
  "answers": [string, ...],
  "correct": integer | string | null,
  "dok": 1 | 2 | 3,
  "dok_rationale": string,
  "topics": [string, ...],
  "has_visual": boolean,
  "source_hint": string,
  "notes": string
}

`source_hint` is your best guess at what to write for the `source` field,
e.g. "Savvas Practice #N", "Savvas Example N", "Lesson Quiz". Leave blank
if unclear.
"""


def infer_lesson_from_path(p: Path) -> str | None:
    m = re.search(r"(\d+-\d+)", p.name)
    return m.group(1) if m else None


def load_calibration_text(lesson: str) -> str:
    cal = qb.load_calibration(lesson)
    if not cal:
        sys.stderr.write(
            f"ERROR: no calibration file at questionbank/calibration/{lesson}.json\n"
            f"Populate Savvas-declared DOK2/DOK3 anchors for lesson {lesson} first.\n"
        )
        sys.exit(1)
    # Flatten into a deterministic reference block.
    parts = [f"# Calibration anchors for lesson {lesson}: {cal.get('title', '')}"]
    parts.append("\n## DOK 2 anchors (Savvas-declared)")
    for a in cal.get("dok2_anchors", []):
        parts.append(f"- **{a.get('source', '')}** — {a.get('prompt', '')}\n  Why DOK 2: {a.get('why_dok2', '')}")
    parts.append("\n## DOK 3 anchors (Savvas-declared)")
    for a in cal.get("dok3_anchors", []):
        parts.append(f"- **{a.get('source', '')}** — {a.get('prompt', '')}\n  Why DOK 3: {a.get('why_dok3', '')}")
    parts.append("\n## Topic vocabulary (prefer these tags)")
    parts.append(", ".join(cal.get("topic_vocabulary", [])))
    parts.append(
        "\nCalibration rule: when classifying a new question, compare cognitive demand "
        "to the anchors above. DOK 1 = recall of a fact or single-step procedure. "
        "DOK 2 = multi-step procedure with known strategy. DOK 3 = strategic thinking, "
        "critique, justification, or non-routine construction."
    )
    return "\n".join(parts)


def call_claude(client, lesson: str, image_path: Path) -> dict:
    calibration_text = load_calibration_text(lesson)
    image_bytes = image_path.read_bytes()
    b64 = base64.standard_b64encode(image_bytes).decode()
    ext = image_path.suffix.lower().lstrip(".")
    media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                  "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/png")

    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": calibration_text,
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64,
                    },
                },
                {
                    "type": "text",
                    "text": f"Classify the question in the image above using the calibration anchors.",
                },
            ],
        }],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    # Strip common ```json fences if present.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL).strip()
    return json.loads(text)


def next_id(lesson: str, source_hint: str) -> str:
    base = f"{lesson}-"
    # derive a short slug from source_hint
    slug = re.sub(r"[^a-z0-9]+", "-", source_hint.lower()).strip("-") or "q"
    slug = slug[:40]
    existing = {q["id"] for q in qb.load()}
    candidate = f"{base}{slug}"
    i = 2
    while candidate in existing:
        candidate = f"{base}{slug}-{i}"
        i += 1
    return candidate


def edit_json(entry: dict) -> dict:
    editor = os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "vi")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(entry, tf, indent=2, ensure_ascii=False)
        tmp_path = tf.name
    try:
        subprocess.run([editor, tmp_path], check=True)
        return json.loads(Path(tmp_path).read_text(encoding="utf-8"))
    finally:
        os.unlink(tmp_path)


def ingest_one(client, image_path: Path, lesson: str, dry_run: bool, do_edit: bool) -> None:
    # Move image into questionbank/images/ if it isn't there already.
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    if image_path.resolve().parent != IMAGES_DIR.resolve():
        target = IMAGES_DIR / image_path.name
        if not target.exists():
            target.write_bytes(image_path.read_bytes())
        image_path = target

    print(f"[ingest] {image_path.name}  lesson={lesson}  model={MODEL}", file=sys.stderr)
    raw = call_claude(client, lesson, image_path)

    source_hint = raw.get("source_hint") or "q"
    qid = next_id(lesson, source_hint)

    entry = {
        "id": qid,
        "lesson": lesson,
        "source": raw.get("source_hint") or "",
        "page": None,
        "image": str(image_path.relative_to(ROOT)).replace("\\", "/"),
        "has_visual": bool(raw.get("has_visual", False)),
        "prompt": raw["prompt"],
        "answers": raw.get("answers", []),
        "correct": raw.get("correct"),
        "dok": int(raw["dok"]),
        "dok_rationale": raw.get("dok_rationale", ""),
        "topics": raw.get("topics", []),
        "tags": [],
        "used_in": [],
        "notes": raw.get("notes", ""),
        "created_at": dt.date.today().isoformat(),
    }

    if do_edit:
        entry = edit_json(entry)

    pretty = json.dumps(entry, indent=2, ensure_ascii=False)
    print(pretty)

    if dry_run:
        print("[ingest] --dry-run: not writing.", file=sys.stderr)
        return

    qb.append(entry)
    print(f"[ingest] appended id={entry['id']}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+", help="screenshot paths")
    ap.add_argument("--lesson", help="lesson code (e.g. 3-5). Inferred from filename if omitted.")
    ap.add_argument("--dry-run", action="store_true", help="don't append to registry")
    ap.add_argument("--edit", action="store_true", help="open stub in $EDITOR before append")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.stderr.write("ERROR: ANTHROPIC_API_KEY not set.\n")
        sys.exit(2)

    client = anthropic.Anthropic()

    for img in args.images:
        p = Path(img)
        if not p.exists():
            sys.stderr.write(f"skip: {img} not found\n")
            continue
        lesson = args.lesson or infer_lesson_from_path(p)
        if not lesson:
            sys.stderr.write(f"skip: couldn't infer --lesson from {p.name}; pass --lesson\n")
            continue
        ingest_one(client, p, lesson, args.dry_run, args.edit)


if __name__ == "__main__":
    main()
