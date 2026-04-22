"""Generate Lesson 5-4 Period 1 materials — Klimsara-adapted, no Blooket.

Design: Introduce solving radical equations (isolate radical, raise to power,
check for extraneous solutions). Period 1 lays the conceptual foundation —
isolate, raise, check. Assessment items for 5-4 come from later periods;
P1 is foundation, not assessment-critical.

Phases (55 min base; Period F 65-min on Fri; Period A 65-min on Mon):
  0–  5   Do Now    : 5-4 Model & Discuss starter — notice & wonder       [DOK 2]
  5– 17   Launch    : teacher models Example 1 (isolate & raise)          [DOK 1-2]
                     + Example 3 (extraneous solution)
 17– 50   Explore   : Try-It 1 + Try-It 3 + Practice #22/#8/#15/#4 TPS   [DOK 1-2]
 50– 55   Share/Sum : sentence-frame consolidation on extraneous solutions [DOK 2]
 55– 58   Exit      : summary recap fill-in                               [DOK 1-2]
 (back)   Optional Reinforcement: Practice #21
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import qb
import packet_styles as ps

from packet_build import (
    TABLE_STYLE, new_packet_doc,
    set_cell, add_callout, bank_item_block, add_header_block,
)
DO_NOW_ID      = "5-4-savvas-model-discuss-lesson-5-4-launch"
# Explore sequence: Try-It 1 -> Try-It 3 -> #22 -> #8 -> #15 -> #4.
EXPLORE_IDS = [
    "5-4-savvas-try-it-1-lesson-5-4",
    "5-4-savvas-try-it-3-lesson-5-4",
    "5-4-savvas-q22",
    "5-4-savvas-q8",
    "5-4-savvas-q15",
    "5-4-savvas-q4",
]
REINFORCE_IDS  = ["5-4-savvas-q21"]

_ALL_IDS = [DO_NOW_ID] + EXPLORE_IDS + REINFORCE_IDS
qb.get_for_packet(_ALL_IDS)

LESSON_LABEL = "Lesson 5-4 · Period 1"
LESSON_TITLE = "Solving Radical Equations — Foundation"

OBJECTIVES = [
    ("Math Objective",
     "Solve radical equations by isolating the radical and raising both sides "
     "to the appropriate power; identify and reject extraneous solutions."),
    ("Language Objective",
     "Explain in writing, using sentence frames, why squaring both sides can "
     "introduce extraneous solutions and how to check."),
    ("Essential Understanding",
     "Squaring both sides is NOT a reversible operation — it can create "
     "solutions that don't satisfy the original equation. Every candidate "
     "must be checked."),
]

FRAMEWORK_HEADER = [
    ("Topic Goals",
     "Solve single-radical equations; detect extraneous solutions."),
    ("Essential Question",
     "Why does squaring both sides sometimes produce solutions that don't "
     "work, and how do we catch them?"),
    ("Materials",
     "Student packet, pencil. Teacher models Example 1, then gradual-release "
     "into Example 3 (extraneous)."),
]


def _header(doc, *, for_teacher=False):
    add_header_block(doc, lesson_title=LESSON_TITLE, lesson_label=LESSON_LABEL,
                     objectives=OBJECTIVES, framework_header=FRAMEWORK_HEADER,
                     for_teacher=for_teacher, day_number=1)


# ── Do Now ─────────────────────────────────────────────────────────────────────────

def build_do_now(path):
    doc = new_packet_doc(top=0.6, bottom=0.6, left=0.75, right=0.75)
    ps.running_header_name_block(doc, label_right="BLOCK")
    ps.day_banner(doc, 1, "Do Now — " + LESSON_TITLE, subtitle=LESSON_LABEL)

    ps.framework_phase_header(
        doc,
        phase="Do Now",
        framework_tag="notice & wonder",
        dok="2",
        minutes=5,
        teacher_does=["Project the starter on screen or sketch on board.",
                      "Don't answer questions — this is exploration.",
                      "Collect sheets at 5 min sharp."],
        students_do=["Look at the equation. Notice what makes it different from equations you've solved before.",
                     "Write 1 thing you NOTICE and 1 thing you WONDER.",
                     "Bonus: write one sentence about what you would do first to solve it."],
        questions_to_ask=[
            "What makes this equation different from a linear or quadratic equation?",
            "What operation could undo the square root?",
            "Can squaring both sides ever cause a problem?",
        ],
        adult_role="Solo teacher: circulate silently. No hints. Students must struggle productively for a moment.",
    )

    add_callout(doc, "\U0001f534  STARTER — A Radical Equation",
                [
                    "Starter: Look at the equation below. What makes it different from equations you have solved before? What would you do first?",
                    "",
                    "A) Notice: Write something you notice about this equation.",
                    "",
                    "B) Wonder: Write something you wonder about how to solve it.",
                    "",
                    "C) Sentence: What would you do first to start solving? Why?",
                ],
                color_hex="FFF2CC")

    doc.save(path)


# ── Student packet ───────────────────────────────────────────────────────────────────────────────

def build_student(path):
    doc = new_packet_doc(top=0.55, bottom=0.55, left=0.7, right=0.7)
    _header(doc, for_teacher=False)

    ps.teal_section(doc, "LAUNCH — Solving Radical Equations (teacher models on screen)", [])
    add_callout(doc, "\U0001f4d8  ISOLATE–RAISE–CHECK RULES (keep printed on your page)",
                [
                    "1. Isolate the radical on one side of the equation.",
                    "2. Raise BOTH sides to the index power (square for √, cube for ∛, etc.).",
                    "3. Solve the resulting polynomial equation.",
                    "4. CHECK each candidate in the ORIGINAL equation — reject any that don't satisfy it (extraneous).",
                ],
                color_hex="D9EAD3")

    add_callout(doc, "⚠️  COMMON ERROR",
                [
                    "Do NOT skip the CHECK step — squaring both sides is not a reversible operation.",
                    "A candidate solution that makes the radicand negative under an even-index radical is extraneous.",
                    "Always substitute back into the ORIGINAL equation, not the squared form.",
                ],
                color_hex="F4CCCC")
    doc.add_paragraph()

    ps.teal_section(doc, "EXPLORE — Think-Pair-Share (33 min)",
                    ["Work with a partner. Use the Isolate–Raise–Check Rules above for every problem. Move through items in order — each builds on the last."])

    items = qb.get_for_packet(EXPLORE_IDS)
    labels = [
        "Try It 1 — Isolate and raise to solve",
        "Try It 3 — Solve and check for extraneous solutions",
        "Practice #22 — Solve radical equation",
        "Practice #8 — Solve radical equation",
        "Practice #15 — Identify extraneous solutions",
        "Practice #4 — Solve and verify",
    ]
    for label, q in zip(labels, items):
        bank_item_block(doc, q, label=label, space_after_inches=1.4)

    # Share / Summary
    ps.teal_section(doc, "SHARE / SUMMARY (5 min)", [])
    ps.sentence_frame_box(doc, [
        "Pair share: “I isolated the radical to get ___. Squaring both sides gives ___. My candidate solutions are ___. When I check in the ORIGINAL equation, ___ is valid and ___ is extraneous because ___.”",
        "Whole class: one pair reads their sentence. Class signals thumbs up/sideways.",
    ])

    ps.summary_exit_box(doc, "EXIT TICKET — Summary Recap",
                        [
                            "To solve a radical equation I first ___.",
                            "I raise both sides to power ___ because ___.",
                            "An extraneous solution happens when ___.",
                            "One biggest thing I learned today: ________________________",
                        ])

    doc.add_page_break()
    ps.teal_section(doc, "OPTIONAL REINFORCEMENT (not collected)",
                    ["If you finish Explore early or want extra practice before Period 2."])

    # Model & Discuss extension (demoted from Explore to optional)
    add_callout(doc, "\U0001f52d  OPTIONAL · Model & Discuss",
                [
                    "Return to the Do Now equation. With your partner:",
                    "",
                    "B) Use Structure. Why can squaring both sides introduce a solution that doesn’t work in the original equation?",
                    "",
                    "C) Examine at least two equations you solved in Explore. For each, explain in your own words why checking is a required step and not optional.",
                ],
                color_hex="CFE2F3")

    reinforce = qb.get_for_packet(REINFORCE_IDS)
    for i, q in enumerate(reinforce, 1):
        bank_item_block(doc, q, label=f"Optional #{i}  (Savvas Practice)",
                        space_after_inches=1.8)

    doc.save(path)


# ── Teacher packet ──────────────────────────────────────────────────────────────────────────────────────

def build_teacher(path):
    doc = new_packet_doc(top=0.5, bottom=0.5, left=0.7, right=0.7)
    _header(doc, for_teacher=True)

    add_callout(doc, "\U0001f4cc  PRE-FLIGHT NOTE (read before class)",
                [
                    "Explore is 6 bank items: Try-It 1 → Try-It 3 → #22 → #8 → #15 → #4. Paced for ~5-6 min per item.",
                    "If pairs finish early, push them to the Optional Reinforcement: Model & Discuss Parts B + C (verbal/TPS), then Practice #21.",
                    "If pace slows, cut #4 (extension) — it’s the DOK-2 stretch; the core DOK-1 arc (Try-It 1 → Try-It 3 → #22 → #8 → #15) is the minimum viable set.",
                ],
                color_hex="FFD9E0")

    ps.framework_phase_header(
        doc,
        phase="Do Now",
        framework_tag="notice & wonder",
        dok="2",
        minutes=5,
        teacher_does=["Project the starter (or use printed Do Now sheet).",
                      "Circulate silently. Do NOT teach during this phase.",
                      "Collect at 5 min sharp."],
        students_do=["Write 1 notice + 1 wonder.",
                     "Write one sentence about what they would do first to solve a radical equation."],
        questions_to_ask=["(None during the phase — teacher harvests answers in Launch.)"],
        adult_role="Solo teacher: circulate silently. Resist the urge to give hints.",
    )
    q = qb.get_for_packet([DO_NOW_ID])[0]
    bank_item_block(doc, q, label=f"Do Now ({q['id']})", space_after_inches=0.3)
    add_callout(doc, "✅  ANTICIPATED STUDENT RESPONSES",
                [
                    "NOTICE (typical): \"There’s a square root.” “It’s not a normal equation.” “The variable is under a radical sign.”",
                    "WONDER (typical): “How do you undo a square root?” “Do you square both sides?” “Could there be no solution?”",
                    "SENTENCES: students might write “square both sides” or “isolate the radical first.”",
                    "KEY MOVE in Launch: surface that squaring both sides is a one-way operation — it can create solutions that don’t work in the original. That’s why CHECK is non-negotiable.",
                ],
                color_hex="D9EAD3")

    ps.framework_phase_header(
        doc,
        phase="Launch",
        framework_tag="teacher models Example 1 + Example 3",
        dok="1-2",
        minutes=12,
        teacher_does=[
            "Bridge from Do Now: “You noticed the square root. To undo it, we square both sides — but that move can create fake solutions, so we always check.”",
            "Project Example 1 (Savvas Topic 5-4). Think aloud: isolate the radical, square both sides, solve, check the candidate in the ORIGINAL equation.",
            "Project Example 3. Think aloud: isolate, square, solve, check — one candidate fails the check (extraneous). Cross it out.",
            "Pause 1× for 30-sec partner-check: “In Example 1, what step would catch a fake solution?”",
            "Do NOT solve Try-Its. Release promptly at minute 17.",
        ],
        students_do=[
            "Watch silently through Example 1.",
            "During partner-check: identify the check step.",
            "Copy the Isolate–Raise–Check Rules card into their page margin.",
            "Note the COMMON ERROR warning: always substitute into the ORIGINAL, not the squared form.",
        ],
        questions_to_ask=[
            "“What must I do before squaring?”",
            "“After squaring, how do I verify my answer?”",
            "“In Example 3, why is one solution extraneous?”",
        ],
        adult_role="Project, think aloud. Do NOT give students Try-Its to work until minute 17.",
    )
    add_callout(doc, "\U0001f3a4  TEACHER SCRIPT",
                [
                    "1. “From the Do Now, you noticed the radical. The first move is always: isolate the radical on one side.”",
                    "2. Example 1 walk-through: “Watch me. I isolate the radical, then square both sides. Now I have a polynomial equation I can solve normally. Then I CHECK my answer in the ORIGINAL — not the squared form.”",
                    "3. Example 3 walk-through: “This time I get two candidates. I check both. One works; one does NOT. That failing one is extraneous — I cross it out and write ‘extraneous’ next to it.”",
                    "4. Common-error flag: “Never skip the check. Squaring is not reversible — it can create solutions that never existed in the original equation.”",
                    "5. Release: “Now you try. Try-It 1 asks you to isolate and solve. Try-It 3 asks you to find and reject an extraneous solution.”",
                ],
                color_hex="CFE2F3")

    ps.framework_phase_header(
        doc,
        phase="Explore",
        framework_tag="Think-Pair-Share + Practice",
        dok="1-2",
        minutes=33,
        teacher_does=[
            "5 laps circulation across 33 min (~6-7 min each).",
            "Lap 1: Try-It 1 — press pairs to isolate first before squaring.",
            "Lap 2: Try-It 3 — press pairs to show the check step explicitly.",
            "Lap 3: #22 + #8 — check that pairs are substituting into the ORIGINAL equation.",
            "Lap 4: #15 — verify pairs identify and label the extraneous solution.",
            "Lap 5: #4 (extension) — stretch. Cut if pace slows.",
            "Do not give answers. Use sentence frame to press justification.",
        ],
        students_do=[
            "Pairs move in order through 6 items: 2 Try-Its + 4 Practice.",
            "For each item: isolate the radical FIRST, then raise, then check.",
            "For Practice #15 (identify extraneous): show the check step and cross out the extraneous solution.",
            "Justify with sentence frame before writing.",
        ],
        questions_to_ask=[
            "Did you isolate the radical before raising both sides?",
            "Which equation did you substitute into to check — original or squared?",
            "If a candidate doesn’t satisfy the original, what do you write?",
            "Can you use the sentence frame to explain your answer?",
            "For #4: show all steps including the check.",
        ],
        adult_role="Solo teacher: 5 laps. Press pairs to justify using the rule card. No answers.",
    )
    items = qb.get_for_packet(EXPLORE_IDS)
    labels = [
        "Try It 1",
        "Try It 3 — extraneous solution",
        "Practice #22 — Solve radical equation",
        "Practice #8 — Solve radical equation",
        "Practice #15 — Identify extraneous",
        "Practice #4 — Solve and verify",
    ]
    for label, q in zip(labels, items):
        bank_item_block(doc, q, label=f"{label} ({q['id']})", space_after_inches=0.3)
        add_callout(doc, "✅  ANSWER / ANTICIPATED TALK",
                    [q.get("notes") or "(no answer key — verify before class)"],
                    color_hex="D9EAD3")

    ps.framework_phase_header(
        doc,
        phase="Share / Summary",
        framework_tag="academic conversation",
        dok="2",
        minutes=5,
        teacher_does=[
            "Cold-call 2 pairs to read their sentence-frame sentence.",
            "Write one student-generated sentence on board.",
            "Preview P2: “Next class we’ll tackle equations with two radicals or a radical and a binomial — the same Isolate–Raise–Check logic applies.”",
        ],
        students_do=[
            "Presenting pair reads their sentence.",
            "Class signals thumbs up/sideways.",
            "Note: next class extends this to more complex radical equations.",
        ],
        questions_to_ask=[
            "What’s a sentence that captures today’s rule about extraneous solutions?",
            "Why can’t we trust a candidate solution without checking it?",
        ],
        adult_role="Cold-call 2 pairs. Keep it brief — 5 min.",
    )

    ps.framework_phase_header(
        doc,
        phase="Exit Ticket",
        framework_tag="summary recap (not graded)",
        dok="1-2",
        minutes=2,
        teacher_does=[
            "Collect at door.",
            "Scan the fill-in items — misconceptions about the check step or extraneous solutions tell you what to re-hit in P2 Do Now.",
        ],
        students_do=[
            "Complete the fill-in stems.",
            "Be honest about confusion.",
        ],
        questions_to_ask=[
            "Did students correctly identify what an extraneous solution is and why it arises?",
        ],
        adult_role="Collect. No grade.",
    )
    add_callout(doc, "\U0001f4cb  EXIT TICKET — Student Form",
                [
                    "To solve a radical equation I first ___.",
                    "I raise both sides to power ___ because ___.",
                    "An extraneous solution happens when ___.",
                    "One biggest thing I learned today: ________________________",
                ],
                color_hex="FFF2CC")

    doc.add_page_break()
    add_callout(doc, "\U0001f550  PERIOD A & F — 65-MIN CLASS NOTES",
                [
                    "Both sections get 65 min for P1. Use the extra 10 min on Explore, NOT Launch.",
                    "Suggested add: project Savvas Practice #15 and #4 on screen for 2 more TPS rounds if pairs finish fast.",
                    "Or: extend Model & Discuss Parts B + C with “write one more radical equation that has an extraneous solution — then solve and reject it.”",
                ],
                color_hex="FFD9E0")

    add_callout(doc, "\U0001f9e9  MODIFICATIONS / SUPPORT FOR IEP STUDENTS",
                [
                    "• Provide the Isolate–Raise–Check Rules card as a sticker/cut-out on their desk.",
                    "• For Try-It 1, allow students to use a step-by-step graphic organizer (isolate → raise → check).",
                    "• Accept verbal sentence-frame completions in lieu of written.",
                ],
                color_hex="E2F0D9")
    add_callout(doc, "\U0001f30d  SUPPORTS FOR ELL STUDENTS",
                [
                    "• Sentence frames printed on student packet (don’t skip).",
                    "• Word card: “extraneous solution” = a candidate answer that does not satisfy the original equation; must be rejected.",
                    "• “isolate” = get the radical alone on one side of the equation.",
                    "• “raise to the index power” = square both sides for a square root; cube both sides for a cube root.",
                    "• Pair ELL students with English-dominant partners for TPS.",
                ],
                color_hex="DEEBF7")

    doc.save(path)


# ── Main ─────────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_do_now("L54_P1_Do_Now.docx")
    build_student("L54_P1_Student_Packet.docx")
    build_teacher("L54_P1_Teacher_Packet.docx")
    print("Built L54_P1_Do_Now.docx, L54_P1_Student_Packet.docx, L54_P1_Teacher_Packet.docx")
    ps.emit_visuals_checklist(_ALL_IDS, "L54_P1_Visuals_Checklist.md",
                              title="L54 P1 — Visuals Checklist")
