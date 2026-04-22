"""Generate Lesson 3-5 Period 2 (Tuesday) materials — Klimsara-adapted, no Blooket.

Design: multiplicity + factored-form graphing. Klimsara-style student-centered
flow honoring the Lynn DOK framework (Do Now / Launch / Explore 35–40 / Share /
Exit). All student-facing items trace to Savvas bank IDs.

Phases (55 min base; Period F extended to 65 via Explore):
  0–  5   Do Now    : 3-5-savvas-q13 — identify zeros from factored form      [DOK 1]
  5– 17   Launch    : teacher models Example 2 (multiplicity) on projector    [DOK 2]
 17– 50   Explore   : Try-It 2a/2b + Practice #14, #15, #16 via Think-Pair-   [DOK 2]
                     Share (F: extended to 55' — add Practice #11 TPS slot)
 50– 55   Share/Sum : sentence-frame recap + conjugate-pair bridge prompt     [DOK 2]
 55– 58   Exit      : summary recap fill-in + one sentence                    [DOK 1-2]
 (back)   Optional Reinforcement: Practice #12, #13 (not collected)           [DOK 1-2]

Context: solo teacher, class of up to ten. No Blooket. Try-Its stay in class
(TPS) because student homework completion is unreliable.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

import qb
import packet_styles as ps

from packet_build import (
    TABLE_STYLE, new_packet_doc,
    set_cell, add_callout, bank_item_block, add_header_block,
)
DO_NOW_ID      = "3-5-savvas-q13"
PRACTICE_IDS   = ["3-5-tryit-2a", "3-5-tryit-2b",
                  "3-5-savvas-q14", "3-5-savvas-q15", "3-5-savvas-q16"]
REINFORCE_IDS  = ["3-5-savvas-q11", "3-5-savvas-q12"]
# Exit is a summary recap (fill-in + one sentence), not a bank question.

_ALL_IDS = [DO_NOW_ID] + PRACTICE_IDS + REINFORCE_IDS
qb.get_for_packet(_ALL_IDS)   # fail loudly if any ID is missing

LESSON_LABEL = "Lesson 3-5 · Period 2"
LESSON_TITLE = "Multiplicity and Factored-Form Graphing"

OBJECTIVES = [
    ("Math Objective",
     "Use the multiplicity of each zero to determine whether the graph of a "
     "polynomial crosses the x-axis or is tangent to (turns back from) it at "
     "each zero."),
    ("Language Objective",
     "Students will use the frame \u201cThe zero x = ___ has multiplicity ___, "
     "so the graph ___ the x-axis.\u201d to describe each zero's graph "
     "behavior."),
    ("Essential Understanding",
     "A factored-form polynomial reveals its zeros directly. The multiplicity "
     "of each zero — odd or even — controls whether the graph crosses or is "
     "tangent to the x-axis at that zero."),
]

FRAMEWORK_HEADER = [
    ("Topic Goals",
     "Students apply the multiplicity rule to four factored-form polynomials, "
     "one per practice item. Every item is drawn from Savvas Lesson 3-5."),
    ("Essential Question",
     "How does the multiplicity of each zero determine the graph's behavior "
     "at that x-intercept?"),
    ("Materials",
     "Pencils; student packet; calculator (optional). No Chromebooks required "
     "for Period 2."),
]


def _header(doc, *, for_teacher=False):
    add_header_block(doc, lesson_title=LESSON_TITLE, lesson_label=LESSON_LABEL,
                     objectives=OBJECTIVES, framework_header=FRAMEWORK_HEADER,
                     for_teacher=for_teacher, day_number=2)


# ── Do Now (separate 1-page sheet; collected at entry) ───────────────────

def build_do_now(path):
    doc = new_packet_doc(top=0.6, bottom=0.6, left=0.75, right=0.75)
    ps.running_header_name_block(doc, label_right="BLOCK")
    ps.day_banner(doc, 2, "Do Now — " + LESSON_TITLE, subtitle=LESSON_LABEL)

    ps.framework_phase_header(
        doc,
        phase="Do Now",
        framework_tag="bridge from Monday",
        dok="1",
        minutes=5,
        teacher_does=["Hand out at door.", "Circulate; do not stop to re-teach."],
        students_do=["Read each factor; write the zero each factor produces.",
                     "Check with a neighbor if time remains."],
        questions_to_ask=[
            "What are the zeros of a polynomial in factored form?",
            "How do you read zeros directly off (x − a)(x − b)(x − c)?",
        ],
        adult_role="Solo teacher: circulate, time 5 min, then pull the sheet.",
    )

    q = qb.get_for_packet([DO_NOW_ID])[0]
    bank_item_block(doc, q, label="Do Now — Zeros from Factored Form",
                    space_after_inches=2.0)

    add_callout(doc, "🎯  SENTENCE FRAME (for your answer)",
                ["\u201cThe zeros are x = ___, x = ___, and x = ___ because each factor equals zero.\u201d"],
                color_hex="FFF2CC")

    doc.save(path)


# ── Student packet ───────────────────────────────────────────────────────

def build_student(path):
    doc = new_packet_doc(top=0.55, bottom=0.55, left=0.7, right=0.7)
    _header(doc, for_teacher=False)

    # ── Launch space (teacher models Example 2 on projector) ──
    ps.teal_section(doc, "LAUNCH — Multiplicity Rule (teacher models on screen)", [])
    add_callout(doc, "📘  MULTIPLICITY RULES (keep printed on your page)",
                [
                    "• If a factor appears ONCE or an ODD number of times, the zero has ODD multiplicity → the graph CROSSES the x-axis at that zero.",
                    "• If a factor appears an EVEN number of times, the zero has EVEN multiplicity → the graph is TANGENT to the x-axis (touches and turns back) at that zero.",
                    "• Example: f(x) = (x − 2)³(x + 1)²  →  x = 2 has multiplicity 3 (crosses); x = −1 has multiplicity 2 (tangent).",
                ],
                color_hex="D9EAD3")
    doc.add_paragraph()

    # ── Explore ──
    ps.teal_section(doc, "EXPLORE — Think-Pair-Share (35+ min)",
                    ["Work with a partner. Use the multiplicity rules above for every problem."])

    items = qb.get_for_packet(PRACTICE_IDS)
    labels = ["Try It 2a", "Try It 2b", "Practice #14", "Practice #15", "Practice #16"]
    for label, q in zip(labels, items):
        bank_item_block(doc, q, label=label, space_after_inches=1.4)

    # ── Share / Summary ──
    ps.teal_section(doc, "SHARE / SUMMARY (5 min)", [])
    ps.sentence_frame_box(doc, [
        "Pair share: \u201cFor f(x) = ___, the zero x = ___ has multiplicity ___, "
        "so the graph ___ the x-axis at that zero.\u201d",
        "Whole class: one pair at random reads their sentence. Class signals thumbs up/sideways.",
    ])
    add_callout(doc, "🔭  BRIDGE TO TOMORROW",
                ["If a cubic has zeros 2, 1 + √3, and 1 − √3, what is the nature of its coefficients — rational, irrational, or complex? (Tuesday-to-Wednesday bridge; revisit at start of Period 3.)"],
                color_hex="FCE5CD")

    # ── Exit ──
    ps.summary_exit_box(doc, "EXIT TICKET — Summary Recap",
                        [
                            "Today I learned that _____________________________________________________.",
                            "The rule I want to remember is _____________________________________________________.",
                            "One thing I'm still unsure about is _____________________________________________________.",
                        ])

    # ── Optional Reinforcement (back-of-packet) ──
    doc.add_page_break()
    ps.teal_section(doc, "OPTIONAL REINFORCEMENT (not collected)",
                    ["If you finish early or want extra practice before Wednesday. Answers on Desmos or ask for a check."])
    reinforce = qb.get_for_packet(REINFORCE_IDS)
    for i, q in enumerate(reinforce, 1):
        bank_item_block(doc, q, label=f"Optional #{i}  (Savvas Practice)",
                        space_after_inches=1.8)

    doc.save(path)


# ── Teacher packet ───────────────────────────────────────────────────────

def build_teacher(path):
    doc = new_packet_doc(top=0.5, bottom=0.5, left=0.7, right=0.7)
    _header(doc, for_teacher=True)

    # Framework phase blocks with evaluator-required fields

    ps.framework_phase_header(
        doc,
        phase="Do Now",
        framework_tag="bridge from Monday",
        dok="1",
        minutes=5,
        teacher_does=["Hand out Do Now at door.", "Circulate during 3 min work.",
                      "Cold-call 1 student to share one zero at minute 4."],
        students_do=["Read each factor; write zeros directly.",
                     "Use sentence frame on the sheet."],
        questions_to_ask=[
            "What does it mean for (x − a) to be a factor?",
            "If (x + 6) is a factor, what zero does that give you?",
        ],
        adult_role="Solo teacher: stand at door, hand out Do Now as students enter. Circulate for ~3 min. Cold-call 1 student to share one zero.",
    )
    q = qb.get_for_packet([DO_NOW_ID])[0]
    bank_item_block(doc, q, label=f"Do Now ({q['id']})", space_after_inches=0.3)
    add_callout(doc, "✅  ANSWER KEY",
                ["Zeros: x = −3, x = 1, x = 4. Each factor (x + 3), (x − 1), (x − 4) equals zero when x takes the opposite sign of its constant term."],
                color_hex="D9EAD3")

    ps.framework_phase_header(
        doc,
        phase="Launch",
        framework_tag="teacher models Example 2",
        dok="2",
        minutes=12,
        teacher_does=[
            "Project Savvas Example 2. Think aloud: count each factor; odd → crosses, even → tangent.",
            "Pause 2× for 30-sec partner-checks.",
            "Do NOT model Try-Its — release to Explore.",
        ],
        students_do=[
            "Watch the modeled example silently first.",
            "Turn-and-talk during each 30-sec pause.",
            "Copy the Multiplicity Rules card into their page margin if desired.",
        ],
        questions_to_ask=[
            "Say: \u201cCount the factor. Odd or even?\u201d for each zero.",
            "What's the difference between \u201ccrosses\u201d and \u201ctangent to\u201d?",
            "Why does the graph turn back at even multiplicity? (Sign doesn't flip.)",
        ],
        adult_role="Project Savvas Example 2. Work it aloud with think-aloud voice. Pause 2× for 30-sec partner-check: \u201cTell your neighbor what multiplicity this zero has.\u201d",
    )
    add_callout(doc, "🎤  TEACHER SCRIPT",
                [
                    "1. \u201cWatch me do this first one. I'll read each factor, count how many times it appears, and decide if the graph crosses or is tangent.\u201d",
                    "2. For f(x) = (x − 2)³(x + 1)²: \u201cAt x = 2, the factor appears 3 times — odd — so the graph CROSSES. At x = −1, the factor appears 2 times — even — so the graph is TANGENT.\u201d",
                    "3. \u201cWhat's one thing I just did that I want you to copy?\u201d — cold-call.",
                    "4. Do NOT do Try-Its for them. Set them up, release to TPS.",
                ],
                color_hex="CFE2F3")

    ps.framework_phase_header(
        doc,
        phase="Explore",
        framework_tag="Think-Pair-Share + Practice",
        dok="2",
        minutes=33,
        teacher_does=[
            "4 laps of circulation (~8 min each).",
            "Lap 1: notice stalls. Lap 2: ask purposeful Qs. Lap 3: check answers. Lap 4: invite 1 pair to share.",
            "Do not give answers. Press pairs to justify with the rule card.",
        ],
        students_do=[
            "Work in pairs through Try-It 2a, 2b, then Practice #14, #15, #16.",
            "For each zero, write multiplicity + crosses/tangent before sketching.",
            "Justify with sentence frame aloud to partner before writing.",
        ],
        questions_to_ask=[
            "What's the multiplicity of each zero?",
            "Does the graph cross or is it tangent at each zero?",
            "How does the end behavior match the leading coefficient + degree?",
        ],
        adult_role="Solo teacher: 4 laps of circulation (~8 min each). Lap 1: notice who's stalling. Lap 2: ask purposeful Qs. Lap 3: check answers. Lap 4: invite 1 pair to share at board.",
    )
    items = qb.get_for_packet(PRACTICE_IDS)
    labels = ["Try It 2a", "Try It 2b", "Practice #14", "Practice #15", "Practice #16"]
    for label, q in zip(labels, items):
        bank_item_block(doc, q, label=f"{label} ({q['id']})", space_after_inches=0.3)
        add_callout(doc, "✅  ANSWER / ANTICIPATED TALK",
                    [q.get("notes") or "(no answer key recorded — verify before class)"],
                    color_hex="D9EAD3")

    ps.framework_phase_header(
        doc,
        phase="Share / Summary",
        framework_tag="academic conversation + bridge prompt",
        dok="2",
        minutes=5,
        teacher_does=[
            "Cold-call 2 pairs to read their sentence-frame sentence.",
            "Write the rule sentence on board (student-generated).",
            "Post the Wednesday bridge prompt visibly.",
        ],
        students_do=[
            "One student per pair reads their sentence aloud.",
            "Class signals thumbs up/sideways.",
            "Write the bridge prompt's key term (conjugate pair) in packet margin.",
        ],
        questions_to_ask=[
            "What's a sentence that captures today's rule?",
            "For Wednesday: if a cubic has zeros 2, 1 + √3, and 1 − √3 — what does that say about its coefficients?",
        ],
        adult_role="Cold-call 2 pairs. Write one sentence on board. Leave the bridge prompt posted for Wednesday Do Now.",
    )
    add_callout(doc, "🔭  BRIDGE PROMPT (post for Wednesday Do Now)",
                ["\u201cA cubic has zeros 2, 1 + √3, and 1 − √3. What is the nature of its coefficients — rational, irrational, or complex? Why?\u201d (Directly prepares Topic 3 Assessment Q#2.)"],
                color_hex="FCE5CD")

    ps.framework_phase_header(
        doc,
        phase="Exit Ticket",
        framework_tag="summary recap (not graded)",
        dok="1-2",
        minutes=2,
        teacher_does=[
            "Collect at door as students exit.",
            "Scan for confusion flags; plan tomorrow's Do Now emphasis accordingly.",
        ],
        students_do=[
            "Complete 3 sentence stems.",
            "Be honest about confusion — this is not graded.",
        ],
        questions_to_ask=[
            "Did students write a complete sentence for #1?",
            "Did anyone flag confusion in #3?",
        ],
        adult_role="Collect at door. Scan flagged items tonight. No formal grade.",
    )
    add_callout(doc, "📋  EXIT TICKET — Student Form",
                [
                    "Today I learned that ___.",
                    "The rule I want to remember is ___.",
                    "One thing I'm still unsure about is ___.",
                ],
                color_hex="FFF2CC")

    # ── Teacher-only modifications panel ──
    doc.add_page_break()
    add_callout(doc, "🧩  MODIFICATIONS / SUPPORT FOR IEP STUDENTS",
                [
                    "• Provide the Multiplicity Rule card as a sticker/cut-out on their desk.",
                    "• Allow color-coding each zero on their factored form before answering.",
                    "• Accept verbal sentence-frame completions in lieu of written.",
                ],
                color_hex="E2F0D9")
    add_callout(doc, "🌍  SUPPORTS FOR ELL STUDENTS",
                [
                    "• Sentence frames printed on student packet (don't skip).",
                    "• Word card: \u201cmultiplicity\u201d = how many times a factor appears.",
                    "• \u201ccrosses\u201d = goes through; \u201ctangent\u201d = touches and turns back (Savvas terminology).",
                    "• Pair ELL students with English-dominant partners for TPS whenever possible.",
                ],
                color_hex="DEEBF7")

    # Period F extension note
    add_callout(doc, "🕐  PERIOD F EXTENSION (65-min class)",
                [
                    "Period F has an extra 10 min. Use Explore +10 min (not Launch +10).",
                    "Suggested add: after Practice #16, pair students do Practice #11 or #12 from the Optional Reinforcement page.",
                    "Do NOT add a second Launch example — keeping the rhythm simple.",
                ],
                color_hex="FFD9E0")

    doc.save(path)


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_do_now("L35_P2_Do_Now.docx")
    build_student("L35_P2_Student_Packet.docx")
    build_teacher("L35_P2_Teacher_Packet.docx")
    print("Built L35_P2_Do_Now.docx, L35_P2_Student_Packet.docx, L35_P2_Teacher_Packet.docx")
    ps.emit_visuals_checklist(_ALL_IDS, "L35_P2_Visuals_Checklist.md",
                              title="L35 P2 — Visuals Checklist")
