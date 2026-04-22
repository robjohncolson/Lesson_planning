"""Generate Lesson 6-3 materials — single-period quick treatment.

Single-period lesson — condensed Klimsara. If 45-min Wed F variant, cut Explore
by dropping q53 and q54.

NOTE: This is a COMPRESSED lesson — one Example is modeled in Launch (Ex 3:
Evaluate Logarithms), but the DOK-3 spine q15 (Use y=3^x graph to estimate
log_3 50) drives the entire Explore block.

Design: Logarithms + DOK-3 spine q15 (exp↔log inverse via graph).
Students use the graph of y=3^x to estimate log_3 50 by reading the x-value
where y=50 is reached. Pair-share: why does this work? (Because log_3 50 = x
means 3^x = 50 — logs and exponentials are inverses.)

NOTE: PT#58 dropped as spine — not Form-B-aligned. q15 rehearses 3 of 8 Form B
items through the exp↔log inverse relationship. The continuous-growth modeling
of PT#58 will live in a future lesson if the class picks up 6-6+.

Phases (50 min base; 45-min Wed-F cuts q53 and q54):
  0–  7   Do Now    : 3 items — q14 (error analysis e^t=98), q16 (log_4 x < 0),
                      q3 (common vs natural log vocab) [DOK 1-2]
  7– 15   Launch    : teacher think-aloud Example 3 (Evaluate Logarithms) [DOK 1-2]
 15– 40   Explore   : ⭐ DOK-3 q15 (graph estimate, 10 min TPS + 5 min pair present)
                      + q52/q53/q54 + q17 (promote to core) [DOK 2-3]
 40– 45   Share/Sum : DOK-3 pair presents q15 reasoning + bridge to 6-4 [DOK 2]
 45– 50   Exit      : summary recap fill-in [DOK 1-2]
 (back)   Optional: q18 (ln 1000 ≠ 3 — fast finisher)
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import qb
import packet_styles as ps

from packet_build import (
    TABLE_STYLE, new_packet_doc,
    set_cell, add_callout, bank_item_block, add_header_block,
)
DO_NOW_IDS = [
    "6-3-savvas-q14",   # error analysis on e^t = 98
    "6-3-savvas-q16",   # log_4 x < 0 reasoning
    "6-3-savvas-q3",    # common vs natural log vocab
]
LAUNCH_IDS = [
    "6-3-savvas-example-3-lesson-6-3",  # Evaluate Logarithms: log_5 125, log_{1/4}16, log_3 0, log_2 2^8
]
EXPLORE_IDS = [
    "6-3-savvas-q15",   # ⭐ DOK-3 SPINE — Use y=3^x graph to estimate log_3 50
    "6-3-savvas-q52",
    "6-3-savvas-q53",
    "6-3-savvas-q54",
    "6-3-savvas-q17",   # critique log_3(1/27) = -3 (promoted to core; short DOK-3 proof)
]
DOK3_ID       = "6-3-savvas-q15"
REINFORCE_IDS = ["6-3-savvas-q18"]  # ln 1000 ≠ 3 — fast finisher only

_ALL_IDS = DO_NOW_IDS + LAUNCH_IDS + EXPLORE_IDS + REINFORCE_IDS
qb.get_for_packet(_ALL_IDS)

LESSON_LABEL = "Lesson 6-3 · Quick"
LESSON_TITLE = "Logarithms + DOK-3 Spine: q15 (exp↔log inverse via graph)"

OBJECTIVES = [
    ("Math Objective",
     "Evaluate logarithms using the definition log_b x = y ⇔ b^y = x, distinguish "
     "common (log) vs natural (ln) logs, and use the graph of y=3^x to estimate "
     "logarithmic values through the exp↔log inverse relationship."),
    ("Language Objective",
     "Explain the inverse relationship between exponential and logarithmic equations "
     "using 'undo' language."),
    ("Essential Understanding",
     "A logarithm answers the question: what exponent? -- logs undo exponentials. "
     "If I know how to graph y = 3^x, I can use that same picture to estimate log_3 50 "
     "because logarithms and exponentials are inverses."),
]

FRAMEWORK_HEADER = [
    ("Topic Goals",
     "Fluency evaluating logarithms; use the exp↔log inverse relationship graphically "
     "(Topic 6 Form B prep: q15 covers Q7, Q10, Q11; q17 covers Q13)."),
    ("Essential Question",
     "If I know how to graph y = 3^x, how can I use that same picture to estimate "
     "log_3 50 — and why does this work?"),
    ("Materials",
     "Student packet with printed y=3^x graph (x ∈ [−1, 4.5], y ∈ [0, 85], gridlines). "
     "Teacher copy adds dashed y=50 line and read-off annotation. "
     "[GRAPH PLACEHOLDER — needs_cleanup=YES, see Visuals Checklist]."),
]

RULES_CARD_LINES = [
    "LOG ⇔ EXP:   log_b x = y  ⇔  b^y = x",
    "COMMON LOG:  log x = log_10 x",
    "NATURAL LOG: ln x  = log_e x",
    "KEY:         ln(e^t) = t     (this solves continuous growth!)",
    "UNDEFINED:   log_b 0 and log_b (negative) — no real answer",
    "IDENTITY:    log_b (b^k) = k",
]

FORM_B_ALIGNMENT = [
    ("q15 (spine)", "Form B Q7 (inverse of exp), Q10 (inverse from graph), Q11 (log VA)"),
    ("q17",         "Form B Q13 (condense argument reasoning)"),
    ("q52",         "Form B Q9 (log↔exp definition)"),
    ("q53",         "Form B Q14 (solve exp with logs, Change of Base)"),
    ("q54",         "Form B Q9 + Q14 (multi-part log modeling)"),
]

BRIDGE_NOTE = (
    "PT#58 dropped as spine — not Form-B-aligned. q15 rehearses 3 of 8 Form B items "
    "through exp↔log inverse relationship. The continuous-growth modeling of PT#58 "
    "will live in a future lesson if the class picks up 6-6+."
)


def _header(doc, *, for_teacher=False):
    add_header_block(doc, lesson_title=LESSON_TITLE, lesson_label=LESSON_LABEL,
                     objectives=OBJECTIVES, framework_header=FRAMEWORK_HEADER,
                     for_teacher=for_teacher, day_number=1)


# ── Do Now ───────────────────────────────────────────────────────────────

def build_do_now(path):
    doc = new_packet_doc(top=0.6, bottom=0.6, left=0.75, right=0.75)
    ps.running_header_name_block(doc, label_right="BLOCK")
    ps.day_banner(doc, 1, "Do Now — " + LESSON_TITLE, subtitle=LESSON_LABEL)

    ps.framework_phase_header(
        doc,
        phase="Do Now",
        framework_tag="bridge to logarithms launch",
        dok="1-2",
        minutes=7,
        teacher_does=["Hand out at door.", "Circulate 3 min.",
                      "Cold-call 1 student on q14: What error did the student make? How do you undo an exponential with base e?"],
        students_do=["Analyze an error in solving e^t = 98.",
                     "Reason about when log_4 x is negative.",
                     "Sort common log vs. natural log vocabulary."],
        questions_to_ask=[
            "What is the difference between log x and ln x?",
            "If 4^y = x, what does y equal in log notation?",
        ],
        adult_role="Solo teacher: circulate, time 7 min, pull sheets.",
    )

    do_now_items = qb.get_for_packet(DO_NOW_IDS)
    do_now_labels = [
        "Do Now #1 — Error Analysis (e^t = 98)",
        "Do Now #2 — Reasoning (log_4 x < 0)",
        "Do Now #3 — Vocabulary (common vs. natural log)",
    ]
    for label, q in zip(do_now_labels, do_now_items):
        bank_item_block(doc, q, label=label, space_after_inches=1.5)

    add_callout(doc, "\U0001f3af  SENTENCE FRAME",
                ["log_b x = y means b raised to the power ___ equals ___. "
                 "So log_e 6.125 means e^___ = 6.125, which gives t = ___. "
                 "I use ln when the base is ___ because ___."],
                color_hex="FFF2CC")

    doc.save(path)


# ── Student packet ───────────────────────────────────────────────────────

def build_student(path):
    doc = new_packet_doc(top=0.55, bottom=0.55, left=0.7, right=0.7)
    _header(doc, for_teacher=False)

    ps.teal_section(doc, "LAUNCH — Evaluate Logarithms (teacher think-aloud Ex 3)", [])
    add_callout(doc, "\U0001f4d8  LOG ↔ EXP RULES (keep printed on your page)",
                RULES_CARD_LINES,
                color_hex="D9EAD3")

    doc.add_paragraph()

    ps.teal_section(doc, "EXPLORE — Think-Pair-Share (25 min)",
                    ["Work with a partner. Start with ⭐ Practice #15 (DOK-3 spine — 10 min TPS + "
                     "5 min pair presentations). Then move to #52, #53, #54, and #17."])

    add_callout(doc, "\U0001f4ca  GRAPH FOR q15 — y = 3^x  [GRAPH PLACEHOLDER]",
                ["[GRAPH PLACEHOLDER — print the y=3^x graph here: x ∈ [−1, 4.5], "
                 "y ∈ [0, 85], with gridlines. Source: a2_6-3_SE.pdf near end of practice "
                 "problems. See Visuals Checklist — needs_cleanup=YES.]"],
                color_hex="FFF2CC")

    items = qb.get_for_packet(EXPLORE_IDS)
    labels = [
        "Practice #15  ⭐ DOK-3 SPINE — Higher Order Thinking: Use y=3^x graph to estimate log_3 50",
        "Practice #52 — DOK-2 Application",
        "Practice #53 — DOK-2 Application  [45-min variant: skip]",
        "Practice #54 — DOK-2 Application  [45-min variant: skip]",
        "Practice #17 — DOK-3 Proof-style: critique log_3(1/27) = −3 (supports Form B Q13)",
    ]
    for label, q in zip(labels, items):
        bank_item_block(doc, q, label=label, space_after_inches=1.5)

    add_callout(doc, "\U0001f4dd  LOG ↔ EXP RULES — Reference Card (print this!)",
                RULES_CARD_LINES,
                color_hex="FFF2CC")

    ps.teal_section(doc, "SHARE / SUMMARY (5 min)", [])
    ps.sentence_frame_box(doc, [
        "Pair share (q15): On the graph of y = 3^x, I found log_3 50 by looking for "
        "y = ___ and reading the x-value. Since 3^3 = ___ and 3^4 = ___, the answer is "
        "between ___ and ___, closer to ___. This works because log_3 50 = x means "
        "3^x = ___, so the exponential and logarithm are ___.",
        "Whole class: one pair explains why reading the graph works. Class signals thumbs up/sideways.",
    ])

    add_callout(doc, "\U0001f52d  BRIDGE TO LESSON 6-4",
                ["Lesson 6-4 shifts to logarithmic FUNCTIONS — graphing y = log_b x, "
                 "identifying domain, range, and asymptotes. Today’s log ↔ exp definition "
                 "is the foundation."],
                color_hex="FCE5CD")

    ps.summary_exit_box(doc, "EXIT TICKET — Summary Recap",
                        [
                            "log_b x = y means ____.",
                            "log_2 32 = ____ because 2^? = 32.",
                            "To solve e^t = 6.125, take the ____ of both sides giving t = ____.",
                            "One biggest thing I learned today: ________________________",
                        ])

    doc.add_page_break()
    ps.teal_section(doc, "OPTIONAL REINFORCEMENT (not collected)",
                    ["If you finish Explore early. #18 asks you to evaluate whether ln 1000 = 3 "
                     "— use the log ↔ exp definition and the value of e to verify or refute."])
    reinforce = qb.get_for_packet(REINFORCE_IDS)
    for i, q in enumerate(reinforce, 1):
        bank_item_block(doc, q, label=f"Optional #{i}  (Savvas Practice #18 — ln 1000 ≠ 3?)",
                        space_after_inches=1.8)

    doc.save(path)


# ── Teacher packet ───────────────────────────────────────────────────────

def build_teacher(path):
    doc = new_packet_doc(top=0.5, bottom=0.5, left=0.7, right=0.7)
    _header(doc, for_teacher=True)

    add_callout(doc, "\U0001f4cc  PRE-FLIGHT — SINGLE-PERIOD COMPRESSED LESSON + DOK-3 SPINE q15",
                [
                    "This is a single-period quick treatment of Lesson 6-3. ONE example modeled in "
                    "Launch (Ex 3: Evaluate Logarithms). DOK-3 spine q15 drives Explore.",
                    "q15: Use the graph of y=3^x to estimate log_3 50. Students find y=50 on the "
                    "graph and read off the x-value. Since 3^3=27 and 3^4=81, answer is between 3 "
                    "and 4, closer to 3.5. Formally log_3 50 ≈ 3.56. Pair-share: why does this "
                    "work? (Because log_3 50 = x means 3^x = 50 — logs and exp are inverses.)",
                    "VISUAL REQUIRED: Student packet needs printed y=3^x graph (x ∈ [−1, 4.5], "
                    "y ∈ [0, 85], gridlines). Teacher copy: same graph + dashed y=50 line + "
                    "read-off annotation. See Visuals Checklist — needs_cleanup=YES.",
                    BRIDGE_NOTE,
                    "Pace: Do Now (7) → Launch (8) → Explore q15 (15 min) + q52 (4) + q53 (3) + "
                    "q54 (3) → Share (5) → Exit (5). ≈ 48 min. Buffer in q53+q54.",
                    "45-min Wed F variant: cut q53 + q54 from Explore. NEVER cut q15.",
                ],
                color_hex="FFD9E0")

    # ── Do Now ───────────────────────────────────────────────────────────
    ps.framework_phase_header(
        doc,
        phase="Do Now",
        framework_tag="bridge to logarithms launch",
        dok="1-2",
        minutes=7,
        teacher_does=["Hand out at door.", "Circulate 3 min.",
                      "Cold-call 1 student on q14 error analysis.",
                      "Pull sheets at 7 min."],
        students_do=["Error analysis on e^t = 98 (q14).",
                     "Reason about log_4 x < 0 (q16).",
                     "Sort vocab: common vs. natural log (q3)."],
        questions_to_ask=[
            "What is the student’s error in q14? What step undoes the exponential?",
            "For q16: what base-4 power gives a value less than 1?",
            "What’s the base for log x vs. ln x?",
        ],
        adult_role="Solo teacher: circulate silently. No hints on q14 — let pairs argue.",
    )
    do_now_items = qb.get_for_packet(DO_NOW_IDS)
    do_now_labels_te = [
        "Do Now #1 — Error Analysis (q14)",
        "Do Now #2 — Reasoning (q16)",
        "Do Now #3 — Vocabulary (q3)",
    ]
    for label, q in zip(do_now_labels_te, do_now_items):
        bank_item_block(doc, q, label=f"{label} ({q['id']})", space_after_inches=0.3)
        add_callout(doc, "✅  ANSWER KEY / ANTICIPATED TALK",
                    [q.get("notes") or "(verify before class)"],
                    color_hex="D9EAD3")

    # ── Launch ───────────────────────────────────────────────────────────
    ps.framework_phase_header(
        doc,
        phase="Launch",
        framework_tag="teacher think-aloud Example 3 (Evaluate Logarithms)",
        dok="1-2",
        minutes=8,
        teacher_does=[
            "Project Example 3. Think aloud: log_b x = y ⇔ b^y = x.",
            "Walk through log_5 125 = 3 (ask: 5^? = 125).",
            "Walk through log_{1/4} 16 = −2 (negative exponent — flag this!).",
            "Walk through log_3 0: Is there any power of 3 that gives 0? No -- undefined.",
            "Walk through log_2 2^8 = 8 using the identity log_b(b^k) = k.",
            "Flag Rules card — students mark it on student packet.",
            "30-sec pause: Turn to partner: rewrite log_4 64 using the definition.",
            "Do NOT solve Practice items — release at minute 15.",
        ],
        students_do=[
            "Watch Example 3 silently. Copy the log ↔ exp switch.",
            "Note: log_b 0 is undefined (no real answer).",
            "Mark the Rules card on their student packet.",
            "During pause: rewrite log_4 64 with partner.",
        ],
        questions_to_ask=[
            "log_5 125 = ? — what power does 5 need?",
            "log_{1/4} 16 = ? — why is the answer negative?",
            "Why is log_3 0 undefined?",
            "Use the identity: log_2 2^8 = ?",
        ],
        adult_role="Project Example 3 only. Release promptly at minute 15.",
    )
    example_items = qb.get_for_packet(LAUNCH_IDS)
    example_items = qb.get_for_packet(LAUNCH_IDS)
    add_callout(doc, "🎤  TEACHER SCRIPT",
                [
                    "1. 'A logarithm asks: what exponent does b need to produce x?'",
                    "2. 'log_5 125: what power of 5 is 125? 5^1=5, 5^2=25, 5^3=125. Answer: 3.'",
                    "3. 'log_{1/4} 16: tricky — (1/4)^? = 16. (1/4)^(-2) = 4^2 = 16. Answer: -2.'",
                    "4. 'log_3 0: no power of 3 ever reaches 0 — UNDEFINED.'",
                    "5. 'log_2 2^8: identity log_b(b^k) = k. Answer: 8. No work needed.'",
                    "6. 'For today's DOK-3 spine: on the graph of y=3^x, we can read log_3 50 "
                    "directly — because exp and log are inverses, the x-value IS the log.'",
                    "7. Release to Explore.",
                ],
                color_hex="CFE2F3")

    # ── Explore ──────────────────────────────────────────────────────────
    ps.framework_phase_header(
        doc,
        phase="Explore",
        framework_tag="TPS + DOK-3 driver",
        dok="2-3",
        minutes=25,
        teacher_does=[
            "4 laps across 25 min.",
            "Lap 1 (10 min): ⭐ q15 DOK-3 spine. Press pairs: 'Where on the graph is y=50? "
            "What x-value does that correspond to?' Do NOT give the answer.",
            "After 10 min: pair presentations (5 min). One pair explains: 'Why does reading "
            "the x-value on the exp graph give you the log?'",
            "Lap 2 (4 min): q52. Press: 'Which log rule applies here?'",
            "Lap 3 (3 min): q53. Press conversion between log and exp forms.",
            "Lap 4 (3 min): q54. Press asymptote and domain reasoning.",
            "Then q17: press 'Is log_3(1/27) = -3 correct? Use the definition to check.'",
            "45-min variant: skip q53 and q54. Budget extra time on q15.",
        ],
        students_do=[
            "5 items in order: q15 → q52 → q53 → q54 → q17.",
            "For q15: use the printed y=3^x graph. Find y=50, read the x-value.",
            "Pair-share for q15: explain WHY reading the x-value gives log_3 50.",
            "q17: verify or refute log_3(1/27) = -3 using the definition.",
            "Justify each step using sentence frame.",
        ],
        questions_to_ask=[
            "q15: on the graph, where is y=50? Between which two integer x-values?",
            "q15: why does the x-value where the graph hits y=50 equal log_3 50?",
            "q15: 3^3 = 27, 3^4 = 81 — so log_3 50 is between ___ and ___?",
            "q17: what does log_3(1/27) = y mean in exponential form?",
            "q52: does the log change or the argument?",
            "q53: can you rewrite in exponential form first?",
            "q54: what is the domain of log_b x? What is the asymptote?",
        ],
        adult_role="Solo teacher: 4 laps. On q15, press the 'why does this work?' "
                   "reasoning — that's the Form B Q10/Q11 assessment-critical move.",
    )
    items = qb.get_for_packet(EXPLORE_IDS)
    labels_te = [
        "Practice #15 ⭐ DOK-3 SPINE",
        "Practice #52",
        "Practice #53",
        "Practice #54",
        "Practice #17 (promoted to core)",
    ]
    for label, q in zip(labels_te, items):
        bank_item_block(doc, q, label=f"{label} ({q['id']})", space_after_inches=0.3)
        if "DOK-3" in label or "#15" in label:
            add_callout(doc, "⭐ DOK-3 SPINE — Practice #15 (exp↔log inverse via graph)",
                        [
                            "Prompt: Use the graph of y=3^x to estimate the value of log_3 50. "
                            "Explain your reasoning.",
                            "GRAPH: Student packet has y=3^x graph (x ∈ [-1, 4.5], y ∈ [0, 85]). "
                            "Teacher copy: same graph + dashed y=50 line + read-off annotation. "
                            "[GRAPH PLACEHOLDER — needs_cleanup=YES]",
                            "Expected reasoning: Find y=50 on graph, read x-value. "
                            "3^3=27, 3^4=81 → answer between 3 and 4, closer to 3.5. "
                            "Formally log_3 50 ≈ 3.56.",
                            "Pair-share: why does this work? Because log_3 50 = x means "
                            "3^x = 50 — the x-value where the exp graph hits y=50 IS the log.",
                            "Form B alignment: Q7 (inverse of exp), Q10 (inverse from graph), "
                            "Q11 (log VA).",
                        ],
                        color_hex="FFD9E0")
        else:
            add_callout(doc, "✅  ANSWER / ANTICIPATED TALK",
                        [q.get("notes") or "(no answer key — verify before class)"],
                        color_hex="D9EAD3")

    # ── Assessment alignment ──────────────────────────────────────────────
    add_callout(doc, "\U0001f9e9  FORM B ASSESSMENT ALIGNMENT",
                [f"  • {qid} → {mapping}" for qid, mapping in FORM_B_ALIGNMENT],
                color_hex="E8F0FE")

    # ── Share / Summary ───────────────────────────────────────────────────
    ps.framework_phase_header(
        doc,
        phase="Share / Summary",
        framework_tag="academic conversation + 6-4 bridge",
        dok="2",
        minutes=5,
        teacher_does=[
            "Cold-call 1 pair to present q15 reasoning using sentence frame.",
            "Class signals thumbs. Write on board: log_3 50 = x means 3^x = 50.",
            "6-4 bridge: 'Next lesson: logarithmic FUNCTIONS — graphing y = log_b x. "
            "Today's log ↔ exp definition is the foundation.'",
        ],
        students_do=[
            "Presenting pair explains: 'I found y=50 on the graph and read x ≈ 3.56. "
            "This works because log_3 50 = x means 3^x = 50.'",
            "Rest of class signals and writes takeaway in margin.",
        ],
        questions_to_ask=[
            "Summarize: how does the graph of y=3^x let you find log_3 50?",
            "Why is it that reading x gives you the log? What is the relationship?",
        ],
        adult_role="Cold-call a pair that got the estimation — hold them "
                   "accountable to naming the exp↔log inverse relationship explicitly.",
    )

    # ── Exit Ticket ───────────────────────────────────────────────────────
    ps.framework_phase_header(
        doc,
        phase="Exit Ticket",
        framework_tag="summary recap (not graded)",
        dok="1-2",
        minutes=5,
        teacher_does=[
            "Collect at door.",
            "Scan blank 3 (e^t = 6.125 → ln). Plan re-teach if many students "
            "write ‘log’ instead of ‘ln’ or leave the base blank.",
        ],
        students_do=["4 sentence stems, honest."],
        questions_to_ask=[
            "Did students correctly state log_b x = y means b^y = x?",
            "Did students get log_2 32 = 5 (since 2^5 = 32)?",
            "Did students write ln (not log) for base e?",
        ],
        adult_role="Collect. No grade.",
    )
    add_callout(doc, "\U0001f4cb  EXIT TICKET — Student Form",
                [
                    "log_b x = y means ____.",
                    "log_2 32 = ____ because 2^? = 32.",
                    "To solve e^t = 6.125, take the ____ of both sides giving t = ____.",
                    "One biggest thing I learned today: ________________________",
                ],
                color_hex="FFF2CC")

    doc.add_page_break()
    add_callout(doc, "🕐  PERIOD A / PERIOD F — 50-MIN CLASS NOTES",
                [
                    "Base lesson is 50 min. If 65 min: use extra 15 min on Explore q15 "
                    "(richer pair-share on why exp↔log inversion works) and q53/q54.",
                    "45-min Wed F variant: cut q53 + q54 from Explore. NEVER cut q15.",
                    "If finished early: hand out Practice #18 (ln 1000 ≠ 3 — fast finisher).",
                ],
                color_hex="FFD9E0")

    add_callout(doc, "🧩  MODIFICATIONS / SUPPORT FOR IEP STUDENTS",
                [
                    "• Provide the Log ↔ Exp Rules card as a sticker/cut-out.",
                    "• For q15, pre-label the y-axis at y=27, y=50, y=81 so students "
                    "can locate the target values without visual confusion.",
                    "• Accept 'between 3 and 4, closer to 3.5' as full credit for the estimate.",
                ],
                color_hex="E2F0D9")
    add_callout(doc, "🌍  SUPPORTS FOR ELL STUDENTS",
                [
                    "• Sentence frames on student page (don't skip).",
                    "• Word cards: 'logarithm' = the exponent; 'inverse' = undoes; "
                    "'estimate' = approximate value, not exact.",
                    "• 'UNDEFINED' = no real number answer (not zero).",
                    "• Pair ELL students with English-dominant partners for TPS.",
                ],
                color_hex="DEEBF7")

    doc.save(path)


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_do_now("L63_P1_Do_Now.docx")
    build_student("L63_P1_Student_Packet.docx")
    build_teacher("L63_P1_Teacher_Packet.docx")
    print("Built L63_P1_Do_Now.docx, L63_P1_Student_Packet.docx, L63_P1_Teacher_Packet.docx")
    ps.emit_visuals_checklist(_ALL_IDS, "L63_P1_Visuals_Checklist.md",
                              title="L63 P1 — Visuals Checklist")
