// Entry point for dag.html. Ports the JS that qb_graph.py used to inline
// into graph/graph.html, but reads nodes + edges from Supabase at runtime.
import { api } from "/js/api.js";

// ── Constants ──────────────────────────────────────────────────────────────────

const ROLE_COLORS = {
  "do-now-explore":        "#8ab4f8",
  "do-now-bridge":         "#8ab4f8",
  "launch-model-1":        "#34a853",
  "launch-model-2":        "#34a853",
  "explore-tps":           "#fbbc04",
  "explore-practice":      "#f28b82",
  "optional-stretch":      "#dadce0",
  "dok3-driver":           "#ea4335",
  "exit-recap":            "#9aa0a6",
  "assessment-rehearsal":  "#a78bfa",
  "assessment-shell":      "#c084fc",
};

const DEFAULT_COLOR = "#dadce0";

const EDGE_COLORS = {
  "prereq":    "#5f6368",
  "rehearses": "#1a73e8",
  "echoes":    "#ea4335",
};

// ── Helpers ────────────────────────────────────────────────────────────────────

function escHtml(s) {
  // Escape quotes too — ids land in data-target attributes, not just text content.
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Build the title string for a vis-network node.
 *
 * The Python template embeds literal two-char sequences "\\n" (backslash + n)
 * so that vis-network never sees real newlines in the title attribute.
 * The renderDetail parser then calls raw.replace(/\\n/g, "\n") to expand them.
 * We reproduce the same encoding: use the literal string "\\n" as the separator.
 *
 * Format (matching qb_graph.py):
 *   {id}\\n
 *   lesson: {lesson}  dok: {dok}  role: {role}\\n
 *   standards: {comma-joined standards}\\n
 *   skills: {comma-joined skill_tokens}\\n\\n
 *   {prompt truncated to 140 chars, newlines stripped}
 */
function buildTitle(item) {
  const lesson    = item.lesson    ?? "?";
  const dok       = item.dok       ?? 1;
  const role      = item.role      ?? "";
  const standards = Array.isArray(item.standards)    ? item.standards.join(", ")    : "";
  const skills    = Array.isArray(item.skill_tokens) ? item.skill_tokens.join(", ") : "";
  const prompt    = ((item.prompt ?? "").replace(/\n/g, " ")).slice(0, 140);
  // Replace non-ASCII with "?" to match Python's re.sub(r"[^\x20-\x7e]", "?", ...)
  const safePrompt = prompt.replace(/[^\x20-\x7e]/g, "?");

  return [
    item.id,
    `lesson: ${lesson}  dok: ${dok}  role: ${role}`,
    `standards: ${standards}`,
    `skills: ${skills}`,
    "",            // produces the blank line between header and prompt block
    safePrompt,
  ].join("\\n");
}

// ── Local cache (localStorage) ────────────────────────────────────────────────
// Strategy: render from cache instantly, then ask Supabase for items updated
// since our watermark and re-fetch the edge set (composite PK, no updated_at,
// rarely changes). If anything changed, update the cache and surface a
// "reload to see latest" banner — no live mutation of vis-network.

const CACHE_KEY = "dag_cache_v1";
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;  // full-resync floor

function loadCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    if (!Array.isArray(obj.items) || !Array.isArray(obj.edges) || !obj.fetched_at) return null;
    if (Date.now() - new Date(obj.fetched_at).getTime() > CACHE_TTL_MS) return null;
    return obj;
  } catch { return null; }
}

function saveCache(items, edges) {
  try {
    const maxUpdated = items.reduce(
      (acc, it) => (it.updated_at && it.updated_at > acc ? it.updated_at : acc),
      "1970-01-01T00:00:00Z",
    );
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      items, edges,
      max_updated_at: maxUpdated,
      fetched_at: new Date().toISOString(),
    }));
  } catch (e) {
    console.warn("dag cache save failed:", e.message);
  }
}

function edgeSetsEqual(a, b) {
  if (a.length !== b.length) return false;
  const key = e => `${e.from_id}|${e.to_id}|${e.kind}`;
  const setA = new Set(a.map(key));
  for (const e of b) if (!setA.has(key(e))) return false;
  return true;
}

function showReloadBanner(nItems, edgeChanged) {
  if (document.getElementById("dag-refresh-banner")) return;
  const b = document.createElement("div");
  b.id = "dag-refresh-banner";
  b.style.cssText =
    "position:fixed;top:12px;right:12px;background:#1a73e8;color:#fff;" +
    "padding:8px 14px;border-radius:6px;font-size:12px;cursor:pointer;" +
    "z-index:9999;box-shadow:0 2px 8px rgba(0,0,0,0.4);";
  const parts = [];
  if (nItems) parts.push(`${nItems} item${nItems === 1 ? "" : "s"} updated`);
  if (edgeChanged) parts.push("edges changed");
  b.textContent = `Graph changed (${parts.join(", ")}) — click to reload`;
  b.addEventListener("click", () => location.reload());
  document.body.appendChild(b);
}

async function refreshInBackground(cache) {
  try {
    const [newItems, freshEdges] = await Promise.all([
      api.listItemsUpdatedSince(cache.max_updated_at),
      api.listAllEdges(),
    ]);
    const edgeChanged = !edgeSetsEqual(freshEdges, cache.edges);
    if (newItems.length === 0 && !edgeChanged) return;
    const byId = new Map(cache.items.map(it => [it.id, it]));
    for (const it of newItems) byId.set(it.id, it);
    saveCache([...byId.values()], freshEdges);
    showReloadBanner(newItems.length, edgeChanged);
  } catch (e) {
    console.warn("dag delta refresh failed:", e.message);
  }
}

// ── Main ───────────────────────────────────────────────────────────────────────

async function init() {
  const loadingEl = document.getElementById("loading");
  const errorBanner = document.getElementById("error-banner");
  const detailEl = document.getElementById("detail");

  // Show loading
  if (loadingEl) loadingEl.style.display = "";

  let items, edges;
  const cache = loadCache();
  let renderedFromCache = false;

  if (cache) {
    items = cache.items;
    edges = cache.edges;
    renderedFromCache = true;
  } else {
    try {
      [items, edges] = await Promise.all([api.listAllItems(), api.listAllEdges()]);
    } catch (err) {
      // Hide loading, show error banner, bail.
      if (loadingEl) loadingEl.style.display = "none";
      if (errorBanner) {
        errorBanner.textContent = `Failed to load graph data from Supabase: ${err.message}`;
        errorBanner.style.display = "";
      }
      return;
    }
    saveCache(items, edges);
  }

  // Filter out deprecated / out-of-scope items before anything downstream:
  //   - APStats proof-of-concept lesson (wrong subject for this DAG)
  items = items.filter(it =>
    !(typeof it.lesson === "string" && it.lesson.toLowerCase().startsWith("apstats"))
  );
  const keep = new Set(items.map(it => it.id));
  edges = edges.filter(e => keep.has(e.from_id) && keep.has(e.to_id));

  // ── Build vis DataSets ─────────────────────────────────────────────────────

  const visNodes = new window.vis.DataSet(
    items.map(item => {
      const role  = item.role ?? "explore-practice";
      const dok   = item.dok  ?? 1;
      return {
        id:          item.id,
        label:       item.id.replace(/-savvas-/, "-").replace(/-lesson-/, "-").slice(0, 28),
        group:       item.lesson,
        color: {
          background: ROLE_COLORS[role] ?? DEFAULT_COLOR,
          border:     "#202124",
        },
        borderWidth: 1,
        size:        10 + 6 * Number(dok),
        title:       buildTitle(item),
      };
    })
  );

  const visEdges = new window.vis.DataSet(
    edges.map(edge => {
      const color = EDGE_COLORS[edge.kind] ?? "#5f6368";
      const entry = {
        from:  edge.from_id,
        to:    edge.to_id,
        color,
        kind: edge.kind,   // preserved so neighborsByNode doesn't color-reverse
        chosen: { edge: false, label: false },
      };
      if (edge.kind === "echoes") {
        entry.dashes = [2, 4];
      } else {
        entry.arrows = "to";
      }
      return entry;
    })
  );

  // ── vis-network init ──────────────────────────────────────────────────────

  const network = new window.vis.Network(
    document.getElementById("net"),
    { nodes: visNodes, edges: visEdges },
    {
      physics: {
        solver: "forceAtlas2Based",
        stabilization: { iterations: 300 },
      },
      interaction: {
        hover: true,
        tooltipDelay: 999999,  // disable native tooltip — we render our own detail panel
      },
      nodes: {
        shape: "dot",
        font: { color: "#e8eaed", size: 11 },
        // Disable vis-network's default "chosen" tint — it was recoloring
        // hovered/selected nodes blue and making the role palette unreadable.
        chosen: { node: false, label: false },
        scaling: { min: 14, max: 32 },
      },
      edges: {
        smooth: { type: "continuous" },
        arrows: { to: { scaleFactor: 0.5 } },
        chosen: { edge: false, label: false },
      },
      groups: {},
    }
  );

  // ── Cache titles + strip from node data ──────────────────────────────────
  // Strip title from vis nodes so vis-network never renders the raw hover
  // tooltip with literal "\n" characters (same workaround as qb_graph.py).
  const titleById = {};
  visNodes.get().forEach(n => { titleById[n.id] = n.title; });
  visNodes.update(visNodes.get().map(n => ({ id: n.id, title: undefined })));

  // ── Adjacency indexes ─────────────────────────────────────────────────────
  // neighborsByNode: id -> [{id, color, kind, direction}, ...]
  const neighborsByNode = {};
  visEdges.get().forEach(e => {
    const kind = e.kind ?? "link";
    (neighborsByNode[e.from] = neighborsByNode[e.from] || []).push(
      { id: e.to,   color: e.color, kind, direction: "out" }
    );
    (neighborsByNode[e.to] = neighborsByNode[e.to] || []).push(
      { id: e.from, color: e.color, kind, direction: "in"  }
    );
  });

  // siblingsByLesson: lesson -> [nodeId, ...]
  const siblingsByLesson = {};
  visNodes.get().forEach(n => {
    if (!n.group || n.group === "?") return;
    (siblingsByLesson[n.group] = siblingsByLesson[n.group] || []).push(n.id);
  });

  // nodeAttrs + bySkill + byStandard — parsed from title strings once at startup
  // (same approach as qb_graph.py template's parseAttrs + indexing pass).
  const nodeAttrs  = {};   // id -> {skills, standards, role, lesson, dok}
  const bySkill    = {};   // skill-token -> [nodeId, ...]
  const byStandard = {};   // standards code -> [nodeId, ...]

  function parseAttrs(nodeId) {
    const raw    = (titleById[nodeId] || "").replace(/\\n/g, "\n");
    const header = raw.split(/\n\n/)[0].split("\n").slice(1);
    const rows   = [];
    for (const line of header) {
      const pairs = line.split(/\s{2,}/);
      for (const pair of pairs) {
        const m = /^([^:]+):\s*(.+)$/.exec(pair.trim());
        if (m) rows.push([m[1].trim().toLowerCase(), m[2].trim()]);
      }
    }
    const get = k => (rows.find(r => r[0] === k) || [])[1] || "";
    return {
      skills:    get("skills").split(/,\s*/).filter(Boolean),
      standards: get("standards").split(/,\s*/).filter(Boolean),
      role:      get("role"),
      lesson:    get("lesson"),
      dok:       get("dok"),
    };
  }

  visNodes.get().forEach(n => {
    const a = parseAttrs(n.id);
    nodeAttrs[n.id] = a;
    a.skills.forEach(s    => (bySkill[s]    = bySkill[s]    || []).push(n.id));
    a.standards.forEach(s => (byStandard[s] = byStandard[s] || []).push(n.id));
  });

  // ── renderDetail ──────────────────────────────────────────────────────────

  function renderDetail(node) {
    if (!node) {
      detailEl.className = "empty";
      detailEl.innerHTML = "Click a node to see its details.";
      return;
    }

    // Titles embed literal "\\n" two-char sequences, not real newlines.
    const rawTitle = titleById[node.id] || node.title || "";
    const raw      = rawTitle.replace(/\\n/g, "\n").replace(/\r/g, "");
    const parts    = raw.split(/\n\n/);
    const header   = (parts[0] || "").split("\n");
    const prompt   = parts.slice(1).join("\n\n").trim();

    const id   = header[0] || node.id;
    const rows = [];
    for (const line of header.slice(1)) {
      const pairs = line.split(/\s{2,}/);
      for (const pair of pairs) {
        const m = /^([^:]+):\s*(.+)$/.exec(pair.trim());
        if (m) rows.push([m[1].trim().toLowerCase(), m[2].trim()]);
      }
    }
    const get      = k  => (rows.find(r => r[0] === k) || [])[1] || "";
    const dok      = get("dok");
    const role     = get("role");
    const lesson   = get("lesson");
    const standards = get("standards");
    const skills   = get("skills");

    // ── Edge buckets ────────────────────────────────────────────────────────
    const neighbors = neighborsByNode[node.id] || [];
    const buckets = {
      "prereq-in":     { label: "Prerequisites (incoming)", items: [] },
      "prereq-out":    { label: "Leads to (outgoing)",      items: [] },
      "rehearses-in":  { label: "Rehearsed by",             items: [] },
      "rehearses-out": { label: "Rehearses",                items: [] },
      "echoes-in":     { label: "Echoed by",                items: [] },
      "echoes-out":    { label: "Echoes",                   items: [] },
    };
    for (const n of neighbors) {
      const key = n.kind + "-" + n.direction;
      (buckets[key] ?? (buckets[key] = { label: n.kind + " (" + n.direction + ")", items: [] }))
        .items.push(n);
    }
    const neighborHtml = Object.entries(buckets)
      .filter(([, b]) => b.items.length > 0)
      .map(([, b]) =>
        '<div class="meta-row"><strong>' + escHtml(b.label) + ":</strong> " +
        b.items.map(n =>
          '<a class="neighbor" data-target="' + escHtml(n.id) +
          '" style="border-left-color:' + escHtml(n.color || "#888") + ';">' +
          escHtml(n.id) + "</a>"
        ).join("") +
        "</div>"
      ).join("");

    // Dedupe set: prevent later sections from re-showing already-listed nodes.
    const shown = new Set([node.id]);
    for (const n of neighbors) shown.add(n.id);

    // Chip renderer — caps at 18 with "+N more" tail.
    function chips(ids, borderColor) {
      const capped = ids.slice(0, 18);
      const tail   = ids.length > 18
        ? ' <span class="tag" style="background:#2a2d32">+' + (ids.length - 18) + " more</span>"
        : "";
      return capped.map(i =>
        '<a class="neighbor" data-target="' + escHtml(i) +
        '" style="border-left-color:' + borderColor + ';">' + escHtml(i) + "</a>"
      ).join("") + tail;
    }

    // ── Render header + core sections ───────────────────────────────────────
    detailEl.className = "";
    detailEl.innerHTML =
      "<h2>" + escHtml(id) + "</h2>" +
      '<div class="meta-row">' +
        (lesson ? '<span class="tag">lesson ' + escHtml(lesson) + "</span>" : "") +
        (role   ? '<span class="tag">' + escHtml(role) + "</span>" : "") +
        (dok    ? '<span class="dok dok-' + escHtml(dok) + '">DOK ' + escHtml(dok) + "</span>" : "") +
      "</div>" +
      (standards
        ? '<div class="meta-row"><strong>Standards:</strong> ' +
          standards.split(/,\s*/).map(s => '<span class="tag">' + escHtml(s) + "</span>").join("") +
          "</div>"
        : "") +
      (skills
        ? '<div class="meta-row"><strong>Skills:</strong> ' +
          skills.split(/,\s*/).map(s => '<span class="tag">' + escHtml(s) + "</span>").join("") +
          "</div>"
        : "") +
      (prompt
        ? '<div class="meta-row"><strong>Prompt:</strong><div class="prompt">' +
          escHtml(prompt) + "</div></div>"
        : "") +
      neighborHtml;

    const attrs = nodeAttrs[node.id] || { skills: [], standards: [], role: "" };

    // ── Assessment coverage (assessment-shell nodes only) ────────────────────
    // For each tested skill, show which non-assessment items rehearse it.
    // Skills with zero rehearsers are flagged as gaps.
    if (attrs.role === "assessment-shell" && attrs.skills.length) {
      const covRow = document.createElement("div");
      covRow.className = "meta-row";
      covRow.style.cssText = "border-top:1px dashed #555;padding-top:10px;margin-top:14px;";
      let html = '<strong style="color:#fbbc04;">Rehearsal coverage:</strong>';
      for (const skill of attrs.skills) {
        const rehearsers = (bySkill[skill] || [])
          .filter(i => i !== node.id)
          .filter(i => (nodeAttrs[i] || {}).role !== "assessment-shell");
        const label = escHtml(skill);
        if (rehearsers.length === 0) {
          html +=
            '<div style="margin-top:6px;"><span class="tag" style="background:#5c2a2a;color:#f6b6b6;">' +
            label + " — no rehearsal (GAP)</span></div>";
        } else {
          html +=
            '<div style="margin-top:6px;"><strong style="font-size:11px;color:#b8c0c8;">' +
            label + " (" + rehearsers.length + ")</strong><br>" +
            chips(rehearsers, "#1a73e8") + "</div>";
          rehearsers.forEach(i => shown.add(i));
        }
      }
      covRow.innerHTML = html;
      detailEl.appendChild(covRow);
    }

    // ── Other items in this lesson (sibling fallback) ────────────────────────
    const siblings = (siblingsByLesson[node.group] || []).filter(i => !shown.has(i));
    if (siblings.length) {
      const siblingRow = document.createElement("div");
      siblingRow.className = "meta-row";
      siblingRow.innerHTML =
        "<strong>Other items in lesson " + escHtml(node.group) + ":</strong> " +
        chips(siblings, "#666");
      detailEl.appendChild(siblingRow);
      siblings.slice(0, 18).forEach(i => shown.add(i));
    }

    // ── Cross-lesson: shares skill (green border) ────────────────────────────
    for (const skill of attrs.skills) {
      const others = (bySkill[skill] || []).filter(i => !shown.has(i));
      if (!others.length) continue;
      const row = document.createElement("div");
      row.className = "meta-row";
      row.innerHTML =
        '<strong>Shares skill <code style="color:#8ab4f8;">' + escHtml(skill) +
        "</code>:</strong> " + chips(others, "#34a853");
      detailEl.appendChild(row);
      others.slice(0, 18).forEach(i => shown.add(i));
    }

    // ── Cross-lesson: shares standard (purple border) ────────────────────────
    for (const std of attrs.standards) {
      const others = (byStandard[std] || []).filter(i => !shown.has(i));
      if (!others.length) continue;
      const row = document.createElement("div");
      row.className = "meta-row";
      row.innerHTML =
        '<strong>Shares standard <code style="color:#c084fc;">' + escHtml(std) +
        "</code>:</strong> " + chips(others, "#c084fc");
      detailEl.appendChild(row);
      others.slice(0, 18).forEach(i => shown.add(i));
    }

    // ── No-connections fallback ──────────────────────────────────────────────
    if (!neighborHtml && shown.size === 1) {
      const empty = document.createElement("div");
      empty.className = "meta-row";
      empty.style.cssText = "color:#7a828a;font-style:italic;";
      empty.textContent = "No connections.";
      detailEl.appendChild(empty);
    }

    // ── Neighbor click wiring ────────────────────────────────────────────────
    detailEl.querySelectorAll("a.neighbor").forEach(a => {
      a.addEventListener("click", () => {
        const target = a.dataset.target;
        const n = visNodes.get(target);
        if (n) { network.selectNodes([target]); renderDetail(n); }
      });
    });
  }

  // ── Network click handler ─────────────────────────────────────────────────
  network.on("click", params => {
    if (params.nodes.length === 0) { renderDetail(null); return; }
    renderDetail(visNodes.get(params.nodes[0]));
  });

  // ── Lesson focus: dropdown + color-swap ───────────────────────────────────
  // (opacity doesn't reliably render on vis-network's standalone build with
  // color objects — swap to a dim gray background + bright yellow ring on
  // the focused lesson instead.)
  const origColorById = {};
  visNodes.get().forEach(n => {
    origColorById[n.id] = {
      background:  (n.color && n.color.background) || DEFAULT_COLOR,
      border:      (n.color && n.color.border)     || "#202124",
      borderWidth: n.borderWidth || 1,
    };
  });

  const lessonSelect = document.getElementById("lesson-select");
  const lessons = [...new Set(visNodes.get().map(n => n.group).filter(g => g && g !== "?"))].sort();
  if (lessonSelect) {
    lessons.forEach(L => {
      const opt = document.createElement("option");
      opt.value = L; opt.textContent = L;
      lessonSelect.appendChild(opt);
    });
  }

  let focusBadge = null;
  function applyFocus(L) {
    if (!L) {
      visNodes.update(visNodes.get().map(n => {
        const orig = origColorById[n.id];
        return {
          id: n.id,
          color: { background: orig.background, border: orig.border },
          borderWidth: orig.borderWidth,
        };
      }));
      if (focusBadge) { focusBadge.remove(); focusBadge = null; }
      network.fit({ animation: { duration: 400 } });
      return;
    }
    const focus = visNodes.get({ filter: n => n.group === L });
    if (!focus.length) return;
    visNodes.update(visNodes.get().map(n => {
      const orig = origColorById[n.id];
      if (n.group === L) {
        return {
          id: n.id,
          color: { background: orig.background, border: "#fbbc04" },
          borderWidth: 4,
        };
      }
      return {
        id: n.id,
        color: { background: "#2a2d32", border: "#3a3d42" },
        borderWidth: 1,
      };
    }));
    network.fit({ nodes: focus.map(n => n.id), animation: { duration: 400 } });
    if (focusBadge) focusBadge.remove();
    focusBadge = document.createElement("span");
    focusBadge.id = "focus-badge";
    focusBadge.textContent = "Focused: lesson " + L + " (" + focus.length + " nodes)";
    document.getElementById("legend").appendChild(focusBadge);
  }

  if (lessonSelect) {
    lessonSelect.addEventListener("change", e => applyFocus(e.target.value));
  }

  const focusLesson = new URLSearchParams(location.search).get("lesson");
  if (focusLesson && lessons.includes(focusLesson)) {
    if (lessonSelect) lessonSelect.value = focusLesson;
    network.once("stabilizationIterationsDone", () => applyFocus(focusLesson));
  }

  // ── Hide loading, reset detail placeholder ────────────────────────────────
  if (loadingEl) loadingEl.style.display = "none";
  detailEl.className = "empty";
  detailEl.innerHTML = "Click a node to see its details.";

  // ── Background delta check (cache-hit path only) ──────────────────────────
  // Cold load already fetched fresh, so skip; cache-hit needs to verify that
  // nothing was updated under us and prompt the user to reload if so.
  if (renderedFromCache) refreshInBackground(cache);
}

init();
