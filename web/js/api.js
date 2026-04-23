import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { SUPABASE_URL, SUPABASE_ANON_KEY } from "/config.js";

// schema option routes all queries to lesson_planning without per-call overrides
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  db: { schema: "lesson_planning" },
});

function raise(ctx, error) {
  throw new Error(`${ctx}: ${error.message}`);
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
    // prompt is included so the DAG detail panel can render it; truncated at
    // render time, not here. ~1006 rows total; payload is still <1MB gzipped.
    const { data, error } = await supabase
      .from("items")
      .select("id, lesson, role, dok, topics, skill_tokens, standards, tags, prompt");
    if (error) raise("listAllItems", error);
    return data;
  },

  async listAllEdges() {
    const { data, error } = await supabase
      .from("edges")
      .select("from_id, to_id, kind");
    if (error) raise("listAllEdges", error);
    return data;
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

// GitHub raw URL — placeholder until Railway pdflatex service wires up (Phase A step 3)
export function pdfUrl(lessonId, kind) {
  const fileMap = {
    student: `tex/${lessonId}_student.pdf`,
    teacher: `tex/${lessonId}_teacher.pdf`,
    slides:  `tex/${lessonId}_slides.pdf`,
  };
  const file = fileMap[kind];
  return `https://raw.githubusercontent.com/robjohncolson/Lesson_planning/main/${file}`;
}
