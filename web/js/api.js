import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { SUPABASE_URL, SUPABASE_ANON_KEY, RAILWAY_URL } from "/config.js";
import { passcode } from "/js/passcode.js";

// schema option routes all queries to lesson_planning without per-call overrides
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
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
    // N-N; pass-through anything else (e.g. "3-5" directly).
    const m = /^L(\d)(\d)_P\d$/.exec(lessonOrId || "");
    const lesson = m ? `${m[1]}-${m[2]}` : lessonOrId;
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
      "id, lesson, role, dok, topics, skill_tokens, standards, tags, prompt");
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
};

// jsdelivr: slides PDFs still live in git (not Supabase Storage).
const CDN_BASE = "https://cdn.jsdelivr.net/gh/robjohncolson/Lesson_planning@main";

// PDF URLs: student + teacher come from Supabase Storage; slides stay on jsdelivr.
export function pdfUrl(lessonId, kind) {
  if (kind === "slides") {
    return `${CDN_BASE}/tex/${lessonId}_slides.pdf`;
  }
  return `${SUPABASE_URL}/storage/v1/object/public/lesson-pdfs/${lessonId}_${kind}.pdf`;
}

// Tex source: read from Supabase lessons.tex_{edition} column.
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

// saveTex: PUT tex source to Railway. Throws on non-2xx.
// On 401: clears stored passcode and throws a WrongPasscode error.
export async function saveTex(lessonId, edition, body) {
  const pc = passcode.get();
  const r = await fetch(`${RAILWAY_URL}/tex/${lessonId}/${edition}`, {
    method: "PUT",
    headers: { "Content-Type": "text/plain", "X-Passcode": pc },
    body,
  });
  if (r.status === 401) {
    passcode.clear();
    const err = new Error("Wrong passcode — please try again.");
    err.name = "WrongPasscode";
    throw err;
  }
  if (!r.ok) throw new Error(`saveTex ${lessonId}/${edition}: HTTP ${r.status}`);
}

// rebuildPdf: POST to Railway build endpoint. Returns parsed JSON response.
export async function rebuildPdf(lessonId) {
  const pc = passcode.get();
  const r = await fetch(`${RAILWAY_URL}/build/${lessonId}`, {
    method: "POST",
    headers: { "X-Passcode": pc },
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
