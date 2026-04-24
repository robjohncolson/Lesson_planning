// realtime.js — per-lesson presence + Postgres-change subscriptions.
// Exports one factory: subscribeLesson({ lessonId, username, onRemoteSave, onPresenceChange })
// Returns: async unsubscribe() that tears the channel down.

import { supabase } from "/js/api.js";

const TEX_FIELDS = ["tex_student", "tex_teacher", "tex_slides", "tex_do_now", "yaml_text"];

export function subscribeLesson({ lessonId, username, onRemoteSave, onPresenceChange }) {
  const channel = supabase.channel(`lesson:${lessonId}`);

  // Postgres-change: fires when THIS row UPDATEs
  channel.on(
    "postgres_changes",
    {
      event: "UPDATE",
      schema: "lesson_planning",
      table: "lessons",
      filter: `id=eq.${lessonId}`,
    },
    (payload) => {
      const { new: newRow, old: oldRow } = payload;
      for (const field of TEX_FIELDS) {
        if (newRow[field] !== oldRow[field]) {
          onRemoteSave({
            field,
            old_value: oldRow[field] ?? null,
            new_value: newRow[field] ?? null,
            changed_at: newRow.updated_at ?? new Date().toISOString(),
          });
          return; // fire once for the first changed field
        }
      }
    }
  );

  // Presence sync: flatten presenceState to unique usernames list
  channel.on("presence", { event: "sync" }, () => {
    const state = channel.presenceState();
    const users = [];
    for (const presences of Object.values(state)) {
      for (const p of presences) {
        if (p.username && !users.includes(p.username)) {
          users.push(p.username);
        }
      }
    }
    onPresenceChange(users);
  });

  channel.subscribe(async (status) => {
    if (status === "SUBSCRIBED") {
      await channel.track({ username, joined_at: new Date().toISOString() });
    }
  });

  return async function unsubscribe() {
    await channel.untrack();
    await supabase.removeChannel(channel);
  };
}
