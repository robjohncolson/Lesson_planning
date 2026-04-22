"""Generate Lesson 4-3 Period 2 materials — Klimsara-adapted, no Blooket.

Design: Multiply & divide rational expressions + the lesson's single-DOK-3 spine.
P2 is the conceptual core: students apply factoring and cancellation to multiply
and divide rational expressions, then tackle the Closure Argument task (#13)
which asks WHY rational expressions are closed under multiplication and division —
the pedagogical anchor of the whole lesson.

Phases (55 min base; Period F 65-min):
  0–  5   Do Now    : Practice #25 — bridge: simplify rational expressions from P1 [DOK 1]
  5– 17   Launch    : teacher models Example 3 (multiply/divide setup) [DOK 2]
 17– 50   Explore   : Try-It 3/4/5 + Practice #27/#29/#32 + ⭐ DOK-3 q13 (Closure) [DOK 2-3]
 50– 55   Share/Sum : DOK-3 pair presents closure argument + bridge to P3 [DOK 2]
 55– 58   Exit      : summary recap fill-in                              [DOK 1-2]
 (back)   Optional: Practice #40 (performance-task finance item) — fast-finisher stretch
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import qb
import packet_styles as ps
from packet_build import (
    TABLE_STYLE, new_packet_doc,
    set_cell, add_callout, bank_item_block, add_header_block,
)
DO_NOW_ID   = "4-3-savvas-q25"
EXPLORE_IDS = [
    "4-3-savvas-try-it-3-lesson-4-3",
    "4-3-savvas-q27",
    "4-3-savvas-try-it-4-lesson-4-3",
    "4-3-savvas-q29",
    "4-3-savvas-try-it-5-lesson-4-3",
    "4-3-savvas-q32",
    "4-3-savvas-q13",        # ⭐ DOK-3 spine — Closure Argument
]
DOK3_ID       = "4-3-savvas-q13"
REINFORCE_IDS = ["4-3-savvas-q40"]   # performance-task finance item stretch

_ALL_IDS = [DO_NOW_ID] + ["4-3-savvas-example-3-lesson-4-3"] + EXPLORE_IDS + REINFORCE_IDS
qb.get_for_packet(_ALL_IDS)

LESSON_LABEL = "Lesson 4-3 · Period 2"
LESSON_TITLE = "Multiply & Divide Rational Expressions + DOK-3 Closure"

OBJECTIVES = [
    ("Math Objective",
     "Multiply and divide rational expressions by factoring, canceling common "
     "factors, and rewriting division as multiplication by the reciprocal; track "
     "all domain restrictions through every step."),
    ("Language Objective",
     "Justify in writing whether a set is closed under an operation, using "
     "sentence frames that cite factoring and cancellation."),
    ("Essential Understanding",
     "Rational expressions behave like rational numbers: closed under "
     "multiplication and nonzero division, because factoring + cancellation "
     "always produces another rational expression."),
]

FRAMEWORK_HEADER = [
    ("Topic Goals",
     "Multiply and divide rational expressions; justify closure under these operations."),
    ("Essential Question",
     "Why are rational expressions closed under multiplication and division, "
     "and what must we track to prove it?"),
    ("Materials",
     "Student packet, pencil. Teacher models Example 3; DOK-3 Practice #13 is "
     "the capstone closure-argument task."),
]


def _header(doc, *, for_teacher=False):
    add_header_block(doc, lesson_title=LESSON_TITLE, lesson_label=LESSON_LABEL,
                     objectives=OBJECTIVES, framework_header=FRAMEWORK_HEADER,
                     for_teacher=for_teacher)


# ── Do Now ───────────────────────────────────────────────────────────────

def build_do_now(path):
    doc = new_packet_doc(top=0.6, bottom=0.6, left=0.75, right=0.75)
    ps.running_header_name_block(doc, label_right="BLOCK")
    ps.day_banner(doc, 2, "Do Now — " + LESSON_TITLE, subtitle=LESSON_LABEL)

    ps.framework_phase_header(
        doc,
        phase="Do Now",
        framework_tag="bridge from P1",
        dok="1",
        minutes=5,
        teacher_does=["Hand out at door.", "Circulate 3 min.",
                      "Cold-call 1 student: \"Factor the numerator and denominator. What cancels?\""],
        students_do=["Simplify the rational expression by factoring and canceling.",
                     "State any domain restrictions."],
        questions_to_ask=[
            "What do you factor first — numerator or denominator?",
            "What values of x must be excluded, and why?",
        ],
        adult_role="Solo teacher: circulate, time 5 min, pull sheets.",
    )

    q = qb.get_for_packet([DO_NOW_ID])[0]
    bank_item_block(doc, q, label="Do Now — Simplify this rational expression",
                    space_after_inches=2.0)

    add_callout(doc, "\U0001f3af  SENTENCE FRAME",
                ["“I factor the numerator as ___ and the denominator as ___. I cancel the common factor ___, leaving ___. The domain excludes x = ___ because that value makes the denominator zero.”"],
                color_hex="FFF2CC")

    doc.save(path)


# ── Student packet ───────────────────────────────────────────────────────

def build_student(path):
    doc = new_packet_doc(top=0.55, bottom=0.55, left=0.7, right=0.7)
    _header(doc, for_teacher=False)

    ps.teal_section(doc, "LAUNCH — Multiply & Divide Rational Expressions (teacher models Example 3)", [])
    add_callout(doc, "\U0001f4d8  MULTIPLY / DIVIDE RULES (keep printed on your page)",
                [
                    "MULTIPLY / DIVIDE RULES",
                    "1. Factor every numerator AND denominator completely.",
                    "2. For division, rewrite as multiplication by the RECIPROCAL of the divisor.",
                    "3. Cancel only common FACTORS across any numerator with any denominator.",
                    "4. State the domain: exclude every zero of every denominator that appeared in ANY step, including the reciprocal’s new denominator.",
                ],
                color_hex="D9EAD3")

    add_callout(doc, "⚠️  DIVISION IS MULTIPLICATION BY THE RECIPROCAL",
                [
                    "a/b ÷ c/d  =  a/b × d/c",
                    "The new denominator (c) must be added to your domain-restriction list even if it cancelled.",
                    "Never cancel across the ÷ sign — flip FIRST, then cancel.",
                ],
                color_hex="F4CCCC")
    doc.add_paragraph()

    ps.teal_section(doc, "EXPLORE — Think-Pair-Share (33 min)",
                    ["Work with a partner. Move in order. Practice #13 (Closure Argument) is the big one — plan ~12 min for it."])

    items = qb.get_for_packet(EXPLORE_IDS)
    labels = [
        "Try It 3 — Multiply rational expressions",
        "Practice #27 — Multiply with factoring",
        "Try It 4 — Divide rational expressions",
        "Practice #29 — Divide: rewrite as multiplication",
        "Try It 5 — Mixed multiply/divide",
        "Practice #32 — Multi-step multiply/divide",
        "Practice #13  ⭐ DOK-3 CLOSURE ARGUMENT",
    ]
    for label, q in zip(labels, items):
        bank_item_block(doc, q, label=label, space_after_inches=1.5)

    ps.teal_section(doc, "SHARE / SUMMARY (5 min)", [])
    ps.sentence_frame_box(doc, [
        "Pair share (Closure Argument): “I rewrite the division as multiplication by the reciprocal, giving ___. After factoring, I cancel the factor ___, leaving ___. The domain excludes x = ___ because those values make at least one denominator zero at some step.”",
        "Whole class: one pair reads the closure argument. Class signals thumbs up/sideways.",
    ])

    add_callout(doc, "\U0001f52d  BRIDGE TO P3",
                ["Next period we apply multiply/divide skills to complex rational expressions and assessment-critical items. Bring your domain-restriction list habit."],
                color_hex="FCE5CD")

    ps.summary_exit_box(doc, "EXIT TICKET — Summary Recap",
                        [
                            "To divide rational expressions I first ___.",
                            "I cancel common factors, not ___.",
                            "My domain restriction list must include zeros from ___.",
                            "One biggest thing I learned today: ________________________",
                        ])

    doc.add_page_break()
    ps.teal_section(doc, "OPTIONAL REINFORCEMENT (not collected)",
                    ["If you finish Explore early. #40 is a finance performance task that applies rational expressions to a real-world context."])
    reinforce = qb.get_for_packet(REINFORCE_IDS)
    for i, q in enumerate(reinforce, 1):
        bank_item_block(doc, q, label=f"Optional #{i}  (Savvas Practice, performance-task finance item)",
                        space_after_inches=1.8)

    doc.save(path)


# ── Teacher packet ───────────────────────────────────────────────────────

def build_teacher(path):
    doc = new_packet_doc(top=0.5, bottom=0.5, left=0.7, right=0.7)
    _header(doc, for_teacher=True)

    add_callout(doc, "\U0001f4cc  PRE-FLIGHT — P2 IS THE DOK-3 SPINE DAY",
                [
                    "Today’s conceptual core is Practice #13 (Closure Argument). Students must produce a written paragraph with at least ONE worked example showing a product AND one showing a quotient, concluding that the result in each case is itself rational. That argument IS the lesson’s deepest content.",
                    "Pace: Try-It 3 (4 min) → #27 (4 min) → Try-It 4 (4 min) → #29 (4 min) → Try-It 5 (3 min) → #32 (4 min) → #13 (12 min). ~35 min total Explore.",
                    "If running tight: cut Try-It 5 or #32. Never cut #13.",
                ],
                color_hex="FFD9E0")

    ps.framework_phase_header(
        doc,
        phase="Do Now",
        framework_tag="bridge from P1",
        dok="1",
        minutes=5,
        teacher_does=["Hand out at door.", "Circulate 3 min.",
                      "Cold-call 1 student for factoring and domain restriction."],
        students_do=["Simplify by factoring and canceling.",
                     "State domain restrictions."],
        questions_to_ask=[
            "What do you factor first?",
            "Is xy constant here? What values are excluded from the domain?",
        ],
        adult_role="Solo teacher: circulate silently. No hints.",
    )
    q = qb.get_for_packet([DO_NOW_ID])[0]
    bank_item_block(doc, q, label=f"Do Now ({q['id']})", space_after_inches=0.3)
    add_callout(doc, "✅  ANSWER KEY",
                [q.get("notes") or "(verify)"],
                color_hex="D9EAD3")

    ps.framework_phase_header(
        doc,
        phase="Launch",
        framework_tag="teacher models Example 3",
        dok="2",
        minutes=12,
        teacher_does=[
            "Project Example 3. Think aloud: factor every numerator and denominator before canceling.",
            "\"For division I flip the second fraction — the RECIPROCAL — before I do anything else.\"",
            "Flag the Multiply/Divide Rules card — print it in student minds.",
            "30-sec pause: \"What domain values did I exclude and why?\" (partner check)",
            "Do NOT solve Try-Its or Practice items — release at minute 17.",
        ],
        students_do=[
            "Watch Example 3 silently.",
            "During pause: state domain restrictions to partner.",
            "Copy Rules card into margin.",
            "Note the division-as-reciprocal step: this comes back in #13.",
        ],
        questions_to_ask=[
            "What must I do BEFORE canceling in a division problem?",
            "Why can’t I cancel terms (numerator + denominator) — only factors?",
            "If x = 2 makes ANY denominator zero at ANY step, is it excluded? (Yes, always.)",
        ],
        adult_role="Project. Think aloud. Release promptly at minute 17.",
    )
    example_items = qb.get_for_packet(["4-3-savvas-example-3-lesson-4-3"])
    add_callout(doc, "\U0001f3a4  TEACHER SCRIPT",
                [
                    "1. “Watch me multiply two rational expressions. I factor everything before I cancel.”",
                    "2. “Step 1: Factor every numerator and denominator completely.”",
                    "3. “Step 2: For division, rewrite as multiplication by the reciprocal NOW — before factoring or canceling.”",
                    "4. “Step 3: Cancel only common FACTORS across any numerator with any denominator.”",
                    "5. “Step 4: State the domain — list every x-value that makes any denominator zero, including the reciprocal’s new denominator.”",
                    "6. “Today’s DOK-3 task asks WHY rational expressions are always closed under these operations. You’ll write a paragraph with a worked example.”",
                    "7. Release to Explore.",
                ],
                color_hex="CFE2F3")

    ps.framework_phase_header(
        doc,
        phase="Explore",
        framework_tag="TPS + DOK-3 driver",
        dok="2-3",
        minutes=33,
        teacher_does=[
            "5 laps across 33 min.",
            "Lap 1 (4 min): Try-It 3 — multiply. Press pairs to factor before canceling.",
            "Lap 2 (4 min): #27 — multiply with factoring. Watch for premature canceling.",
            "Lap 3 (4 min): Try-It 4 — divide. Check that pairs flip FIRST.",
            "Lap 4 (4 min): #29 — divide. Confirm domain restriction includes reciprocal’s new denominator.",
            "Lap 5 (12 min): ⭐ #13 Closure Argument. Students write a paragraph with ONE product example AND one quotient example, concluding the result is rational.",
            "Do NOT give #13 answers. Pairs present argument to each other; one pair presents at Share.",
        ],
        students_do=[
            "6 items + #13 in order: Try-It 3 → #27 → Try-It 4 → #29 → Try-It 5 → #32 → #13.",
            "For #13: BEFORE writing, identify what ‘closed’ means and plan your two examples.",
            "Justify with sentence frame.",
        ],
        questions_to_ask=[
            "Did you factor completely before canceling?",
            "#27: what common factor appears in numerator and denominator?",
            "#29: what is the reciprocal of the divisor? What new domain restriction does it add?",
            "Try-It 5: both multiply and divide steps — which comes first?",
            "#13: what makes a set ‘closed’ under an operation? (The result is always in the same set.)",
            "#13: can you name a product of two rational expressions that is NOT rational? (No — that’s the argument.)",
        ],
        adult_role="Solo teacher: 5 laps. Press CLOSURE argument structure on #13.",
    )
    items = qb.get_for_packet(EXPLORE_IDS)
    labels = [
        "Try It 3", "Practice #27", "Try It 4", "Practice #29",
        "Try It 5", "Practice #32",
        "Practice #13 ⭐ DOK-3 CLOSURE ARGUMENT",
    ]
    for label, q in zip(labels, items):
        bank_item_block(doc, q, label=f"{label} ({q['id']})", space_after_inches=0.3)
        if "DOK-3" in label or "#13" in label:
            add_callout(doc, "⭐ DOK-3 CLOSURE ARGUMENT — Practice #13",
                        [
                            "Students should produce a paragraph with at least ONE worked example showing a product AND one showing a quotient, concluding that the result in each case is itself rational.",
                            "Key criteria: (1) cites factoring + cancellation by name, (2) shows domain restriction tracking, (3) explicitly concludes the result is a rational expression.",
                        ],
                        color_hex="FFD9E0")
        else:
            add_callout(doc, "✅  ANSWER / ANTICIPATED TALK",
                        [q.get("notes") or "(no answer key — verify before class)"],
                        color_hex="D9EAD3")

    ps.framework_phase_header(
        doc,
        phase="Share / Summary",
        framework_tag="academic conversation + P3 bridge",
        dok="2",
        minutes=5,
        teacher_does=[
            "Cold-call 1 pair to present their Closure Argument using sentence frame.",
            "Class signals thumbs. Write the closure definition on board.",
            "P3 bridge: \"Next period we apply these skills to more complex items — bring your domain-restriction list habit.\"",
        ],
        students_do=[
            "Presenting pair reads their paragraph and cites their two worked examples.",
            "Rest of class signals and writes takeaway in margin.",
        ],
        questions_to_ask=[
            "Summarize: what does it mean for rational expressions to be ‘closed’ under multiplication?",
            "Does division by zero break closure? How do domain restrictions handle that?",
        ],
        adult_role="Cold-call a pair that struggled on #13 — hold them accountable to the closure-argument structure.",
    )

    ps.framework_phase_header(
        doc,
        phase="Exit Ticket",
        framework_tag="summary recap (not graded)",
        dok="1-2",
        minutes=3,
        teacher_does=[
            "Collect at door.",
            "Scan stem 3 (domain restrictions). Plan P3 Do Now if many students miss the reciprocal’s denominator.",
        ],
        students_do=["4 sentence stems, honest."],
        questions_to_ask=[
            "Did students remember to include reciprocal’s denominator in domain restrictions?",
        ],
        adult_role="Collect. No grade.",
    )
    add_callout(doc, "\U0001f4cb  EXIT TICKET — Student Form",
                [
                    "To divide rational expressions I first ___.",
                    "I cancel common factors, not ___.",
                    "My domain restriction list must include zeros from ___.",
                    "One biggest thing I learned today: ________________________",
                ],
                color_hex="FFF2CC")

    doc.add_page_break()
    add_callout(doc, "\U0001f550  PERIOD A / PERIOD F — 65-MIN CLASS NOTES",
                [
                    "Both sections should have 65 min for P2. Use the extra 10 min on Explore #13 (Closure Argument) — the richer the written paragraph, the better the DOK-3 payoff.",
                    "If finished early: hand out Practice #40 (finance performance task) as fast-finisher.",
                ],
                color_hex="FFD9E0")

    add_callout(doc, "\U0001f9e9  MODIFICATIONS / SUPPORT FOR IEP STUDENTS",
                [
                    "• Provide the Multiply/Divide Rules card as a sticker/cut-out.",
                    "• For #13, provide a paragraph starter: “I will show that the product of two rational expressions is rational. Let P(x)/Q(x) and R(x)/S(x) be two rational expressions…”",
                    "• Accept verbal closure argument in lieu of written paragraph.",
                ],
                color_hex="E2F0D9")
    add_callout(doc, "\U0001f30d  SUPPORTS FOR ELL STUDENTS",
                [
                    "• Sentence frames on student page (don’t skip).",
                    "• Word cards: “reciprocal” = flip the fraction; “closed” = the result stays in the same type; “domain restriction” = values x cannot equal.",
                    "• “Closure Argument” = a written explanation showing WHY something is always true.",
                    "• Pair ELL students with English-dominant partners for TPS.",
                ],
                color_hex="DEEBF7")

    doc.save(path)


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_do_now("L43_P2_Do_Now.docx")
    build_student("L43_P2_Student_Packet.docx")
    build_teacher("L43_P2_Teacher_Packet.docx")
    print("Built L43_P2_Do_Now.docx, L43_P2_Student_Packet.docx, L43_P2_Teacher_Packet.docx")
    ps.emit_visuals_checklist(_ALL_IDS, "L43_P2_Visuals_Checklist.md",
                              title="L43 P2 — Visuals Checklist")
