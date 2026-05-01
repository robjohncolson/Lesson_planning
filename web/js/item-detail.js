import { api, screenshotUrl, uploadAsset } from "/js/api.js";
import { passcode } from "/js/passcode.js";
import { username } from "/js/username.js";

function escHtml(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function dokBadge(dok) {
  if (!dok) return "";
  return `<span class="dok-badge dok-${escHtml(dok)}">DOK ${escHtml(dok)}</span>`;
}

function tagList(arr, cssClass) {
  if (!arr || arr.length === 0) return "";
  return arr.map(t => `<span class="${cssClass}">${escHtml(t)}</span>`).join(" ");
}

// Truncate prompt for list view — full text in detail view
function truncate(s, max = 80) {
  const str = s ?? "";
  return str.length > max ? str.slice(0, max) + "…" : str;
}

// ── Screenshot helpers ───────────────────────────────────────────────────────
// Probe all item IDs for screenshots in parallel (one HEAD each).
// Returns Map<itemId, { exists: bool, ext: "png"|"jpg", url: string }>.
async function probeScreenshots(itemIds) {
  const results = new Map();
  await Promise.all(itemIds.map(async (id) => {
    // Try png first, then jpg
    for (const ext of ["png", "jpg"]) {
      const url = screenshotUrl(id, ext);
      const ok = await fetch(url, { method: "HEAD" }).then(r => r.ok).catch(() => false);
      if (ok) {
        results.set(id, { exists: true, ext, url });
        return;
      }
    }
    results.set(id, { exists: false, ext: "png", url: screenshotUrl(id, "png") });
  }));
  return results;
}

function attachScreenshotWidget(row, itemId, screenshotInfo, onReprobe) {
  const widget = document.createElement("span");
  widget.className = "screenshot-widget";

  if (screenshotInfo && screenshotInfo.exists) {
    const link = document.createElement("a");
    link.className = "screenshot-view-link";
    link.href = screenshotInfo.url;
    link.target = "_blank";
    link.rel = "noopener";
    link.title = "View screenshot";
    link.textContent = "📷 view";
    widget.appendChild(link);
  } else {
    const upBtn = document.createElement("button");
    upBtn.className = "btn-screenshot-upload";
    upBtn.title = "Upload screenshot for this item";
    upBtn.textContent = "📷 upload";
    upBtn.addEventListener("click", (e) => {
      e.stopPropagation(); // don't open item detail
      const input = document.createElement("input");
      input.type = "file";
      input.accept = "image/png,image/jpeg";
      input.addEventListener("change", async () => {
        const file = input.files[0];
        if (!file) return;
        try {
          const r = await uploadAsset(
            `/upload/screenshot/${encodeURIComponent(itemId)}`,
            file, passcode.get(), username.get()
          );
          if (r.ok && onReprobe) onReprobe(itemId, widget);
        } catch {}
      });
      input.click();
    });
    widget.appendChild(upBtn);
  }
  row.appendChild(widget);
}

// Phase display order + human labels. Matches the CHECK constraint in
// supabase/migrations/005_lesson_phases.sql.
const PHASE_ORDER = ["do_now", "launch", "explore", "share_summary", "exit", "reinforcement"];
const PHASE_LABELS = {
  do_now:         "Do Now",
  launch:         "Launch",
  explore:        "Explore",
  share_summary:  "Share / Summary",
  exit:           "Exit Ticket",
  reinforcement:  "Optional Reinforcement",
};

function renderItemRow(item, onItemClick, screenshotInfo, onReprobe) {
  const row = document.createElement("div");
  row.className = "item-row";
  row.dataset.id = item.id;
  row.innerHTML =
    `<span class="item-id">${escHtml(item.id)}</span>` +
    `<span class="item-role">${escHtml(item.role ?? "")}</span>` +
    dokBadge(item.dok) +
    `<span class="item-prompt">${escHtml(truncate(item.prompt))}</span>`;
  row.addEventListener("click", () => onItemClick(item.id));
  // Screenshot widget appended after click handler so stopPropagation works
  attachScreenshotWidget(row, item.id, screenshotInfo, onReprobe);
  return row;
}

function renderUnmatchedRow(label) {
  const row = document.createElement("div");
  row.className = "item-row item-row-unmatched";
  row.innerHTML =
    `<span class="item-prompt" style="opacity:.75">${escHtml(truncate(label, 120))}</span>` +
    `<span class="item-role" style="color:#888">(unmatched)</span>`;
  return row;
}

export async function renderItemList(lesson, container, onItemClick) {
  container.innerHTML = '<div class="loading">Loading items…</div>';

  // Fetch items and phases in parallel. The phases query uses lesson_id
  // (LNN_Pn form); items uses the LNN_Pn -> N-N conversion done inside
  // api.itemsForLesson. If the caller passed "3-5" directly, phase lookup
  // will return [] and we fall back to the flat list.
  let items, phases;
  try {
    [items, phases] = await Promise.all([
      api.itemsForLesson(lesson),
      api.listPhasesForLesson(lesson),
    ]);
  } catch (err) {
    container.innerHTML = `<div class="empty-msg">Failed to load items: ${escHtml(err.message)}</div>`;
    return;
  }

  if (!items.length && (!phases || !phases.length)) {
    container.innerHTML = '<div class="empty-msg">No items for this lesson.</div>';
    return;
  }

  // Fire all screenshot probes in parallel — one HEAD per item (tries png then jpg).
  // Build the map before rendering so widgets render with correct initial state.
  const screenshotMap = await probeScreenshots(items.map(i => i.id));

  // onReprobe: after an upload, re-probe that single item and refresh its widget.
  function onReprobe(itemId, widget) {
    probeScreenshots([itemId]).then(m => {
      const info = m.get(itemId);
      // Replace old widget contents in place
      widget.innerHTML = "";
      if (info && info.exists) {
        const link = document.createElement("a");
        link.className = "screenshot-view-link";
        link.href = info.url;
        link.target = "_blank";
        link.rel = "noopener";
        link.title = "View screenshot";
        link.textContent = "📷 view";
        widget.appendChild(link);
      }
    }).catch(() => {});
  }

  container.innerHTML = "";

  // Fall-through: no phase data → flat list (legacy behavior + note).
  if (!phases || !phases.length) {
    const note = document.createElement("div");
    note.className = "phase-fallback-note";
    note.style.cssText = "padding:6px 0;color:#888;font-size:.9em;";
    note.textContent = "No phase data yet for this period — showing all items for the lesson code.";
    container.appendChild(note);
    for (const item of items) {
      container.appendChild(renderItemRow(item, onItemClick, screenshotMap.get(item.id), onReprobe));
    }
    return;
  }

  // Phase-grouped rendering.
  const itemsById = new Map(items.map(i => [i.id, i]));
  const usedItemIds = new Set();

  // Bucket phases
  const byPhase = new Map();
  for (const p of phases) {
    if (!byPhase.has(p.phase)) byPhase.set(p.phase, []);
    byPhase.get(p.phase).push(p);
  }

  for (const phaseKey of PHASE_ORDER) {
    const rows = byPhase.get(phaseKey);
    if (!rows || !rows.length) continue;

    const header = document.createElement("h3");
    header.className = `phase-header phase-${phaseKey}`;
    header.style.cssText =
      "margin:14px 0 4px;padding:4px 8px;font-size:1em;border-left:4px solid #4a90e2;background:#f4f8fc;";
    header.textContent = PHASE_LABELS[phaseKey] || phaseKey;
    container.appendChild(header);

    // Phase rows are ordered by position from the query
    rows.sort((a, b) => a.position - b.position);
    for (const pr of rows) {
      if (pr.item_id && itemsById.has(pr.item_id)) {
        usedItemIds.add(pr.item_id);
        container.appendChild(renderItemRow(itemsById.get(pr.item_id), onItemClick, screenshotMap.get(pr.item_id), onReprobe));
      } else {
        // Show the literal label so teacher can still see the item slot.
        container.appendChild(renderUnmatchedRow(pr.label || pr.item_id || "(missing)"));
      }
    }
  }

  // "Other items in this lesson code" — collapsed <details> with the rest.
  const others = items.filter(i => !usedItemIds.has(i.id));
  if (others.length) {
    const details = document.createElement("details");
    details.className = "phase-other-items";
    details.style.cssText = "margin-top:16px;padding:6px 0;border-top:1px dashed #ccc;";
    const summary = document.createElement("summary");
    summary.style.cssText = "cursor:pointer;color:#666;font-size:.95em;padding:4px 0;";
    summary.textContent = `Other items in this lesson code (${others.length})`;
    details.appendChild(summary);
    for (const item of others) {
      details.appendChild(renderItemRow(item, onItemClick, screenshotMap.get(item.id), onReprobe));
    }
    container.appendChild(details);
  }
}

export async function renderItemDetail(itemId, container) {
  container.innerHTML = '<div class="loading">Loading…</div>';
  const item = await api.getItem(itemId);
  if (!item) {
    container.innerHTML = '<div class="empty-msg">Item not found.</div>';
    return;
  }

  const standardsTags = tagList(item.standards,   "tag tag-standard");
  const skillsTags    = tagList(item.skill_tokens, "tag tag-skill");
  const topicsTags    = tagList(item.topics,       "tag tag-topic");

  const tagsBlock = (standardsTags || skillsTags || topicsTags)
    ? `<div class="item-tags">${standardsTags}${skillsTags}${topicsTags}</div>`
    : "";

  const teacherBlock = item.teacher_answer
    ? `<h4>Teacher Answer</h4><pre class="item-field">${escHtml(item.teacher_answer)}</pre>`
    : "";

  const notesBlock = item.notes
    ? `<h4>Notes</h4><pre class="item-field">${escHtml(item.notes)}</pre>`
    : "";

  container.innerHTML =
    `<dl class="item-meta">` +
      `<dt>ID</dt><dd>${escHtml(item.id)}</dd>` +
      `<dt>Lesson</dt><dd>${escHtml(item.lesson ?? "")}</dd>` +
      `<dt>Role</dt><dd>${escHtml(item.role ?? "")}</dd>` +
      `<dt>DOK</dt><dd>${dokBadge(item.dok)}</dd>` +
    `</dl>` +
    tagsBlock +
    `<h4>Prompt</h4>` +
    `<pre class="item-prompt-full">${escHtml(item.prompt ?? "")}</pre>` +
    teacherBlock +
    notesBlock;
}
