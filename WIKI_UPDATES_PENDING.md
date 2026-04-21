# Wiki Updates Pending (Home Laptop)

The Obsidian wiki (`obsidian-wiki/wiki/concepts/`) lives only on the home laptop (not tracked in this repo). When next on home laptop, paste the following into the wiki to reflect the Klimsara-adapted pivot.

---

## 1. NEW FILE: `obsidian-wiki/wiki/concepts/Klimsara-Adapted Lesson Pattern.md`

```markdown
# Klimsara-Adapted Lesson Pattern

The default lesson structure for Algebra 2 Unit 4 onward. Named for Mr. Klimsara, whose packets modeled the shape; adapted to honor Lynn's DOK framework (Explore = 35–40 min student heavy lifting, not teacher modeling).

## Why the pivot (April 2026)

Original 8-day Lesson 3-5 burn rate was ~1.5 weeks per lesson. With 11 lessons remaining and ~7 teaching weeks until June 20, the original cadence was physically impossible. Klimsara's 3-period structure fits — but his version has the teacher modeling 4 Examples back-to-back, which collapses Lynn's Explore phase. This hybrid keeps the 3-period budget while restoring student-centered Explore.

## Three-period template (~55 min base)

| Period | Role | DOK arc | Typical Explore load |
|---|---|---|---|
| P1 | Conceptual introduction | 1 → 2 | Do Now (bridge) + 2 Examples modeled in Launch + 5–7 Practice/Try-It items in TPS |
| P2 | Applications + DOK-3 spine | 2 → 3 | Bridge + 1 Example modeled + 4 Practice + ⭐ DOK-3 driver |
| P3 | Mastery / assessment-critical | 2 | Bridge + 2 Examples paired in Launch + 5–6 Practice (assessment-aligned) |

## Per-period phase flow

| Phase | Time | What happens |
|---|---|---|
| Do Now | 5 | Savvas-sourced DOK-1 bridge from prior period. Cold-call 1 student at minute 4. |
| Launch | 10–12 | Teacher models ONE Example (P1/P2) or TWO paired Examples (P3). Think-aloud. Pause 1× for 30-sec partner check. DO NOT model Try-Its. |
| Explore | 33–38 | Think-Pair-Share through 4–7 bank items. Teacher does 4–5 laps of circulation. Students justify using sentence frames before writing. No answers given. |
| Share / Summary | 5 | Cold-call 1–2 pairs to present via sentence frame. Preview next period's bridge. |
| Exit Ticket | 2–3 | 3-stem summary recap (fill-in + "biggest thing learned" + "one thing I'm unsure about"). Collected at door. Not graded. |

## Hard rules baked into the pattern

- **Try-Its stay in-class as TPS.** Never moved to HW.
- **Single-DOK-3 per period**, not per lesson. P3 may be DOK-2 mastery without a spine.
- **Teacher models ONE Example per Launch** (or two paired closely). Students do the rest via TPS.
- **Back-of-packet HW is optional reinforcement only** (not assigned, not graded).
- **Framework phases never cut.** Even 45-min Wed F variant keeps Launch/Share/Exit; only Explore shrinks.

## Wednesday F 45-min variant

Period F on Wednesday is a 45-min short class. Standard adjustments:
- **Launch**: 10 min (cut 2 min).
- **Explore**: 25 min (cut 8 min). Drop the last 2 practice items; keep the DOK-3 driver if present.
- **Share**: 5 min (cut 2 min). One pair presents, not two.
- **Exit**: 3 min (unchanged).

## Tool correspondence

- **Packet files**: `L{NN}_P{N}_{Do_Now,Student_Packet,Teacher_Packet}.docx`.
- **Pacer**: one `L{NN}_Pacer.html` per lesson with three sub-tabs (P1/P2/P3). Tab switcher + countdown timer + inline scripts/answer keys/rules.
- **Slides**: one `build_L{NN}_slides.py` with `build_p1()`, `build_p2()`, `build_p3()` functions emitting separate decks.
- **Visuals checklist** auto-emitted per period via `emit_visuals_checklist()` hook in builder `__main__`.

## Related

- [[Single-DOK3 Lesson Spine]] — updated to reflect per-period scope
- [[Self-Contained Pacer Pattern]] — v3 tabbed variant
- [[Do Now A-B-C Framework]] — superseded by the unified Do Now above (no more A/B/C sub-phases now that Blooket is dropped)
```

---

## 2. UPDATE: `obsidian-wiki/wiki/concepts/Single-DOK3 Lesson Spine.md`

**Add this section near the top, after the pattern description:**

```markdown
## Scope clarification (2026-04-20 update)

**The single-DOK3 rule is PER PERIOD, not per lesson.** A 3-period Klimsara-adapted lesson may legitimately have:
- P1: no DOK-3 driver (foundation DOK-1/2 day)
- P2: one DOK-3 driver (Performance Task or Model With Math item)
- P3: no DOK-3 driver (DOK-2 mastery / assessment rehearsal)

The rule exists to keep students on ONE cognitively demanding task per period so they can go deep. Having DOK-3 drivers in back-to-back periods fragments attention.

### Example: Lesson 4-1

- P1 (inverse variation intro) — no DOK-3. 7 Explore items, all DOK 1-2.
- P2 (applications) — DOK-3 = Practice #26 (Ramón direct-vs-inverse).
- P3 (reciprocal + translations) — no DOK-3. Pure DOK-2 mastery for Topic 4 assessment prep.

### Example: Lesson 3-5 (legacy 8-day → 3-period close-out)

- P2 (Tue multiplicity) — no DOK-3.
- P3 (Wed modeling) — DOK-3 = Practice #27 (Storage Box).
- P4 (Thu) — external Topic 3 assessment (no class instruction).
```

---

## 3. UPDATE: `obsidian-wiki/wiki/concepts/Self-Contained Pacer Pattern.md`

**Add this section:**

```markdown
## V3 — Single-file, Multi-tab (2026-04-20)

Previous pacers were one HTML file per day (e.g., `Day_23_Pacer.html`, `Day_45_Pacer.html`). Klimsara-adapted lessons use ONE pacer per lesson with sub-tabs:

- `L35_Pacer.html` — tabs for P2 / P3 / P4 (Topic 3 assessment)
- `L41_Pacer.html` — tabs for P1 / P2 / P3

### Features

- **Tab switcher** in nav bar; click to change period.
- **Per-tab sticky timer** at top with Start/Stop buttons.
- **Phase chips** (clickable) below timer — switch to any phase. Completed phases strike through.
- **Active phase card** shows: DOK + minutes + framework-tag badges, bank items (⭐ for DOK-3 or assessment-critical), teacher script callout, rules callout, inline answer keys, bridge prompts, short-variant warnings.
- **Single HTML file**, no build step, opens directly in browser. Offline-capable.

### Design principles (unchanged from v2)

- Teacher runs the whole lesson from the pacer alone — printed teacher packet is for evaluators/archival.
- Every phase carries the framework metadata (DOK, time, phase label) to satisfy evaluator walkthroughs.
- No QR overlay on v3 (was v2 feature); teachers bookmark pacer URL instead.
```

---

---

## 4. NEW FILE: `obsidian-wiki/wiki/concepts/LaTeX Ingest Pipeline.md`

```markdown
# LaTeX Ingest Pipeline

The high-throughput alternative to screenshot-by-screenshot ingest. Added 2026-04-20 after burning 3 hours on Lesson 4-1's manual ingest (30+ screenshots, per-item transcription). Used for Lesson 4-3 and will be used for everything after.

## Pipeline

1. **User has a Savvas TE PDF + SE PDF for the target lesson.**
2. **User pastes the prompt template + PDFs into Gemini or ChatGPT.** Both work; GPT's structural output matches the parser more literally, but Gemini's prose is often richer. Try both if unsure.
3. **Output arrives as a single `.tex` file** using custom environments.
4. **Save to `source/<lesson>_savvas_{SE,TE}.tex`** in the repo.
5. **Run `python ingest_lesson_from_latex.py source/<lesson>_SE.tex source/<lesson>_TE.tex`.**
6. **Review the output files:** `skeletons/<lesson>_from_latex.json` + `questionbank/calibration/<lesson>.json`.
7. **Commit to registry:** `python qb_append.py skeletons/<lesson>_from_latex.json`.

## Gemini/GPT prompt template

Full prompt in `CLAUDE.md` → Toolchain section, or see git history commit `a4da1de`. Key bits:

- Wrap structural blocks in custom environments: `lesson-meta`, `item-analysis`, `model-discuss`, `example{N}`, `tryit{N}`, `practice{N}{DOK}`, `concept-box`, `concept-summary`, `te-addendum{anchor}{type}`.
- Use `\answer{...}`, `\placeholder{type}{desc}`, `\uncertain{best}{alts}` as helper commands.
- TE type shortnames: `PurposefulQuestions`, `ElicitEvidence`, `CommonError`, `HabitsOfMind`, `RtISupport`, `RtIExtend`, `ELLAddendum`, `LearnTogether`.
- Photos/maps that can't be TikZ'd → `\placeholder{photo}{description with any text labels}`.
- Flag any transcription uncertainty with `\uncertain{best_guess}{alternatives}` rather than silently guessing.

## What the parser handles

- Savvas item-analysis tabular (handles `\hline`, `\toprule`/`\bottomrule`, en-dash ranges `14--16`).
- Multi-file input (SE + TE concatenated).
- Gemini descriptive TE anchors (`{Explore & Reason}{Establish Math Goals}`) — kept as strings.
- GPT numeric TE anchors (`{1}{PurposefulQuestions}`) — standard path.
- Visual auto-detection: placeholder → photo/map, tikzpicture → graph, tabular → table.
- DOK override: if item-analysis table disagrees with inline `{N}{D}` arg, item-analysis wins (Gemini/GPT often default to DOK=1 when they don't have the table).

## Known limitations

- **Multiple-choice answer options don't populate `answers[]`** — if a practice item is MC, edit the JSON stub before `qb_append.py`.
- **Image placeholders still need manual staging** — photos/maps aren't renderable from TikZ, so the source image needs to be screenshotted + copied to `questionbank/images/` with a sane name + registry entry updated with the path.
- **Practice items #1-#10** in Savvas are concept-review (ESSENTIAL QUESTION restatement, vocabulary) and typically in the SE only, not TE. If TE-only ingest, those items are missed.

## Throughput

- Lesson 4-1 (manual screenshot ingest): ~3 hours, 47 items.
- Lesson 4-3 (LaTeX pipeline): ~15 minutes (Gemini + GPT round-trips + review), 70 items.
- Target: **one Unit per session** once prompt templates are dialed in.

## When to fall back to manual screenshots

- Topic assessments with heavy graphics (may be faster to screenshot directly).
- Half-lessons or supplementary handouts not covered by Savvas.
- Any item that fails transcription 2+ times (just screenshot it and hand-ingest).

## Related

- [[Klimsara-Adapted Lesson Pattern]] — what you do WITH the ingested bank.
- [[Single-DOK3 Lesson Spine]] — how to pick a DOK-3 driver from the ingested practice items.
```

---

---

## 4. NEW FILE: `obsidian-wiki/wiki/concepts/Assessment-Forward vs DOK-3-Forward Workflow.md`

```markdown
# Assessment-Forward vs DOK-3-Forward Workflow

Two distinct workflows for building a unit's lesson materials, picked based on the shape of the topic assessment.

## Assessment-Forward (default)

When the topic assessment is **8–11 discrete items** (like Topic 3 and Topic 4 LEHS), work BACKWARD:
1. List the assessment items.
2. For each item, identify the lesson + Example it tests.
3. Pick the lesson period that will rehearse each item most faithfully (the "assessment-critical period", usually P3).
4. Pick DOK-3 drivers that reinforce the assessment skills.
5. Toss lesson content that has no assessment alignment.

This is how Lesson 3-5 and Lesson 4-1 were built.

## DOK-3-Forward (pivot)

When the topic assessment is **a single Performance Assessment** (one scenario, 2–4 chained items — like Topic 5 Form B's underwater pyramid), work FORWARD:
1. Scan each lesson for its Savvas-declared DOK-3 items.
2. Pick the richest, most-teachable DOK-3 as the topic spine (usually from the "main" lesson of the unit).
3. Cross-reference the Performance Assessment's skills back to the DOK-3 candidates — some lessons' DOK-3s will NOT align (e.g., 5-5 function composition has zero Topic 5 assessment payoff).
4. Accept non-aligned DOK-3s on their own reasoning merits — they're still worth teaching, just not as the spine.
5. Build assessment-critical rehearsal periods around the DOK-3-forward picks.

This is how Lessons 5-1 / 5-4 / 5-5 were built. Topic 5's whole assessment chains off rational-exponent evaluation (5-4 Q#41 half-life), so 5-4 P2 carries the spine, 5-1 Q#50 cylinder is a supporting DOK-3 (Item 1A rehearsal), and 5-5 Q#32 music store is standalone.

## Detecting which workflow applies

Open the topic assessment source. If it's a numbered list of 8+ independent items → assessment-forward. If it's a single scenario with Part A / Part B / Item 2 / Item 3 → DOK-3-forward.

## Related

- [[Single-DOK3 Lesson Spine]] — per-period DOK-3 selection heuristic.
- [[Klimsara-Adapted Lesson Pattern]] — the 3-period container.
- [[Single-Period Compressed Klimsara]] — when a lesson only gets one period.
```

---

## 5. NEW FILE: `obsidian-wiki/wiki/concepts/Single-Period Compressed Klimsara.md`

```markdown
# Single-Period Compressed Klimsara

A one-period variant of the Klimsara-adapted lesson pattern, for "quick" lessons inside a topic that don't warrant a full 3-period treatment.

## When to use

- The lesson is declared "quick" in the unit roadmap (e.g., 5-1 and 5-5 were quick; 5-4 was the main focus).
- The lesson's content is narrower than the 3-period norm (one major skill, not a skill-ladder).
- End-of-year pacing pressure — you'd skip the lesson otherwise.

## Structure

Clone the P2 period builder (`build_L{NN}_P2_packets.py`) — not P1, because P2's template has the DOK-3 capstone machinery a quick lesson needs. Single-period lessons typically still carry their own DOK-3.

Departures from standard Klimsara:

- **Launch uses TWO examples, not one.** The Klimsara "model ONE" rule assumes 3 periods will cover all examples over time. One period has to front-load enough examples to make the Explore worth doing. Note this exception in a comment at the top of the builder.
- **Explore stays 33 min** — do not compress the student-work time. If you need to cut, drop Reinforce items, not Explore.
- **No P1/P2/P3 sub-tabs on the pacer.** Strip the tab switcher; render the single phase list directly. The `PACER` object has one key (`p1`) instead of three.
- **Slides: one `build_p1(path)` function only.** Delete `build_p2` and `build_p3` from the slides builder.

## Pacer HTML — tab-stripping

Three things to remove from the L43 pacer clone:
1. `<nav class="tabs">` and all tab buttons.
2. The `Object.keys(PACER).forEach(renderPanel)` loop.
3. The `tabBar` click listener.

Replace with a single `<div id="panel-p1">` declared with `display: block` (not `none`), and a single `renderPanel("p1")` boot call.

## Examples

- **Lesson 5-1** (nth roots + rational exponents + ⭐ Q#50 cylinder DOK-3) — supports Topic 5 Assessment Item 1A.
- **Lesson 5-5** (function operations + ⭐ Q#32 music-store DOK-3) — standalone, no assessment alignment.

Both lessons clone `build_L43_P2_packets.py` and `build_L43_slides.py` / `L43_Pacer.html`.

## Output naming

Still `L{NN}_P1_*.{docx,pptx,md}` and `L{NN}_Pacer.html`, even though "P1" is the only period. Preserves the naming convention across lesson types.

## Related

- [[Klimsara-Adapted Lesson Pattern]] — the full 3-period pattern this compresses.
- [[Assessment-Forward vs DOK-3-Forward Workflow]] — the decision context for when quick lessons are appropriate.
```

---

## 6. UPDATE: `obsidian-wiki/wiki/concepts/LaTeX to Registry Pipeline.md`

Add a new "Gotchas" section before "Known limitations":

```markdown
## Gotchas

- **Chat-UI chrome prefix.** LaTeX pasted from AI chat exports (Gemini, ChatGPT) often begins with UI artifacts like `code`, `Latex`, `download`, `content_copy`, `expand_less` before the `\documentclass`. Strip every line before `\documentclass` — the parser chokes on them. Standard pre-processing step for every fresh ingest.
- **Duplicate `-2`-suffixed IDs from SE+TE.** If both SE and TE files contain the same examples/try-its/practices (they usually do, with slightly different wording), the ingest creates `*-lesson-N-M` AND `*-lesson-N-M-2` versions in the registry. For packet-building, reference only the non-`-2` variants. The duplicates are harmless for `qb.get_for_packet` but inflate counts and should be cleaned up periodically.
- **Item-analysis table failures silently default to DOK 2.** If Gemini or GPT fails to transcribe the Savvas item-analysis table, every practice item defaults to DOK 2 at ingest. Verify Savvas-declared DOK-3 items made it into the registry with `dok=3` after ingest — if not, hand-patch with a small Python script (don't use `qb_append.py`, it's append-only).
- **SE + TE must be ingested as one concatenated file OR carefully merged.** If you run the pipeline twice (once per file), you'll produce two skeleton JSONs. Either concatenate the `.tex` files before ingest OR merge the skeletons before `qb_append.py`.
```

---

Once pasted on home laptop, delete this staging file (`WIKI_UPDATES_PENDING.md`) from the repo.
