import { api } from "/js/api.js";

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

export async function renderItemList(lesson, container, onItemClick) {
  container.innerHTML = '<div class="loading">Loading items…</div>';
  let items;
  try {
    items = await api.itemsForLesson(lesson);
  } catch (err) {
    container.innerHTML = `<div class="empty-msg">Failed to load items: ${escHtml(err.message)}</div>`;
    return;
  }
  if (!items.length) {
    container.innerHTML = '<div class="empty-msg">No items for this lesson.</div>';
    return;
  }
  container.innerHTML = "";
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "item-row";
    row.dataset.id = item.id;
    row.innerHTML =
      `<span class="item-id">${escHtml(item.id)}</span>` +
      `<span class="item-role">${escHtml(item.role ?? "")}</span>` +
      dokBadge(item.dok) +
      `<span class="item-prompt">${escHtml(truncate(item.prompt))}</span>`;
    row.addEventListener("click", () => onItemClick(item.id));
    container.appendChild(row);
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
