import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { SUPABASE_URL, SUPABASE_ANON_KEY, RAILWAY_URL } from "/config.js";
import { passcode } from "/js/passcode.js";
import { username } from "/js/username.js";

// schema option routes all queries to lesson_planning without per-call overrides
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  db: { schema: "lesson_planning" },
});

function raise(ctx, error) {
  throw new Error(`${ctx}: ${error.message}`);
}

async function paginateAll(table, select, pageSize = 1000) {
  let out = [];
  let from = 0;
  while (true) {
    const { data, error } = await supabase
      .from(table).select(select).range(from, from + pageSize - 1);
    if (error) raise(`paginate ${table}`, error);
    out = out.concat(data);
    if (data.length < pageSize) return out;
    from += pageSize;
  }
}

export const api = {
  async listLessons() {
    const { data, error } = await supabase
      .from("lessons")
      .select("id, cadence, title, has_pdf_student, has_pdf_teacher, has_slides_pdf, updated_at")
      .order("id");
    if (error) raise("listLessons", error);
    return data;
  },

  async getLesson(id) {
    const { data, error } = await supabase
      .from("lessons")
      .select("*")
      .eq("id", id)
      .maybeSingle();
    if (error) raise("getLesson", error);
    return data;
  },

  async itemsForLesson(lessonOrId) {
    // Lessons table uses LNN_Pn ids (e.g. "L35_P2") but items.lesson in the
    // registry uses the topic-subtopic form (e.g. "3-5"). Convert LNN_Pn to
    // N-N. AP Stats uses APStats_6-4_P1 -> APStats-6-4. Pass through anything
    // else (e.g. "3-5" directly).
    // Strip optional variant suffix (e.g. _obs) before converting id to registry lesson field.
    // L35_P3_obs → L35_P3 so itemsForLesson looks up the same "3-5" registry entries.
    const strippedId = (lessonOrId || "").replace(/(_P\d)_[a-z][a-z0-9_]*$/, "$1");
    const algebra = /^L(\d)(\d)_P\d$/.exec(strippedId);
    const apStats = /^APStats_(\d+)-(\d+)_P\d$/.exec(strippedId);
    const lesson = algebra
      ? `${algebra[1]}-${algebra[2]}`
      : apStats
        ? `APStats-${apStats[1]}-${apStats[2]}`
        : strippedId;
    const { data, error } = await supabase
      .from("items")
      .select("*")
      .eq("lesson", lesson)
      .order("id");
    if (error) raise("itemsForLesson", error);
    return data;
  },

  async getItem(id) {
    const { data, error } = await supabase
      .from("items")
      .select("*")
      .eq("id", id)
      .maybeSingle();
    if (error) raise("getItem", error);
    return data;
  },

  async listAllItems() {
    // Paginate — PostgREST defaults to a 1000-row page cap; ~1006 items means
    // the first page silently truncates without explicit range requests.
    return paginateAll("items",
      "id, lesson, role, dok, topics, skill_tokens, standards, tags, prompt, updated_at");
  },

  // Delta fetch for dag.js cache: rows with updated_at strictly greater than
  // the caller's watermark. Paginated to survive large backfills.
  async listItemsUpdatedSince(isoTimestamp) {
    let out = [];
    let from = 0;
    const pageSize = 1000;
    while (true) {
      const { data, error } = await supabase
        .from("items")
        .select("id, lesson, role, dok, topics, skill_tokens, standards, tags, prompt, updated_at")
        .gt("updated_at", isoTimestamp)
        .order("updated_at", { ascending: true })
        .range(from, from + pageSize - 1);
      if (error) raise("listItemsUpdatedSince", error);
      out = out.concat(data);
      if (data.length < pageSize) return out;
      from += pageSize;
    }
  },

  async listAllEdges() {
    return paginateAll("edges", "from_id, to_id, kind");
  },

  async checkHealth() {
    try {
      const { error } = await supabase
        .from("lessons")
        .select("id")
        .limit(1);
      return !error;
    } catch {
      return false;
    }
  },

  // Return the set of item_ids that are actively used in any lesson phase.
  // Fetches all non-null item_ids from lesson_phases (paginated, though the
  // count is small relative to the 1000-row page cap). Returns a Set<string>.
  async listActiveItemIds() {
    let out = [];
    let from = 0;
    const pageSize = 1000;
    while (true) {
      const { data, error } = await supabase
        .from("lesson_phases")
        .select("item_id")
        .not("item_id", "is", null)
        .range(from, from + pageSize - 1);
      if (error) raise("listActiveItemIds", error);
      out = out.concat(data);
      if (data.length < pageSize) break;
      from += pageSize;
    }
    return new Set(out.map(r => r.item_id));
  },

  // Per-period phase mapping — see supabase/migrations/005_lesson_phases.sql.
  // Ordered by phase then position. Returns [] if no phases seeded for this
  // lesson_id — caller should fall back to flat item list.
  async listPhasesForLesson(lessonId) {
    const { data, error } = await supabase
      .from("lesson_phases")
      .select("id, lesson_id, phase, position, item_id, label")
      .eq("lesson_id", lessonId)
      .order("phase")
      .order("position");
    if (error) raise("listPhasesForLesson", error);
    return data;
  },

  async listSchedule() {
    const { data, error } = await supabase
      .from("schedule")
      .select("id, class_date, period, lesson_id, day_of_lesson, minutes, notes")
      .order("class_date")
      .order("period");
    if (error) raise("listSchedule", error);
    return data;
  },

  // getLastAudit: returns the most recent audit row for a lesson, or null.
  // The audit table lives in lesson_planning schema (same client scope).
  // Never throws — silently returns null on error or empty result.
  async getLastAudit(lessonId) {
    try {
      const { data, error } = await supabase
        .from("audit")
        .select("action, changed_at, changed_by")
        .eq("table_name", "lessons")
        .eq("row_id", lessonId)
        .order("changed_at", { ascending: false })
        .limit(1)
        .maybeSingle();
      if (error || !data) return null;
      return data;
    } catch {
      return null;
    }
  },
};

// All three PDF flavours (student/teacher/slides) live in Supabase Storage
// after Phase 1: the initial bulk-upload + any subsequent Railway rebuild
// both target lesson-pdfs/{lessonId}_{kind}.pdf.
export function pdfUrl(lessonId, kind) {
  return `${SUPABASE_URL}/storage/v1/object/public/lesson-pdfs/${lessonId}_${kind}.pdf`;
}

// Textbook PDFs (Savvas): stored in topic-pdfs bucket.
// topic: "4-1" | "4-3" | etc.  edition: "SE" | "TE"
export function topicPdfUrl(topic, edition) {
  return `${SUPABASE_URL}/storage/v1/object/public/topic-pdfs/a2_${topic}_${edition}.pdf`;
}

// Editable formats: DOCX lives in lesson-docx bucket.
// kind: "student" | "teacher"
export function docxUrl(lessonId, kind) {
  return `${SUPABASE_URL}/storage/v1/object/public/lesson-docx/${lessonId}_${kind}.docx`;
}

// PPTX (slides) in same lesson-docx bucket.
export function pptxUrl(lessonId) {
  return `${SUPABASE_URL}/storage/v1/object/public/lesson-docx/${lessonId}_slides.pptx`;
}

// Per-item screenshots: item-screenshots bucket.
// ext: "png" | "jpg" (default "png")
export function screenshotUrl(itemId, ext = "png") {
  return `${SUPABASE_URL}/storage/v1/object/public/item-screenshots/${itemId}.${ext}`;
}

// Derive Algebra-2 topic string from lesson id.
// L41_P2 -> "4-1"   L35_P3_obs -> "3-5"
// APStats_* and anything unrecognised -> null (textbook section hidden).
export function lessonIdToTopic(lessonId) {
  const m = /^L(\d)(\d)_P\d/.exec(lessonId || "");
  return m ? `${m[1]}-${m[2]}` : null;
}

// Upload a file asset to a Railway endpoint with auth headers.
// endpoint: e.g. "/upload/topic-pdf/4-1/SE"
// Returns the fetch Response (caller checks .ok).
export async function uploadAsset(endpoint, file, pc, un) {
  const fd = new FormData();
  fd.append("file", file);
  const headers = { "X-Passcode": pc };
  if (un) headers["X-User-Name"] = un;
  return fetch(`${RAILWAY_URL}${endpoint}`, {
    method: "POST",
    headers,
    body: fd,
  });
}

// Tex source: read from Supabase lessons.tex_{edition} column.
// edition: "student" | "teacher" | "slides"
// Returns string or null (null = column empty / lesson not found).
export async function getTex(lessonId, edition) {
  const col = `tex_${edition}`;
  const { data, error } = await supabase
    .from("lessons")
    .select(col)
    .eq("id", lessonId)
    .maybeSingle();
  if (error) raise(`getTex ${lessonId}/${edition}`, error);
  return data ? (data[col] ?? null) : null;
}

// sha256Hex: hex sha256 of a string (empty string for null/undefined).
export async function sha256Hex(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s || ""));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}

// saveTex: PUT tex source to Railway. Throws on non-2xx.
// On 401: clears stored passcode and throws a WrongPasscode error.
// On 409: throws a TexConflict error with current_tex, current_sha, changed_by.
// baseSha (optional): hex sha256 of the tex the editor loaded; when set,
//   sends If-Match-Sha so the server can detect concurrent edits.
export async function saveTex(lessonId, edition, body, baseSha) {
  const pc = passcode.get();
  const un = username.get();
  const headers = { "Content-Type": "text/plain", "X-Passcode": pc };
  if (un) headers["X-User-Name"] = un;  // omit header when user cancelled prompt
  if (baseSha) headers["If-Match-Sha"] = baseSha;
  const r = await fetch(`${RAILWAY_URL}/tex/${lessonId}/${edition}`, {
    method: "PUT",
    headers,
    body,
  });
  if (r.status === 401) {
    passcode.clear();
    const err = new Error("Wrong passcode — please try again.");
    err.name = "WrongPasscode";
    throw err;
  }
  if (r.status === 409) {
    const payload = await r.json();
    const err = new Error("Tex conflict: document was modified by another user.");
    err.name = "TexConflict";
    err.conflict = true;
    err.current_tex = payload.current_tex;
    err.current_sha = payload.current_sha;
    err.changed_by = payload.changed_by;
    throw err;
  }
  if (!r.ok) throw new Error(`saveTex ${lessonId}/${edition}: HTTP ${r.status}`);
}

// rebuildPdf: POST to Railway build endpoint. Returns parsed JSON response.
export async function rebuildPdf(lessonId) {
  const pc = passcode.get();
  const un = username.get();
  const headers = { "X-Passcode": pc };
  if (un) headers["X-User-Name"] = un;
  const r = await fetch(`${RAILWAY_URL}/build/${lessonId}`, {
    method: "POST",
    headers,
  });
  if (r.status === 401) {
    passcode.clear();
    const err = new Error("Wrong passcode — please try again.");
    err.name = "WrongPasscode";
    throw err;
  }
  if (!r.ok) throw new Error(`rebuildPdf ${lessonId}: HTTP ${r.status}`);
  return await r.json();
}
