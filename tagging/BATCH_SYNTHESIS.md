# Batch tagging synthesis — all 11 operational spines

Tagged lesson-by-lesson: 3-5 (P2 + P3), 4-1 (full 3-period), 4-3 (full), 4-4, 4-5, 5-1 (pilot), 5-4 (full), 5-5, 6-3, 6-4, 6-5 (pilot). Total ≈125 items carrying v2 fields. Eleven pilot JSONLs in `tagging/`.

## The year, as a DAG (before we build it visually)

### DOK-3 flavor distribution

The four archetypes that surfaced from tagging, with exemplars:

| Flavor | Lesson exemplars |
|---|---|
| **Derive-from-constraint** (extract a hidden variable by modeling a physical/geometric situation) | 3-5-q27 (Storage Box), 4-5-q33 (Chemist mixture), 5-1-q50 (Cylinder Capstone), 6-4-q28 (Revenue inverse) |
| **Prove-by-properties** (establish a general fact by unpacking definitions) | 4-3-q13 (rational closure), 6-5-q13 (Power Property proof) |
| **Model-then-extract** (given a model, solve for a specific input) | 3-5-q30 (Venetta profit), 5-4-q41 (soft-drink half-life), 6-3-q52 (continuous compound), 6-5-q40 Part C (Richter generalization) |
| **Read-structure-from-representation** (graphical / multi-rep reasoning) | 4-1-q26 (TBD whether graph-centric), 6-3-q15 (estimate log from graph) |

**Coverage observations:**
- Derive-from-constraint dominates — 4 lessons carry it. That's good (it's the archetype that feels most like "real math").
- Prove-by-properties shows up only twice, both late in the year (4-3 and 6-5). Students meet their first proof-flavor DOK-3 in February-ish. That's late; a Unit 3 proof-flavor driver would help.
- Read-structure-from-representation is the thinnest flavor (confidently only 1 exemplar, 6-3-q15). If Topic 6 assessment rewards reading graphs, students may enter cold.

**Cohesion fix candidate #1:** identify one existing Unit 3 item that could be re-cast as prove-by-properties — or draft a new DOK-3 item for 3-5 that proves a polynomial theorem rather than models a box.

### Cross-unit echo chains (the cohesion signal)

The DAG's load-bearing edges are the `echoes` — they cross unit boundaries. In the corpus:

1. **Extract-hidden-dimension chain** — 3-5-q27 (Storage Box) → 5-1-q50 (Cylinder) → 6-4-q28 (Revenue). Three units, three representations (polynomial → rational-exponent → exponential inverse), same archetype. **This is the year's strongest through-line.**

2. **Model-then-extract chain** — 3-5-q30 (Venetta profit polynomial) → 5-4-q41 (half-life exponential) → 6-3-q52/6-5-q40 (Richter & compound interest). Four representations of "given the model, find the specific t."

3. **Apply-physical-formula chain** — 4-1-q17 (wavelength-frequency) → 4-1-q23 (Boyle) → 6-3-q54 (Richter) → 6-4-q33 (telescope). Consistent "here's a physics formula, plug in, report with units."

4. **Extraneous-check chain** — 4-5-q10 (rational extraneous error) → 5-4-q4 (radical extraneous error). Same logical structure (inverse op introduces false solutions) across two lesson types. Could extend to one more lesson's exit-ticket style.

5. **Rate-reciprocal-modeling chain (intra-Unit 4)** — 4-1-q26 (Ramón) → 4-4-q26 (Ahmed bike) → 4-5-q25 (Kenji+Oscar puzzle). Three practice items in three consecutive lessons use the same structural move. **This is the Unit 4 identity.**

6. **Proof-by-definition chain** — 4-3-q13 (rational closure) → 6-5-q13 (Power Property). Two items, same algebraic-proof flavor.

**Cohesion fix candidate #2:** print a one-page "Year at a Glance" that lists these six chains by name — when teacher plants the Venetta prompt in April, they can say "remember Storage Box? Same move, different machine." Students feel the year cohere.

### Weak or missing signals

- **Unit 6 has no intra-unit chain comparable to Unit 4's rate-reciprocal.** Logs sit as isolated items within each lesson. May be why logs feel fragmented.
- **No current item tags `decide-application-order` outside 5-5-q32.** If this is an important skill (it shows up on standardized tests), it needs a seed earlier and a callback later.
- **`read-graph-values`** and `read-given-formula` are common but low-status — they're implicit in every applied item and therefore unnamed. If tagging had started there, we'd have found that roughly half of Unit 4/6 practice depends on these without ever naming them.

## Schema: final state after batch

Fields `qb_append.py` now accepts (patched this session):
- `role`: enum of 11 positional labels
- `standards`, `prereq_ids`, `rehearses`, `echoes`, `skill_tokens`: all list[str]

Assessment shells live in `questionbank/assessment_shells.jsonl` (separate file, 11 rows). DAG tool must union the two files.

## What to build next

1. **`qb_graph.py`** — ~80 lines. Reads both JSONLs. Emits:
   - `graph.html` (Pyvis) — nodes = items, edges = prereq (black) + rehearses (blue) + echoes (red). Color by `role`, size by DOK.
   - `coverage_report.md` — standards × lesson matrix, DOK-3 flavor × lesson matrix, orphan items.
   - `chains.md` — auto-walks `echoes` transitively and prints the six chains above.

2. **Merge tags into `registry.jsonl`.** `qb_append.py` already accepts the fields, but the tagged items right now live in separate pilot files. A 30-line merge script (`merge_tags.py`) reads `tagging/*_pilot.jsonl` and patches matching IDs in `registry.jsonl`.

3. **The other 900 items.** You flagged wanting these tagged. Three sensible tiers:
   - **Tier 1 (~120 coverage-fill items):** every Savvas Example/Try-It not in a builder + every Practice item tagged DOK≥2. Gets standards coverage honest. 4 hrs.
   - **Tier 2 (~200 DOK-1 practice, the flashcard pool):** regex-auto-tag `skill_tokens` from prompt text, leave other fields empty. The DAG treats them as leaves. 30 min scripted.
   - **Tier 3 (~480 Blooket pool + duplicates):** dedupe duplicates first (especially the `-2`-suffix Example/Try-It re-ingests). Then Tier-2 treatment. Likely 2 hrs of dedup + 30 min scripted.

Total for "everything tagged" would be ≈7–8 hrs of which only Tier 1 requires judgment. Tiers 2 and 3 are mechanical.

## The insight that justifies the whole exercise

Before tagging: I had a mental list of "lessons to teach." After tagging: I have a **structured map of what students can do across the year, where those skills first appear, where they're reinforced, where they're tested, and which ones carry conceptual weight across unit boundaries.**

The tagging is the dry-run. The dry-run produced the map. The map reveals:
- one missing proof-flavor seed in Unit 3
- one overloaded intra-Unit-4 chain (rate-reciprocal might be too heavy)
- one cross-unit chain that *is* the year's spine and could be explicitly named to students
- one flavor (read-from-representation) that's nearly absent

None of that was visible from "read the packets." All of it is visible from 125 tagged rows.
