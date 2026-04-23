import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { SUPABASE_URL, SUPABASE_ANON_KEY } from "/config.js";

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

  async itemsForLesson(lesson) {
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

// jsdelivr serves binary files with correct Content-Type and NO
// Content-Disposition: attachment header — so PDFs render inline in the
// browser instead of downloading (which raw.githubusercontent.com forces).
// Placeholder URL scheme until Railway pdflatex service wires up (step 3).
const CDN_BASE = "https://cdn.jsdelivr.net/gh/robjohncolson/Lesson_planning@main";

export function pdfUrl(lessonId, kind) {
  const fileMap = {
    student: `tex/${lessonId}_student.pdf`,
    teacher: `tex/${lessonId}_teacher.pdf`,
    slides:  `tex/${lessonId}_slides.pdf`,
  };
  return `${CDN_BASE}/${fileMap[kind]}`;
}

// Tex source fetch — the Flask console lets teachers view tex when no
// YAML spec exists. We fetch from jsdelivr as plain text. Returns null
// on 404 so the caller can show a graceful fallback.
export async function getTex(lessonId, kind) {
  const file = `tex/${lessonId}_${kind}.tex`;
  const r = await fetch(`${CDN_BASE}/${file}`, { cache: "no-cache" });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`getTex ${file}: HTTP ${r.status}`);
  return await r.text();
}
