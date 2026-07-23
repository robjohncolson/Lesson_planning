# Collision Review Queue

This queue lists the 85 legacy question-bank IDs from lessons 5-1, 5-4, and 5-5 that the (closed, frozen) dedup workstream flagged as **ambiguous**: one legacy id resolved to two distinct `item_uid`s because the item was captured twice with slight textual drift ("double-ingest-with-drift").
**Nothing here merges anything.** Both `item_uid`s for every group below remain live in the registry. The "suggested canonical keep" is an advisory recommendation only -- a human (the teacher) makes the final call using the checkboxes at the end of each group.
Confidence is assigned by a deterministic ladder: **high** = the drift is a clear completeness gap (one capture is missing an instruction stem or a standards tag like `MP.3`); **medium** = substantive drift (visual encoding, LaTeX formatting, or other textual differences) where the longer capture is suggested but review matters more; **low** = cosmetic-only drift (whitespace or `\circ` spacing) where the two captures are identical after normalization.
Groups are organized by lesson (5-1, then 5-4, then 5-5), and within each lesson ordered by confidence (high to low).

## Summary

| Lesson | Groups |
|---|---|
| 5-1 | 32 |
| 5-4 | 29 |
| 5-5 | 24 |
| **Total** | **85** |

| Confidence | Groups |
|---|---|
| high | 15 |
| medium | 68 |
| low | 2 |

## Lesson 5-1

32 ambiguous groups in this lesson.

### 5-1-savvas-q18

Source: Savvas Practice #18 (lesson 5-1, anchors Example 4)
Capture A = `iu_82f8bdf58be8` (line 144) &middot; Capture B = `iu_4517b4b0fb52` (line 177)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 144) | Capture B (line 177) |
|---|---|
| Construct Arguments Justice found that the fifth root of 243x^{15}y^5 is 3x^3y. Is Justice correct? Explain your reasoning. MP.3 | Construct Arguments Justice found that the fifth root of 243x^{15}y^5 is 3x^3y. Is Justice correct? Explain your reasoning. |

**Diff (exact)**

- delete: A has extra "·MP.3"
- similarity: 0.9801
- drift: trailing_standards_tag

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_82f8bdf58be8`). Flagged drifted duplicate: Capture B (`iu_4517b4b0fb52`). Confidence: high. Rationale: Identical item; drifted capture dropped the trailing standards tag (MP.x) -- keep the tagged/complete capture (A).
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q21

Source: Savvas Practice #21 (lesson 5-1, anchors Example 2)
Capture A = `iu_938dab1e20af` (line 147) &middot; Capture B = `iu_5a2f7f94b32d` (line 180)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 147) | Capture B (line 180) |
|---|---|
| Construct Arguments Determine whether \sqrt[3]{x^2} is equal to (\sqrt[3]{x})^2. Explain your reasoning. MP.3 | Construct Arguments Determine whether \sqrt[3]{x^2} is equal to (\sqrt[3]{x})^2. Explain your reasoning. |

**Diff (exact)**

- delete: A has extra "·MP.3"
- similarity: 0.9765
- drift: trailing_standards_tag

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_938dab1e20af`). Flagged drifted duplicate: Capture B (`iu_5a2f7f94b32d`). Confidence: high. Rationale: Identical item; drifted capture dropped the trailing standards tag (MP.x) -- keep the tagged/complete capture (A).
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q22

Source: Savvas Practice #22 (lesson 5-1, anchors Example 1)
Capture A = `iu_204f8ace504c` (line 148) &middot; Capture B = `iu_4df9cd02a7b7` (line 181)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 148) | Capture B (line 181) |
|---|---|
| Use Structure How many third roots does -512 have? Explain your reasoning. MP.7 | Use Structure How many third roots does -512 have? Explain your reasoning. |

**Diff (exact)**

- delete: A has extra "·MP.7"
- similarity: 0.9673
- drift: trailing_standards_tag

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_204f8ace504c`). Flagged drifted duplicate: Capture B (`iu_4df9cd02a7b7`). Confidence: high. Rationale: Identical item; drifted capture dropped the trailing standards tag (MP.x) -- keep the tagged/complete capture (A).
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q30

Source: Savvas Practice #30 (lesson 5-1, anchors Example 2)
Capture A = `iu_dbef18ec939c` (line 156) &middot; Capture B = `iu_a4f60d7d3ce0` (line 188)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 156) | Capture B (line 188) |
|---|---|
| \sqrt[6]{729} | Rewrite each expression using a fractional exponent.<br><br>\sqrt[6]{729} |

**Diff (exact)**

- insert: B adds "Rewrite·each·expression·using·a·fractional·exponent.↵↵"
- similarity: 0.325
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_a4f60d7d3ce0`). Flagged drifted duplicate: Capture A (`iu_dbef18ec939c`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q32

Source: Savvas Practice #32 (lesson 5-1, anchors Example 2)
Capture A = `iu_50b6d47338f7` (line 158) &middot; Capture B = `iu_a829788a6a35` (line 190)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 158) | Capture B (line 190) |
|---|---|
| \sqrt[4]{ab} | Rewrite each expression using a fractional exponent.<br><br>\sqrt[4]{ab} |

**Diff (exact)**

- insert: B adds "Rewrite·each·expression·using·a·fractional·exponent.↵↵"
- similarity: 0.3077
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_a829788a6a35`). Flagged drifted duplicate: Capture A (`iu_50b6d47338f7`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q33

Source: Savvas Practice #33 (lesson 5-1, anchors Example 3)
Capture A = `iu_ee0b191812e9` (line 159) &middot; Capture B = `iu_3cfd1cc8b908` (line 191)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 159) | Capture B (line 191) |
|---|---|
| \sqrt[4]{25^2} | What is the value of each expression? Round to the nearest hundredth if necessary.<br><br>\sqrt[4]{25^2} |

**Diff (exact)**

- insert: B adds "What·is·the·value·of·each·expression?·Round·to·the·nearest·hundredth·if·necessary.↵↵"
- similarity: 0.25
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_3cfd1cc8b908`). Flagged drifted duplicate: Capture A (`iu_ee0b191812e9`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q34

Source: Savvas Practice #34 (lesson 5-1, anchors Example 3)
Capture A = `iu_dfa0181705cc` (line 160) &middot; Capture B = `iu_99c726736f7f` (line 192)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 160) | Capture B (line 192) |
|---|---|
| -\sqrt[3]{125^5} | What is the value of each expression? Round to the nearest hundredth if necessary.<br><br>-\sqrt[3]{125^5} |

**Diff (exact)**

- insert: B adds "What·is·the·value·of·each·expression?·Round·to·the·nearest·hundredth·if·necessary.↵↵"
- similarity: 0.2759
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_99c726736f7f`). Flagged drifted duplicate: Capture A (`iu_dfa0181705cc`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q35

Source: Savvas Practice #35 (lesson 5-1, anchors Example 4)
Capture A = `iu_21ad0149d96c` (line 161) &middot; Capture B = `iu_a622347b8371` (line 193)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 161) | Capture B (line 193) |
|---|---|
| \sqrt[3]{8y^9} | Simplify each expression. Assume all variables are positive.<br><br>\sqrt[3]{8y^9} |

**Diff (exact)**

- insert: B adds "Simplify·each·expression.·Assume·all·variables·are·positive.↵↵"
- similarity: 0.3111
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_a622347b8371`). Flagged drifted duplicate: Capture A (`iu_21ad0149d96c`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q36

Source: Savvas Practice #36 (lesson 5-1, anchors Example 4)
Capture A = `iu_af115246aa2b` (line 162) &middot; Capture B = `iu_b1976056af7a` (line 194)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 162) | Capture B (line 194) |
|---|---|
| \sqrt[4]{q^{12}z^4} | Simplify each expression. Assume all variables are positive.<br><br>\sqrt[4]{q^{12}z^4} |

**Diff (exact)**

- insert: B adds "Simplify·each·expression.·Assume·all·variables·are·positive.↵↵"
- similarity: 0.38
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_b1976056af7a`). Flagged drifted duplicate: Capture A (`iu_af115246aa2b`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q37

Source: Savvas Practice #37 (lesson 5-1, anchors Example 4)
Capture A = `iu_0e94b3b69e37` (line 163) &middot; Capture B = `iu_7d468efb8457` (line 195)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 163) | Capture B (line 195) |
|---|---|
| \sqrt[6]{729a^{24}b^{18}} | Simplify each expression. Assume all variables are positive.<br><br>\sqrt[6]{729a^{24}b^{18}} |

**Diff (exact)**

- insert: B adds "Simplify·each·expression.·Assume·all·variables·are·positive.↵↵"
- similarity: 0.4464
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_7d468efb8457`). Flagged drifted duplicate: Capture A (`iu_0e94b3b69e37`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q38

Source: Savvas Practice #38 (lesson 5-1, anchors Example 4)
Capture A = `iu_5e878f424a05` (line 164) &middot; Capture B = `iu_f45866c5dbe4` (line 196)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 164) | Capture B (line 196) |
|---|---|
| \sqrt[8]{v^8g^{40}} | Simplify each expression. Assume all variables are positive.<br><br>\sqrt[8]{v^8g^{40}} |

**Diff (exact)**

- insert: B adds "Simplify·each·expression.·Assume·all·variables·are·positive.↵↵"
- similarity: 0.38
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_f45866c5dbe4`). Flagged drifted duplicate: Capture A (`iu_5e878f424a05`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q19

Source: Savvas Practice #19 (lesson 5-1, anchors Example 6)
Capture A = `iu_093060fbab7a` (line 145) &middot; Capture B = `iu_58e5822601fb` (line 178)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 145) | Capture B (line 178) |
|---|---|
| Make Sense and Persevere For a show, spheres were bounced and passed. Explain how to find the radius r of one of the inflated spheres. Use technology to compute your answer. MP.1<br><br>\placeholder{photo}{Many large colorful inflated spheres floating above a crowd. Label 'Volume of a sphere is 4,186 (2)/(3) in.^3'.} | Make Sense and Persevere For a show, spheres were bounced and passed. Explain how to find the radius r of one of the inflated spheres. Use technology to compute your answer.<br><br>[IMAGE: Stage show with many inflated spheres in the air. Label: "Volume of a sphere is 4,186 2/3 in.^3."] |

**Diff (exact)**

- delete: A has extra "·MP.1"
- replace: A has "\placeholder{photo}{" where B has "[I"
- insert: B adds "AGE:·Stage·show·with·m"
- replace: A has "large·colorful·inflated·spheres·floating·" where B has "inflated·spheres·in·the·air.·L"
- replace: A has "ove·a·crowd.·Label·'" where B has "el:·""
- delete: A has extra "("
- delete: A has extra ")"
- delete: A has extra "("
- delete: A has extra ")"
- replace: A has "'.}" where B has "."]"
- similarity: 0.7386
- drift: visual_encoding, latex_formatting

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_093060fbab7a`). Flagged drifted duplicate: Capture B (`iu_58e5822601fb`). Confidence: medium. Rationale: Captures differ in how the visual is encoded (\placeholder vs [IMAGE:]/[GRAPH/TIKZ]) -- suggested keep is the longer capture; reviewer confirm which visual form the pipeline wants.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q20

Source: Savvas Practice #20 (lesson 5-1, anchors Example 2)
Capture A = `iu_46633f67b24d` (line 146) &middot; Capture B = `iu_e03257c00078` (line 179)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 146) | Capture B (line 179) |
|---|---|
| Error Analysis Describe and correct the error a student made in writing this exponential expression in radical form. MP.3<br><br>[GRAPH / TIKZ figure] | Error Analysis Describe and correct the error a student made in writing this exponential expression in radical form.<br><br>x^{\frac43}=(x^4)^{\frac13}<br><br>(x^4)^{\frac13}=\sqrt[4]{x^3} |

**Diff (exact)**

- delete: A has extra "·MP.3"
- insert: B adds "x^{\frac43}=(x^4)^{\frac13}↵↵(x^4)^{\frac13}=\sqrt"
- replace: A has "GRAPH·/·TIKZ·figure" where B has "4"
- insert: B adds "{x^3}"
- similarity: 0.75
- drift: visual_encoding, latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_e03257c00078`). Flagged drifted duplicate: Capture A (`iu_46633f67b24d`). Confidence: medium. Rationale: Captures differ in how the visual is encoded (\placeholder vs [IMAGE:]/[GRAPH/TIKZ]) -- suggested keep is the longer capture; reviewer confirm which visual form the pipeline wants.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q23

Source: Savvas Practice #23 (lesson 5-1, anchors Example 6)
Capture A = `iu_9cc08c80849a` (line 149) &middot; Capture B = `iu_fd7476f3e070` (line 182)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 149) | Capture B (line 182) |
|---|---|
| Higher Order Thinking The annual interest formula below calculates the final balance of an account, F, given a starting balance, S, and an interest rate, r, after 10 years.<br> F = S(1 + r)^{10} <br>When solving for r, why can the negative root be ignored? | Higher Order Thinking The annual interest formula below calculates the final balance of an account, F, given a starting balance, S, and an interest rate, r, after 10 years.<br><br>F=S(1+r)^{10}<br><br>When solving for r, why can the negative root be ignored? |

**Diff (exact)**

- replace: A has "·" where B has "↵"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "·" where B has "↵"
- similarity: 0.9839
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_9cc08c80849a`). Flagged drifted duplicate: Capture B (`iu_fd7476f3e070`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q25

Source: Savvas Practice #25 (lesson 5-1, anchors Example 1)
Capture A = `iu_740df4445f8e` (line 151) &middot; Capture B = `iu_ea7ff0963831` (line 183)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 151) | Capture B (line 183) |
|---|---|
| the real fourth roots of 81 | Find the specified roots of each number.<br><br>The real fourth roots of 81. |

**Diff (exact)**

- insert: B adds "Find·"
- insert: B adds "he·specified·roots·of·each·number.↵↵T"
- insert: B adds "."
- similarity: 0.5567
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_ea7ff0963831`). Flagged drifted duplicate: Capture A (`iu_740df4445f8e`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q26

Source: Savvas Practice #26 (lesson 5-1, anchors Example 1)
Capture A = `iu_fa8da03a0edd` (line 152) &middot; Capture B = `iu_ce5c2234823a` (line 184)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 152) | Capture B (line 184) |
|---|---|
| the real third roots of 343 | Find the specified roots of each number.<br><br>The real third roots of 343. |

**Diff (exact)**

- insert: B adds "Find·"
- insert: B adds "he·specified·roots·of·each·number.↵↵T"
- insert: B adds "."
- similarity: 0.5567
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_ce5c2234823a`). Flagged drifted duplicate: Capture A (`iu_fa8da03a0edd`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q27

Source: Savvas Practice #27 (lesson 5-1, anchors Example 1)
Capture A = `iu_9e0291f03f7d` (line 153) &middot; Capture B = `iu_fee5e53ff9f8` (line 185)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 153) | Capture B (line 185) |
|---|---|
| the real fifth roots of 1,024 | Find the specified roots of each number.<br><br>The real fifth roots of 1,024. |

**Diff (exact)**

- insert: B adds "Find·"
- insert: B adds "he·specified·roots·of·each·number.↵↵T"
- insert: B adds "."
- similarity: 0.5743
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_fee5e53ff9f8`). Flagged drifted duplicate: Capture A (`iu_9e0291f03f7d`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q28

Source: Savvas Practice #28 (lesson 5-1, anchors Example 1)
Capture A = `iu_361700905568` (line 154) &middot; Capture B = `iu_0b2db4e3cfc7` (line 186)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 154) | Capture B (line 186) |
|---|---|
| the real square roots of 25 | Find the specified roots of each number.<br><br>The real square roots of 25. |

**Diff (exact)**

- insert: B adds "Find·"
- insert: B adds "he·specified·roots·of·each·number.↵↵T"
- insert: B adds "."
- similarity: 0.5567
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_0b2db4e3cfc7`). Flagged drifted duplicate: Capture A (`iu_361700905568`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q29

Source: Savvas Practice #29 (lesson 5-1, anchors Example 2)
Capture A = `iu_5072b6a692fe` (line 155) &middot; Capture B = `iu_8c6491022f08` (line 187)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 155) | Capture B (line 187) |
|---|---|
| \sqrt[6]{16^2} | Rewrite each expression using a fractional exponent.<br><br>\sqrt[4]{16^2} |

**Diff (exact)**

- insert: B adds "Rewrite·each·expression·using·a·fractional·exponent.↵↵"
- replace: A has "6" where B has "4"
- similarity: 0.3171
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_8c6491022f08`). Flagged drifted duplicate: Capture A (`iu_5072b6a692fe`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q31

Source: Savvas Practice #31 (lesson 5-1, anchors Example 2)
Capture A = `iu_cf453f3abe95` (line 157) &middot; Capture B = `iu_94d4acbcb912` (line 189)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 157) | Capture B (line 189) |
|---|---|
| \sqrt[3]{x^2} | Rewrite each expression using a fractional exponent.<br><br>\sqrt[7]{x^2} |

**Diff (exact)**

- insert: B adds "Rewrite·each·expression·using·a·fractional·exponent.↵↵"
- replace: A has "3" where B has "7"
- similarity: 0.3
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_94d4acbcb912`). Flagged drifted duplicate: Capture A (`iu_cf453f3abe95`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q39

Source: Savvas Practice #39 (lesson 5-1, anchors Example 5)
Capture A = `iu_43d66123b89c` (line 165) &middot; Capture B = `iu_af8c5e37feaf` (line 197)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 165) | Capture B (line 197) |
|---|---|
| 1,125 = 9x^3 | Solve each equation.<br><br>1,125=9x^3 |

**Diff (exact)**

- insert: B adds "Solve·each·equation.↵↵"
- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.4545
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_af8c5e37feaf`). Flagged drifted duplicate: Capture A (`iu_43d66123b89c`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q40

Source: Savvas Practice #40 (lesson 5-1, anchors Example 5)
Capture A = `iu_f0742a9b81c9` (line 166) &middot; Capture B = `iu_42c330324205` (line 198)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 166) | Capture B (line 198) |
|---|---|
| 6,480 = 5w^4 | Solve each equation.<br><br>6,480=5w^4 |

**Diff (exact)**

- insert: B adds "Solve·each·equation.↵↵"
- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.4545
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_42c330324205`). Flagged drifted duplicate: Capture A (`iu_f0742a9b81c9`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q41

Source: Savvas Practice #41 (lesson 5-1, anchors Example 5)
Capture A = `iu_d72ae9e4f91e` (line 167) &middot; Capture B = `iu_9cdfe21fd21d` (line 199)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 167) | Capture B (line 199) |
|---|---|
| 270 = 10q^3 | Solve each equation.<br><br>270=10q^3 |

**Diff (exact)**

- insert: B adds "Solve·each·equation.↵↵"
- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.4286
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_9cdfe21fd21d`). Flagged drifted duplicate: Capture A (`iu_d72ae9e4f91e`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q42

Source: Savvas Practice #42 (lesson 5-1, anchors Example 5)
Capture A = `iu_c3ea03709d73` (line 168) &middot; Capture B = `iu_2ef927b1c5e0` (line 200)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 168) | Capture B (line 200) |
|---|---|
| 256 = 4h^6 | Solve each equation.<br><br>256=4h^6 |

**Diff (exact)**

- insert: B adds "Solve·each·equation.↵↵"
- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.4
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_2ef927b1c5e0`). Flagged drifted duplicate: Capture A (`iu_c3ea03709d73`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q43

Source: Savvas Practice #43 (lesson 5-1, anchors Example 6)
Capture A = `iu_2f69c5b4a906` (line 169) &middot; Capture B = `iu_0be7ef33b416` (line 201)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 169) | Capture B (line 201) |
|---|---|
| A small cube holds chocolate candies. Its side length is 1.5 in. smaller than a second, larger cube of chocolate candies. What is the volume of the larger cube? SEE EXAMPLE 6<br><br>[IMAGE: Two cubes of chocolate. Smaller cube labeled 'Volume is 85 in.^3' with 'DARK Chocolate' on it. Larger cube with 'Milk CHOCOLATE' on it.] | A small cube holds chocolate candies. Its side length is 1.5 in. smaller than a second, larger cube of chocolate candies. What is the volume of the larger cube?<br><br>[IMAGE: Two chocolate candy boxes. Smaller box labeled "DARK Chocolate" with label "Volume is 85 in.^3"; larger box labeled "Milk CHOCOLATE."] |

**Diff (exact)**

- delete: A has extra "·SEE·EXAMPLE·6"
- replace: A has "ubes·of·chocolate" where B has "hocolate·candy·boxes"
- replace: A has "cube·labeled·'Volume·is·85·in.^3'·with·'" where B has "box·labeled·""
- replace: A has "'·on·it.·L" where B has ""·with·label·"Volume·is·85·in.^3";·l"
- replace: A has "cube·with·'" where B has "box·labeled·""
- replace: A has "'·on·it." where B has ".""
- similarity: 0.7051
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_2f69c5b4a906`). Flagged drifted duplicate: Capture B (`iu_0be7ef33b416`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q44

Source: Savvas Practice #44 (lesson 5-1, anchors Example 6)
Capture A = `iu_5d4f07b8146f` (line 170) &middot; Capture B = `iu_bd1bc0aec281` (line 202)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 170) | Capture B (line 202) |
|---|---|
| Model With Mathematics A water-walking ball has a set volume. What is the radius, r, of the ball?<br><br>\placeholder{illustration}{Person inside a transparent inflatable ball walking on water. Label 'volume ≈ 4.19 m^3'.} | Model With Mathematics A water-walking ball has a set volume. What is the radius, r, of the ball?<br><br>[IMAGE: Person inside a transparent water-walking ball floating on water; label reads "volume ≈ 4.19 m^3."] |

**Diff (exact)**

- replace: A has "\" where B has "[IMAGE:·Person·inside·a·trans"
- replace: A has "laceholder{illustration}{Person·inside·a·transparent·in" where B has "arent·water-walking·ball·"
- replace: A has "atable·ball·walk" where B has "oat"
- replace: A has ".·Label·'" where B has ";·label·reads·""
- delete: A has extra "'"
- replace: A has "}" where B has ""]"
- similarity: 0.6271
- drift: visual_encoding

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_5d4f07b8146f`). Flagged drifted duplicate: Capture B (`iu_bd1bc0aec281`). Confidence: medium. Rationale: Captures differ in how the visual is encoded (\placeholder vs [IMAGE:]/[GRAPH/TIKZ]) -- suggested keep is the longer capture; reviewer confirm which visual form the pipeline wants.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q45

Source: Savvas Practice #45 (lesson 5-1, anchors Example 6)
Capture A = `iu_7b2d29db52d4` (line 171) &middot; Capture B = `iu_47a86f758dce` (line 203)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 171) | Capture B (line 203) |
|---|---|
| Make Sense and Persevere Ahmed received a box of gifts. The box is a rectangular prism with the same height and width, and the length is twice the width. The volume of the box is 3,456 in.^3. What is the height of the box?<br><br>\placeholder{illustration}{A rectangular prism box labeled 'Mystery BOX' with gifts flowing out. Dimensions marked: depth is x in., height is x in., width is 2x in.} | Make Sense and Persevere Ahmed received a box of gifts. The box is a rectangular prism with the same height and width, and the length is twice the width. The volume of the box is 3,456 in.^3. What is the height of the box?<br><br>[GRAPH / TIKZ figure] |

**Diff (exact)**

- replace: A has "\placeholder{ill" where B has "[GRAPH·/·TIKZ·fig"
- replace: A has "stration}{A·rectangular·prism·box·labeled·'Mystery·BOX'·with·gifts·flowing·out.·Dimensions·marked:·depth·is·x·in.,·height·is·x·in.,·width·is·2x·in.}" where B has "re]"
- similarity: 0.7098
- drift: visual_encoding

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_7b2d29db52d4`). Flagged drifted duplicate: Capture B (`iu_47a86f758dce`). Confidence: medium. Rationale: Captures differ in how the visual is encoded (\placeholder vs [IMAGE:]/[GRAPH/TIKZ]) -- suggested keep is the longer capture; reviewer confirm which visual form the pipeline wants.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q46

Source: Savvas Practice #46 (lesson 5-1, anchors Example 6)
Capture A = `iu_0d2113ea5dc1` (line 172) &middot; Capture B = `iu_e035182a3846` (line 204)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 172) | Capture B (line 204) |
|---|---|
| Make Sense and Persevere Amelia's bank account earns interest annually. The equation shows her starting balance of $200 and her balance at the end of four years, $220.82. At what rate, r, did Amelia earn interest?<br> 220.82 = 200(1 + r)^4 | Make Sense and Persevere Amelia's bank account earns interest annually. The equation shows her starting balance of $200 and her balance at the end of four years, $220.82. At what rate, r, did Amelia earn interest?<br><br>220.82=200(1+r)^4 |

**Diff (exact)**

- replace: A has "·" where B has "↵"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.9872
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_0d2113ea5dc1`). Flagged drifted duplicate: Capture B (`iu_e035182a3846`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q47

Source: Savvas Practice #47 (lesson 5-1, anchors Example 2)
Capture A = `iu_c0b126356b15` (line 173) &middot; Capture B = `iu_a6baaed4c594` (line 205)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 173) | Capture B (line 205) |
|---|---|
| Model With Mathematics One measure of a patient's body surface area is found using the expression √((H · W)/(3,600)). Write this with a fractional exponent. | Model With Mathematics One measure of a patient's body surface area is found using the expression<br><br>√((H· W)/(3,600)).<br><br>Write this with a fractional exponent. |

**Diff (exact)**

- replace: A has "·" where B has "↵↵"
- delete: A has extra "·"
- replace: A has "·" where B has "↵↵"
- similarity: 0.9776
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_a6baaed4c594`). Flagged drifted duplicate: Capture A (`iu_c0b126356b15`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q48

Source: Savvas Practice #48 (lesson 5-1, anchors Example 2)
Capture A = `iu_6ccaa1de9864` (line 174) &middot; Capture B = `iu_bd157bf28b74` (line 206)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 174) | Capture B (line 206) |
|---|---|
| Determine if each expression is another way to write b^{(3)/(4)}. Select Yes or No.<br><br>TABLE:<br> →prule \| Yes \| No <br>\midrule<br>a. \sqrt[4]{b^3} \| \square \| \square <br>b. (b^3)^{(1)/(4)} \| \square \| \square <br>c. b^{(4)/(3)} \| \square \| \square <br>d. \sqrt[3]{b^4} \| \square \| \square <br>e. (b^3)/(b^4) \| \square \| \square <br>\bottomrule<br>END_TABLE | Determine if each expression is another way to write b^{\frac34}. Select Yes or No.<br><br>TABLE:<br> →prule<br>Expression \| Yes \| No <br>\midrule<br>a. \sqrt[4]{b^3} \| \square \| \square <br>b. (b^3)^{\frac14} \| \square \| \square <br>c. b^{\frac43} \| \square \| \square <br>d. \sqrt[3]{b^4} \| \square \| \square <br>e. \dfrac{b^3}{b^4} \| \square \| \square <br>\bottomrule<br>END_TABLE |

**Diff (exact)**

- replace: A has "(3)/(4)" where B has "\frac34"
- insert: B adds "↵Expression"
- replace: A has "(" where B has "\frac"
- replace: A has ")/(4)}·|·\square·|·\square·↵c.·b^{(4)/(3)" where B has "4}·|·\square·|·\square·↵c.·b^{\frac43"
- replace: A has "(b^3)/(b^4)" where B has "\dfrac{b^3}{b^4}"
- similarity: 0.7988
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_bd157bf28b74`). Flagged drifted duplicate: Capture A (`iu_6ccaa1de9864`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q49

Source: Savvas Practice #49 (lesson 5-1, anchors Example 4)
Capture A = `iu_74578c8a5256` (line 175) &middot; Capture B = `iu_d41132be3a75` (line 207)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 175) | Capture B (line 207) |
|---|---|
| SAT/ACT Which of the following is equivalent to \sqrt[6]{4,096x^{18}y^{30}}, where x > 0 and y > 0?<br>\begin{enumerate}<br> \item[A] 682.7x^{15}y^{24}<br> \item[B] 4x^{1.6}y^{1.8}<br> \item[C] 4,096x^3y^5<br> \item[D] 4x^3y^5<br> \item[E] 682.7x^3y^5<br>\end{enumerate} | SAT/ACT Which of the following is equivalent to \sqrt[6]{4,096x^{18}y^{30}}, where x>0 and y>0?<br><br>A. 682.7x^{15}y^{24}<br><br>B. 4x^{1.6}y^{1.8}<br><br>C. 4,096x^3y^5<br><br>D. 4x^3y^5<br><br>E. 682.7x^3y^5 |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "\begin{enumerate}"
- delete: A has extra "·\item["
- replace: A has "]" where B has "."
- replace: A has "·\item[" where B has "↵"
- replace: A has "]" where B has "."
- replace: A has "·\item[" where B has "↵"
- replace: A has "]" where B has "."
- replace: A has "·\item[" where B has "↵"
- replace: A has "]" where B has "."
- replace: A has "·\item[" where B has "↵"
- replace: A has "]" where B has "."
- delete: A has extra "↵\end{enumerate}"
- similarity: 0.8
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_74578c8a5256`). Flagged drifted duplicate: Capture B (`iu_d41132be3a75`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-1-savvas-q50

Source: Savvas Practice #50 (lesson 5-1, anchors Example 6)
Capture A = `iu_39e544109263` (line 176) &middot; Capture B = `iu_dacd42314635` (line 208)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 176) | Capture B (line 208) |
|---|---|
| Performance Task A milk processing company uses cylindrical-shaped containers. The height of the container is equal to the diameter of the base.<br><br>\placeholder{illustration}{A cylindrical milk container inside a processing facility. Label 'volume 169.65 ft^3'.}<br><br>Part A How much material is needed to make the lateral surface area of the shipping container?<br><br>Part B The cargo hold of a ship is 20 ft high. What is the largest number of these shipping containers that could be stacked on top of each other inside the cargo hold? | Performance Task A milk processing company uses cylindrical-shaped containers. The height of the container is equal to the diameter of the base.<br><br>[IMAGE: Milk processing machine with an orange cylindrical container; label reads "volume 169.65 ft^3."]<br><br>Part A How much material is needed to make the lateral surface area of the shipping container?<br><br>Part B The cargo hold of a ship is 20 ft high. What is the largest number of these shipping containers that could be stacked on top of each other inside the cargo hold? |

**Diff (exact)**

- replace: A has "\placeholder{illustration}{" where B has "[IM"
- insert: B adds "GE:·Milk·processing·machine·with·an·orange"
- replace: A has "milk·container·inside·a·processing·facility.·L" where B has "container;·l"
- replace: A has "'" where B has "reads·""
- delete: A has extra "'"
- replace: A has "}" where B has ""]"
- similarity: 0.8637
- drift: visual_encoding

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_39e544109263`). Flagged drifted duplicate: Capture B (`iu_dacd42314635`). Confidence: medium. Rationale: Captures differ in how the visual is encoded (\placeholder vs [IMAGE:]/[GRAPH/TIKZ]) -- suggested keep is the longer capture; reviewer confirm which visual form the pipeline wants.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

## Lesson 5-4

29 ambiguous groups in this lesson.

### 5-4-savvas-q16

Source: Savvas Practice #16 (lesson 5-4)
Capture A = `iu_cf96dc8a31e5` (line 274) &middot; Capture B = `iu_6afc10a9b8ed` (line 305)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 274) | Capture B (line 305) |
|---|---|
| Look for Relationships Write a radical equation that relates a square's perimeter to its area. Explain your reasoning. Use s to represent the side length of the square. | Look for Relationships Write a radical equation that relates a square's perimeter to its area. Explain your reasoning. Use (s) to represent the side length of the square. |

**Diff (exact)**

- insert: B adds "("
- insert: B adds ")"
- similarity: 0.9941
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_6afc10a9b8ed`). Flagged drifted duplicate: Capture A (`iu_cf96dc8a31e5`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q17

Source: Savvas Practice #17 (lesson 5-4)
Capture A = `iu_3fce00d12aad` (line 275) &middot; Capture B = `iu_9676950b926c` (line 306)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 275) | Capture B (line 306) |
|---|---|
| Error Analysis Describe and correct the error a student made in rewriting the equation to isolate y.<br><br>\begin{center}<br>\colorbox{gray!10}{ box{4cm}{<br>\begin{align*}<br>x &= \frac{√(58 + y)}{1.98} <br>1.98x &= √(58 + y) <br>1.98x^2 &= 58 + y \text{\textcolor{red}{\ding{55}}} <br>1.98x^2 - 58 &= y<br>\end{align*}<br>}}<br>\end{center} | Error Analysis Describe and correct the error a student made in rewriting the equation to isolate (y).<br>\begin{align*}<br>x&=\frac{√(58+y)}{1.98}\<br>1.98x&=√(58+y)\<br>1.98x^2&=58+y\<br>1.98x^2-58&=y<br>\end{align*} |

**Diff (exact)**

- replace: A has "y.↵" where B has "(y)."
- delete: A has extra "center}↵\colorbox{gray!10}{·box{4cm}{↵\begin{"
- replace: A has "·&=·" where B has "&="
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "·↵1.98x·&=·" where B has "\↵1.98x&="
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "·" where B has "\"
- replace: A has "·&=·58·" where B has "&=58"
- replace: A has "·y·\text{\textcolor{red}{\ding{55}}}·" where B has "y\"
- delete: A has extra "·"
- replace: A has "·58·&=·" where B has "58&="
- delete: A has extra "↵}}↵\end{center}"
- similarity: 0.6824
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_3fce00d12aad`). Flagged drifted duplicate: Capture B (`iu_9676950b926c`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q18

Source: Savvas Practice #18 (lesson 5-4)
Capture A = `iu_35f3e9014abc` (line 276) &middot; Capture B = `iu_d3ef1d0b4a28` (line 307)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 276) | Capture B (line 307) |
|---|---|
| Use Appropriate Tools Find the point of intersection of the two graphs.<br><br>\begin{center}<br>[GRAPH / TIKZ figure]<br>\end{center} | Use Appropriate Tools Find the point of intersection of the two graphs.<br><br>[GRAPH / TIKZ figure] |

**Diff (exact)**

- delete: A has extra "\begin{center}↵"
- delete: A has extra "↵\end{center}"
- similarity: 0.8704
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_35f3e9014abc`). Flagged drifted duplicate: Capture B (`iu_d3ef1d0b4a28`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q21

Source: Savvas Practice #21 (lesson 5-4)
Capture A = `iu_bf2e53fb5aaa` (line 279) &middot; Capture B = `iu_c470845cd9f5` (line 308)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 279) | Capture B (line 308) |
|---|---|
| \sqrt[3]{x} + 8 = 13 | Solve each radical equation. (\sqrt[3]{x}+8=13) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.4776
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_c470845cd9f5`). Flagged drifted duplicate: Capture A (`iu_bf2e53fb5aaa`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q22

Source: Savvas Practice #22 (lesson 5-4)
Capture A = `iu_84131456696f` (line 280) &middot; Capture B = `iu_2687f61c33c5` (line 309)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 280) | Capture B (line 309) |
|---|---|
| √(4x) = 11 | Solve each radical equation. (√(4x)=11) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·("
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.3265
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_2687f61c33c5`). Flagged drifted duplicate: Capture A (`iu_84131456696f`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q23

Source: Savvas Practice #23 (lesson 5-4)
Capture A = `iu_5d11f886423f` (line 281) &middot; Capture B = `iu_e067aeabdb5e` (line 310)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 281) | Capture B (line 310) |
|---|---|
| √(75 + x) - 6 = 14 | Solve each radical equation. (√(75+x)-6=14) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.3934
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_e067aeabdb5e`). Flagged drifted duplicate: Capture A (`iu_5d11f886423f`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q24

Source: Savvas Practice #24 (lesson 5-4)
Capture A = `iu_e106ef5ef48e` (line 282) &middot; Capture B = `iu_da8e33db9d06` (line 311)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 282) | Capture B (line 311) |
|---|---|
| 25 - \sqrt[4]{x} = 22 | Solve each radical equation. (25-\sqrt[4]{x}=22) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.4928
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_da8e33db9d06`). Flagged drifted duplicate: Capture A (`iu_e106ef5ef48e`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q25

Source: Savvas Practice #25 (lesson 5-4)
Capture A = `iu_8e4e2787396a` (line 283) &middot; Capture B = `iu_cd45fbec9dbc` (line 312)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 283) | Capture B (line 312) |
|---|---|
| x = 3(\sqrt[3]{15 + y}) | Solve for (y). (x=3\sqrt[3]{15+y}) |

**Diff (exact)**

- insert: B adds "Solve·for·(y).·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "("
- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.6316
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_cd45fbec9dbc`). Flagged drifted duplicate: Capture A (`iu_8e4e2787396a`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q26

Source: Savvas Practice #26 (lesson 5-4)
Capture A = `iu_68d1a5b3e8f8` (line 284) &middot; Capture B = `iu_323815e656c9` (line 313)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 284) | Capture B (line 313) |
|---|---|
| x = \frac{√(2y)}{26} | Solve for (y). (x=\frac{√(2y)}{26}) |

**Diff (exact)**

- insert: B adds "Solve·for·(y).·("
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.6545
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_323815e656c9`). Flagged drifted duplicate: Capture A (`iu_68d1a5b3e8f8`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q27

Source: Savvas Practice #27 (lesson 5-4)
Capture A = `iu_9681eda37337` (line 285) &middot; Capture B = `iu_26a15cb256cd` (line 314)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 285) | Capture B (line 314) |
|---|---|
| x = \frac{√(y - 14.2)}{0.05} | Solve for (y). (x=\frac{√(y-14.2)}{0.05}) |

**Diff (exact)**

- insert: B adds "Solve·for·(y).·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.6957
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_26a15cb256cd`). Flagged drifted duplicate: Capture A (`iu_9681eda37337`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q28

Source: Savvas Practice #28 (lesson 5-4)
Capture A = `iu_18cac1a8167a` (line 286) &middot; Capture B = `iu_d2eb395dfeee` (line 315)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 286) | Capture B (line 315) |
|---|---|
| x = (1)/(3)(\sqrt[4]{y}) | Solve for (y). (x=(1)/(3)\sqrt[4]{y}) |

**Diff (exact)**

- insert: B adds "Solve·for·(y).·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "("
- similarity: 0.6885
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_d2eb395dfeee`). Flagged drifted duplicate: Capture A (`iu_18cac1a8167a`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q29

Source: Savvas Practice #29 (lesson 5-4)
Capture A = `iu_e7638fcec56e` (line 287) &middot; Capture B = `iu_6eb3a7c167c0` (line 316)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 287) | Capture B (line 316) |
|---|---|
| x = √(x + 6) | Solve each radical equation. Check for extraneous solutions. (x=√(x+6)) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·Check·for·e"
- insert: B adds "traneous"
- insert: B adds "solutions.·(x"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.2169
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_6eb3a7c167c0`). Flagged drifted duplicate: Capture A (`iu_e7638fcec56e`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q30

Source: Savvas Practice #30 (lesson 5-4)
Capture A = `iu_32a6c3b34ca1` (line 288) &middot; Capture B = `iu_3646823c6297` (line 317)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 288) | Capture B (line 317) |
|---|---|
| 2x = √(17x - 15) | Solve each radical equation. Check for extraneous solutions. (2x=√(17x-15)) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·Check·for·extraneous·solutions.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.2637
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_3646823c6297`). Flagged drifted duplicate: Capture A (`iu_32a6c3b34ca1`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q31

Source: Savvas Practice #31 (lesson 5-4)
Capture A = `iu_beec9e3bdf89` (line 289) &middot; Capture B = `iu_d8950c94a8bc` (line 318)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 289) | Capture B (line 318) |
|---|---|
| 4x = √(6x + 10) | Solve each radical equation. Check for extraneous solutions. (4x=√(6x+10)) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·Check·for·extraneous·solutions.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.2472
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_d8950c94a8bc`). Flagged drifted duplicate: Capture A (`iu_beec9e3bdf89`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q32

Source: Savvas Practice #32 (lesson 5-4)
Capture A = `iu_74cca3783f59` (line 290) &middot; Capture B = `iu_c1771afa2a7f` (line 319)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 290) | Capture B (line 319) |
|---|---|
| x = √(56 - x) | Solve each radical equation. Check for extraneous solutions. (x=√(56-x)) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·Check·for·e"
- insert: B adds "traneous"
- insert: B adds "solutions.·(x"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.2353
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_c1771afa2a7f`). Flagged drifted duplicate: Capture A (`iu_74cca3783f59`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q33

Source: Savvas Practice #33 (lesson 5-4)
Capture A = `iu_3adc6df8b95d` (line 291) &middot; Capture B = `iu_c6ab822e227b` (line 320)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 291) | Capture B (line 320) |
|---|---|
| 0.5(x^2 + 5x + 136)^{2/3} = 50 | Solve. (0.5(x^2+5x+136)^{(2)/(3)}=50) |

**Diff (exact)**

- insert: B adds "Solve.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds "("
- insert: B adds ")"
- insert: B adds "("
- insert: B adds ")"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.7164
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_c6ab822e227b`). Flagged drifted duplicate: Capture A (`iu_3adc6df8b95d`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q34

Source: Savvas Practice #34 (lesson 5-4)
Capture A = `iu_a96e5311a459` (line 292) &middot; Capture B = `iu_748071c541b9` (line 321)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 292) | Capture B (line 321) |
|---|---|
| 2(x^2 - 12x - 4)^{1/2} - 3 = 15 | Solve. (2(x^2-12x-4)^{(1)/(2)}-3=15) |

**Diff (exact)**

- insert: B adds "Solve.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds "("
- insert: B adds ")"
- insert: B adds "("
- insert: B adds ")"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.6866
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_748071c541b9`). Flagged drifted duplicate: Capture A (`iu_a96e5311a459`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q35

Source: Savvas Practice #35 (lesson 5-4)
Capture A = `iu_3b2700252892` (line 293) &middot; Capture B = `iu_22bcc429d37c` (line 322)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 293) | Capture B (line 322) |
|---|---|
| (x^2 + 4x + 5)^{3/2} + 1 = 0 | Solve. ((x^2+4x+5)^{(3)/(2)}+1=0) |

**Diff (exact)**

- insert: B adds "Solve.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds "("
- insert: B adds ")"
- insert: B adds "("
- insert: B adds ")"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.6557
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_22bcc429d37c`). Flagged drifted duplicate: Capture A (`iu_3b2700252892`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q36

Source: Savvas Practice #36 (lesson 5-4)
Capture A = `iu_5663d63244d2` (line 294) &middot; Capture B = `iu_3c4458af5f01` (line 323)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 294) | Capture B (line 323) |
|---|---|
| √(6 + x) - √(x - 5) = 2 | Solve each radical equation. Check for extraneous solutions. (√(6+x)-√(x-5)=2) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·Check·for·extraneous·solutions.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.297
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_3c4458af5f01`). Flagged drifted duplicate: Capture A (`iu_5663d63244d2`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q37

Source: Savvas Practice #37 (lesson 5-4)
Capture A = `iu_c8710e0538db` (line 295) &middot; Capture B = `iu_994890f62b0f` (line 324)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 295) | Capture B (line 324) |
|---|---|
| √(4x + 5) - √(x + 1) = 1 | Solve each radical equation. Check for extraneous solutions. (√(4x+5)-√(x+1)=1) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·Check·for·extraneous·solutions.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.3107
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_994890f62b0f`). Flagged drifted duplicate: Capture A (`iu_c8710e0538db`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q38

Source: Savvas Practice #38 (lesson 5-4)
Capture A = `iu_80622035e09c` (line 296) &middot; Capture B = `iu_b04e59b85637` (line 325)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 296) | Capture B (line 325) |
|---|---|
| √(x + 1) + 1 = √(x + 3) | Solve each radical equation. Check for extraneous solutions. (√(x+1)+1=√(x+3)) |

**Diff (exact)**

- insert: B adds "Solve·each·radical·equation.·Check·for·extraneous·solutions.·("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- similarity: 0.297
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_b04e59b85637`). Flagged drifted duplicate: Capture A (`iu_80622035e09c`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q39

Source: Savvas Practice #39 (lesson 5-4)
Capture A = `iu_6afe9c1960b0` (line 297) &middot; Capture B = `iu_6826655b6fe7` (line 326)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 297) | Capture B (line 326) |
|---|---|
| A sports medicine specialist determines that a hot-weather training strategy is appropriate for this athlete. To the nearest tenth, what can the mass of the athlete be for the training strategy to be appropriate?<br><br>[IMAGE: A female runner finishing a race. Labels point to her: "Finish", bib number "1789", height "165 cm", and a note "BSA < 2.0".] | Solve using the formula (BSA=\sqrt{\frac{H· M}{3{,}600}}). A sports medicine specialist determines that a hot-weather training strategy is appropriate for this athlete. To the nearest tenth, what can the mass of the athlete be for the training strategy to be appropriate?<br><br>[IMAGE: Athlete in white coat at a finish line with labels "BSA < 2.0" and "165 cm".] |

**Diff (exact)**

- insert: B adds "Solve·using·the·formula·(BSA=\sqrt{\frac{H··M}{3{,}600}}).·"
- replace: A has "·female·runner·finishing·a·race" where B has "thlete·in·white·coat·at·a·finish·line·with·labels·"BSA·<·2"
- replace: A has "·Labels·point·to·her:·" where B has "0"
- replace: A has "Finish",·bib·number·"1789",·height" where B has "·and"
- delete: A has extra ",·and·a·note·"BSA·<·2.0""
- similarity: 0.6695
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_6826655b6fe7`). Flagged drifted duplicate: Capture A (`iu_6afe9c1960b0`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q40

Source: Savvas Practice #40 (lesson 5-4)
Capture A = `iu_6c46f0da311e` (line 298) &middot; Capture B = `iu_f12f2d341680` (line 327)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 298) | Capture B (line 327) |
|---|---|
| Specialists can determine the speed a vehicle was traveling from the length of its skid marks, d, and the coefficient of friction, f. Rewrite the formula to solve for the length of the skid marks.<br><br>\placeholder{illustration}{A car leaving skid marks on a curvy road. A text box says: "Vehicle's speed is 15.9√(df)."} | Specialists can determine the speed a vehicle was traveling from the length of its skid marks, (d), and the coefficient of friction, (f). Rewrite the formula to solve for the length of the skid marks.<br><br>\placeholder{illustration}{Car skid marks on a road with label "Vehicle's speed is (15.9√(df))".} |

**Diff (exact)**

- replace: A has "d" where B has "(d)"
- replace: A has "f" where B has "(f)"
- replace: A has "A·car·leaving·skid·marks·on·a·curvy·road.·A·text·" where B has "Car·skid·marks·on·a·road·with·la"
- replace: A has "ox·says:" where B has "el"
- insert: B adds "("
- replace: A has "." where B has ")"
- insert: B adds "."
- similarity: 0.8325
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_6c46f0da311e`). Flagged drifted duplicate: Capture B (`iu_f12f2d341680`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q41

Source: Savvas Practice #41 (lesson 5-4)
Capture A = `iu_77d25e1e6131` (line 299) &middot; Capture B = `iu_3c70a19c8d36` (line 328)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 299) | Capture B (line 328) |
|---|---|
| Make Sense and Persevere The half-life of a certain type of soft drink is 5 h. If you drink 50 mL of this drink, the formula y = 50(0.5)^{t/5} tells the amount of the drink left in your system after t hours. How much of the soft drink will be left in your system after 16 hours? | Make Sense and Persevere The half-life of a certain type of soft drink is 5 h. If you drink 50 mL of this drink, the formula (y=50(0.5)^{(t)/(5)}) tells the amount of the drink left in your system after (t) hours. How much of the soft drink will be left in your system after 16 hours? |

**Diff (exact)**

- replace: A has "y·" where B has "(y"
- delete: A has extra "·"
- replace: A has "t" where B has "(t)"
- replace: A has "5" where B has "(5)"
- replace: A has "·tells·the·amount·of·the·drink·left·in·your·system·after·t" where B has ")·tells·the·amount·of·the·drink·left·in·your·system·after·(t)"
- similarity: 0.7651
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_3c70a19c8d36`). Flagged drifted duplicate: Capture A (`iu_77d25e1e6131`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q42

Source: Savvas Practice #42 (lesson 5-4)
Capture A = `iu_0738f4d82434` (line 300) &middot; Capture B = `iu_3424ed062602` (line 329)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 300) | Capture B (line 329) |
|---|---|
| Model With Mathematics Big Ben's pendulum takes 4 s to swing back and forth. The formula t = 2π√((L)/(32)) gives the swing time, t, in seconds, based on the length of the pendulum, L, in feet. What is the minimum length necessary to build a clock with a pendulum that takes longer than Big Ben's pendulum to swing back and forth? | Model With Mathematics Big Ben's pendulum takes 4 s to swing back and forth. The formula (t=2π√((L)/(32))) gives the swing time, (t), in seconds, based on the length of the pendulum, (L), in feet. What is the minimum length necessary to build a clock with a pendulum that takes longer than Big Ben's pendulum to swing back and forth? |

**Diff (exact)**

- replace: A has "t·" where B has "(t"
- delete: A has extra "·"
- insert: B adds ")"
- replace: A has "t" where B has "(t)"
- insert: B adds "("
- insert: B adds ")"
- similarity: 0.9819
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_3424ed062602`). Flagged drifted duplicate: Capture A (`iu_0738f4d82434`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q43

Source: Savvas Practice #43 (lesson 5-4)
Capture A = `iu_9193a0f5443b` (line 301) &middot; Capture B = `iu_8624e125b308` (line 330)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 301) | Capture B (line 330) |
|---|---|
| Make Sense and Persevere Derek is hang gliding on a clear day. Use the formula for visibility, v = 1.225√(a) to find the altitude at which Derek is hang gliding.<br><br>[IMAGE: A person hang gliding. Labels say: "visibility, v = 67.1 miles" and "Distance to ground = a feet".] | Make Sense and Persevere Derek is hang gliding on a clear day. Use the formula for visibility, (v=1.225√(a)), to find the altitude at which Derek is hang gliding.<br><br>[IMAGE: Hang glider with labels "visibility, (v=67.1) miles" and "Distance to ground = (a) feet".] |

**Diff (exact)**

- replace: A has "v·" where B has "(v"
- delete: A has extra "·"
- insert: B adds "),"
- replace: A has "A·person·hang·gliding.·L" where B has "Hang·glider·with·l"
- delete: A has extra "·say:"
- replace: A has "v·" where B has "(v"
- delete: A has extra "·"
- insert: B adds ")"
- replace: A has "a" where B has "(a)"
- similarity: 0.8797
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_9193a0f5443b`). Flagged drifted duplicate: Capture B (`iu_8624e125b308`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q44

Source: Savvas Practice #44 (lesson 5-4)
Capture A = `iu_25b106c19a20` (line 302) &middot; Capture B = `iu_097a1fc43439` (line 331)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 302) | Capture B (line 331) |
|---|---|
| Complete the table to solve for the unknown value in the equation y = \sqrt[3]{2x + z} - 12, using the given values in each row.<br><br>\begin{center}<br>TABLE:<br> y \| x \| z <br><br>0 \| 462 \| -3 \| 439 <br><br>-10 \| 1.25 \| 3 \| 16<br>END_TABLE<br>\end{center} | Complete the table to solve for the unknown value in the equation (y=\sqrt[3]{2x+z}-12), using the given values in each row.<br><br>TABLE:<br> →prule<br>(y) \| (x) \| (z) \<br>\midrule<br>0 \| 462 \| (\square) \<br>-3 \| (\square) \| 439 \<br>-10 \| 1.25 \| (\square) \<br>3 \| (\square) \| 16 \<br>\bottomrule<br>END_TABLE |

**Diff (exact)**

- insert: B adds "("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "·12" where B has "12)"
- delete: A has extra "↵\begin{center}"
- insert: B adds "→prule↵("
- replace: A has "·|·" where B has ")·|·("
- replace: A has "·|·" where B has ")·|·("
- replace: A has "·↵" where B has ")·\↵\midrule"
- insert: B adds "(\square)·\↵"
- insert: B adds "(\square)·|·"
- replace: A has "↵" where B has "\"
- replace: A has "3" where B has "(\square)·\↵3·|·(\square)"
- insert: B adds "·\↵\bottomrule"
- delete: A has extra "↵\end{center}"
- similarity: 0.7165
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_097a1fc43439`). Flagged drifted duplicate: Capture A (`iu_25b106c19a20`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q45

Source: Savvas Practice #45 (lesson 5-4)
Capture A = `iu_57481c4ff850` (line 303) &middot; Capture B = `iu_b69ba77e28bf` (line 332)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 303) | Capture B (line 332) |
|---|---|
| SAT/ACT What is the solution to the equation (x^2 + 5x + 25)^{3/2} = 343?<br><br>\begin{itemize}<br> \item[A] -8 only<br> \item[B] 3 only<br> \item[C] 77 only<br> \item[D] -8 and 3<br> \item[E] There are no solutions.<br>\end{itemize} | SAT/ACT What is the solution to the equation ((x^2+5x+25)^{(3)/(2)}=343)?<br><br>A. (-8) only<br><br>B. 3 only<br><br>C. 77 only<br><br>D. (-8) and 3<br><br>E. There are no solutions. |

**Diff (exact)**

- insert: B adds "("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds "("
- insert: B adds ")"
- insert: B adds "("
- insert: B adds ")"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds ")"
- replace: A has "\begin{itemize}↵" where B has "A."
- replace: A has "\item[A]·" where B has "("
- insert: B adds ")"
- replace: A has "·\item[" where B has "↵"
- replace: A has "]" where B has "."
- replace: A has "·\item[" where B has "↵"
- replace: A has "]" where B has "."
- insert: B adds "↵D."
- replace: A has "\item[D]·" where B has "("
- insert: B adds ")"
- replace: A has "·\item[" where B has "↵"
- replace: A has "]" where B has "."
- delete: A has extra "↵\end{itemize}"
- similarity: 0.7273
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_57481c4ff850`). Flagged drifted duplicate: Capture B (`iu_b69ba77e28bf`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-4-savvas-q46

Source: Savvas Practice #46 (lesson 5-4)
Capture A = `iu_dbd1679d5bd4` (line 304) &middot; Capture B = `iu_25711dfdb66a` (line 333)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 304) | Capture B (line 333) |
|---|---|
| Performance Task Escape velocity is the velocity at which an object must be traveling to leave a star or planet without falling back to its surface or into orbit. Escape velocity depends on the gravitational constant, G = 6.67 × 10^{-11}, the mass, M in kilograms, and radius, r, of the star or planet.<br><br>\placeholder{illustration}{Earth with a rocket trajectory illustrating escape velocity. Labels: "Escape velocity: v = √((2GM)/(r))" and "Earth's radius = 6,371,000 m".}<br><br>Part A Rewrite the equation to solve for mass.<br><br>Part B Earth has an escape velocity of about 11,200 meters per second. What is Earth's mass in kilograms? | Performance Task Escape velocity is the velocity at which an object must be traveling to leave a star or planet without falling back to its surface or into orbit. Escape velocity depends on the gravitational constant, (G=6.67×10^{-11}), the mass, (M) in kilograms, and radius, (r), of the star or planet.<br><br>Escape velocity: (v=√((2GM)/(r)))<br><br>\placeholder{illustration}{Earth with a rocket path and labels "Escape velocity: (v=√((2GM)/(r)))" and "Earth's radius = 6,371,000 m".}<br><br>Part A Rewrite the equation to solve for mass.<br><br>Part B Earth has an escape velocity of about 11,200 meters per second. What is Earth's mass in kilograms? |

**Diff (exact)**

- insert: B adds "("
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has ",·the·mass,·" where B has "),·the·mass,·("
- insert: B adds ")"
- replace: A has "r" where B has "(r)"
- delete: A has extra "\placeholder{illustration}{Earth·with·a·rocket·trajectory·illustrating·escape·velocity.·Labels:·""
- replace: A has "v·" where B has "(v"
- delete: A has extra "·"
- insert: B adds ")↵↵\placeholder{illustration}{Earth·with·a·rocket·path·and·labels·"Escape·velocity:·(v=√((2GM)/(r)))"
- similarity: 0.8108
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_25711dfdb66a`). Flagged drifted duplicate: Capture A (`iu_dbd1679d5bd4`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

## Lesson 5-5

24 ambiguous groups in this lesson.

### 5-5-savvas-q24

Source: Savvas Practice #24 (lesson 5-5, anchors Example 4)
Capture A = `iu_b932d3aeba93` (line 403) &middot; Capture B = `iu_d2e75759490c` (line 427)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 403) | Capture B (line 427) |
|---|---|
| f(g(3)) | Let f(x)=4x-5 and g(x)=-7x. Evaluate each expression. SEE EXAMPLE 4<br><br>f(g(3)) |

**Diff (exact)**

- insert: B adds "Let·f(x)=4x-5·and·g(x)=-7x.·Evaluate·each·expression.·SEE·EXAMPLE·4↵↵"
- similarity: 0.1687
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_d2e75759490c`). Flagged drifted duplicate: Capture A (`iu_b932d3aeba93`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q25

Source: Savvas Practice #25 (lesson 5-5, anchors Example 4)
Capture A = `iu_b5a5c70c7c17` (line 404) &middot; Capture B = `iu_bdcbcee7b9b5` (line 428)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 404) | Capture B (line 428) |
|---|---|
| f(g(x)) | Let f(x)=4x-5 and g(x)=-7x. Evaluate each expression. SEE EXAMPLE 4<br><br>f(g(x)) |

**Diff (exact)**

- insert: B adds "Let·f(x)=4x-5·and·g(x)=-7x.·Evaluate·each·expression.·SEE·EXAMPLE·4↵↵"
- similarity: 0.1687
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_bdcbcee7b9b5`). Flagged drifted duplicate: Capture A (`iu_b5a5c70c7c17`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q26

Source: Savvas Practice #26 (lesson 5-5, anchors Example 4)
Capture A = `iu_72fd554985d6` (line 405) &middot; Capture B = `iu_c7787c4ca378` (line 429)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 405) | Capture B (line 429) |
|---|---|
| g(f(2)) | Let f(x)=4x-5 and g(x)=-7x. Evaluate each expression. SEE EXAMPLE 4<br><br>g(f(2)) |

**Diff (exact)**

- insert: B adds "Let·f(x)=4x-5·and·g(x)=-7x.·Evaluate·each·expression.·SEE·EXAMPLE·4↵↵"
- similarity: 0.1687
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_c7787c4ca378`). Flagged drifted duplicate: Capture A (`iu_72fd554985d6`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q27

Source: Savvas Practice #27 (lesson 5-5, anchors Example 4)
Capture A = `iu_608a20b54dee` (line 406) &middot; Capture B = `iu_0904446bcd4b` (line 430)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 406) | Capture B (line 430) |
|---|---|
| g(f(x)) | Let f(x)=4x-5 and g(x)=-7x. Evaluate each expression. SEE EXAMPLE 4<br><br>g(f(x)) |

**Diff (exact)**

- insert: B adds "Let·f(x)=4x-5·and·g(x)=-7x.·Evaluate·each·expression.·SEE·EXAMPLE·4↵↵"
- similarity: 0.1687
- drift: subset_relation

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_0904446bcd4b`). Flagged drifted duplicate: Capture A (`iu_608a20b54dee`). Confidence: high. Rationale: Capture B is the full item; the other is missing the instruction stem it prepends -- keep the complete capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q14

Source: Savvas Practice #14 (lesson 5-5, anchors Example 5)
Capture A = `iu_2eb8719c5989` (line 393) &middot; Capture B = `iu_d7b7148bc987` (line 417)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 393) | Capture B (line 417) |
|---|---|
| Error Analysis Describe and correct the error a student made in finding the rule for the composition f \circ g of the functions f(x) = 3x^2 - x + 2 and g(x) = 2x + 1.<br>\begin{align*}<br>f \circ g &= f(g(x)) <br>&= 3(2x + 1)^2 - 2x + 1 + 2 <br>&= 3(4x^2 + 4x + 1) - 2x + 1 + 2 <br>&= 12x^2 + 12x + 3 - 2x + 1 + 2 <br>&= 12x^2 + 10x + 6 \text{\Large \textcolor{red}{X}}<br>\end{align*} | Error Analysis Describe and correct the error a student made in finding the rule for the composition f\circ g of the functions f(x)=3x^2-x+2 and g(x)=2x+1.<br><br>\begin{aligned}<br>f\circ g&=f(g(x)) <br>&=3(2x+1)^2-2x+1+2 <br>&=3(4x^2+4x+1)-2x+1+2 <br>&=12x^2+12x+3-2x+1+2 <br>&=12x^2+10x+6<br>\end{aligned} |

**Diff (exact)**

- delete: A has extra "·"
- replace: A has "·=·3x^2·-·x·+·2·and·g(x)·=·2x·+·" where B has "=3x^2-x+2·and·g(x)=2x+"
- insert: B adds "↵"
- replace: A has "*" where B has "ed"
- replace: A has "·\circ·g·&=·f(g(x))·↵&=·3(2x·+·1)^2·-·2x·+·1·+·2·↵&=·" where B has "\circ·g&=f(g(x))·↵&=3(2x+1)^2-2x+1+2·↵&="
- replace: A has "·+·" where B has "+"
- replace: A has "·+·1)·-·2x·+·1·+·2·↵&=·12x^2·+·12x·+·3·-·2x·+·1·+·2·↵&=·12x^2·+·" where B has "+1)-2x+1+2·↵&=12x^2+12x+3-2x+1+2·↵&=12x^2+"
- replace: A has "·+·" where B has "+"
- replace: A has "·\text" where B has "↵\end"
- replace: A has "\Large·\textcolor{r" where B has "align"
- delete: A has extra "{X}}↵\end{align*}"
- similarity: 0.5093
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_2eb8719c5989`). Flagged drifted duplicate: Capture B (`iu_d7b7148bc987`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q15

Source: Savvas Practice #15 (lesson 5-5, anchors Example 5)
Capture A = `iu_712187c5c1fb` (line 394) &middot; Capture B = `iu_dca7798da065` (line 418)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 394) | Capture B (line 418) |
|---|---|
| Make Sense and Persevere Identify the rules for two functions, f(x) and g(x), for which f \circ g = g \circ f. | Make Sense and Persevere Identify the rules for two functions, f(x) and g(x), for which f\circ g=g\circ f. |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.9815
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_712187c5c1fb`). Flagged drifted duplicate: Capture B (`iu_dca7798da065`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q16

Source: Savvas Practice #16 (lesson 5-5, anchors Example 6)
Capture A = `iu_e73346a2c113` (line 395) &middot; Capture B = `iu_e22b2e7e6db5` (line 419)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 395) | Capture B (line 419) |
|---|---|
| Higher Order Thinking Suppose two functions, f(x) and g(x) are only defined by the ordered pairs listed below.<br><br>f = (6, 7), (5, 2), (4, 1), (10, 8)<br><br>g = (5, 4), (3, 6), (1, 5), (2, 10)<br><br>Find the ordered pairs that comprise (f \circ g)(x). | Higher Order Thinking Suppose two functions, f(x) and g(x) are only defined by the ordered pairs listed below.<br><br>f=\{(6,7),(5,2),(4,1),(10,8)\}<br><br>g=\{(5,4),(3,6),(1,5),(2,10)\}<br><br>Find the ordered pairs that comprise (f\circ g)(x). |

**Diff (exact)**

- delete: A has extra "·"
- replace: A has "·" where B has "\{"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "·1),·" where B has "1),"
- delete: A has extra "·"
- replace: A has "↵↵g·" where B has "\}↵↵g"
- replace: A has "·" where B has "\{"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "·(1,·" where B has "(1,"
- delete: A has extra "·"
- delete: A has extra "·"
- insert: B adds "\}"
- delete: A has extra "·"
- similarity: 0.9032
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_e73346a2c113`). Flagged drifted duplicate: Capture B (`iu_e22b2e7e6db5`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q18

Source: Savvas Practice #18 (lesson 5-5, anchors Example 4)
Capture A = `iu_23dc15b5d0d1` (line 397) &middot; Capture B = `iu_601b065ac8cb` (line 421)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 397) | Capture B (line 421) |
|---|---|
| Make Sense and Persevere Identify rules for two functions f(x) and g(x), for which f(g(x)) = x. | Make Sense and Persevere Identify rules for two functions f(x) and g(x), for which f(g(x))=x. |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.9894
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_23dc15b5d0d1`). Flagged drifted duplicate: Capture B (`iu_601b065ac8cb`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q19

Source: Savvas Practice #19 (lesson 5-5, anchors Example 1)
Capture A = `iu_93f8e94f1689` (line 398) &middot; Capture B = `iu_9a017c6f9c2d` (line 422)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 398) | Capture B (line 422) |
|---|---|
| Construct Arguments Is it possible that f(x) - g(x) = c, where c is a constant? If so, give an example. What must be true about two linear functions? If not, explain why it is not possible. | Construct Arguments Is it possible that f(x)-g(x)=c, where c is a constant? If so, give an example. What must be true about two linear functions? If not, explain why it is not possible. |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.9893
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_93f8e94f1689`). Flagged drifted duplicate: Capture B (`iu_9a017c6f9c2d`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q20

Source: Savvas Practice #20 (lesson 5-5, anchors Example 1)
Capture A = `iu_320c6ffc1dea` (line 399) &middot; Capture B = `iu_7bb19812dd74` (line 423)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 399) | Capture B (line 423) |
|---|---|
| f + g | Let f(x)=(5)/(3)x^2+2x-(5)/(8) and g(x)=3x^2. Identify the rules for the following functions. SEE EXAMPLE 1<br><br>f+g |

**Diff (exact)**

- insert: B adds "Let·"
- insert: B adds "(x)=(5)/(3)x^2+2x-(5)/(8)"
- replace: A has "+" where B has "and"
- insert: B adds "(x)=3x^2.·Identify·the·rules·for·the·following·functions.·SEE·EXAMPLE·1↵↵f+g"
- similarity: 0.0684
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_7bb19812dd74`). Flagged drifted duplicate: Capture A (`iu_320c6ffc1dea`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q21

Source: Savvas Practice #21 (lesson 5-5, anchors Example 1)
Capture A = `iu_a19e364d1fa4` (line 400) &middot; Capture B = `iu_4d9ab9a158c1` (line 424)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 400) | Capture B (line 424) |
|---|---|
| f - g | Let f(x)=(5)/(3)x^2+2x-(5)/(8) and g(x)=3x^2. Identify the rules for the following functions. SEE EXAMPLE 1<br><br>f-g |

**Diff (exact)**

- insert: B adds "Let·"
- insert: B adds "(x)=(5)/(3)x^2+2x-(5)/(8)"
- replace: A has "-" where B has "and"
- insert: B adds "(x)=3x^2.·Identify·the·rules·for·the·following·functions.·SEE·EXAMPLE·1↵↵f-g"
- similarity: 0.0684
- drift: latex_formatting

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_4d9ab9a158c1`). Flagged drifted duplicate: Capture A (`iu_a19e364d1fa4`). Confidence: medium. Rationale: Captures differ in LaTeX formatting (e.g. \frac vs (a)/(b)); suggested keep is the longer/cleaner capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q22

Source: Savvas Practice #22 (lesson 5-5, anchors Example 2)
Capture A = `iu_aca43fdbc779` (line 401) &middot; Capture B = `iu_35187501fd9b` (line 425)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 401) | Capture B (line 425) |
|---|---|
| Suppose the demand d, in units sold, for a company's jeans at price x, in dollars, is d(x) = 6,500 - 6.83x.<br>\begin{enumerate}<br>\item[a.] If revenue = price × demand, write the rule for the function R(x), which represent the company's expected revenue in jean sales. Then state the domain of this function.<br>\item[b.] If the cost to manufacture the jeans is c(x) = 386 + 1.27x, find the equation for the company's profit. How much does the company earn if the price is $79?<br>\end{enumerate}<br>\textsc{SEE EXAMPLE 2} | Suppose the demand d, in units sold, for a company's jeans at price x, in dollars, is d(x)=6{,}500-6.83x.<br><br>a. If revenue = price × demand, write the rule for the function R(x), which represents the company's expected revenue in jean sales. Then state the domain of this function.<br><br>b. If the cost to manufacture the jeans is c(x)=386+1.27x, find the equation for the company's profit. How much does the company earn if the price is $79? SEE EXAMPLE 2 |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "," where B has "{,}"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "\begin{enumerate}"
- replace: A has "\item[a.]" where B has "a."
- insert: B adds "s"
- replace: A has "\item[" where B has "↵"
- delete: A has extra "]"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "↵\end{enumerate}↵\textsc{" where B has "·"
- delete: A has extra "}"
- similarity: 0.9207
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_aca43fdbc779`). Flagged drifted duplicate: Capture B (`iu_35187501fd9b`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q23

Source: Savvas Practice #23 (lesson 5-5, anchors Example 3)
Capture A = `iu_5779e311d71a` (line 402) &middot; Capture B = `iu_54a767de4d10` (line 426)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 402) | Capture B (line 426) |
|---|---|
| Identify the rule and domain for (f)/(g) when f(x) = 10x^2 + 3x - 18 and g(x) = 2x + 3. \textsc{SEE EXAMPLE 3} | Identify the rule and domain for (f)/(g) when f(x)=10x^2+3x-18 and g(x)=2x+3. SEE EXAMPLE 3 |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "\textsc{"
- delete: A has extra "}"
- similarity: 0.9055
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_5779e311d71a`). Flagged drifted duplicate: Capture B (`iu_54a767de4d10`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q28

Source: Savvas Practice #28 (lesson 5-5, anchors Example 5)
Capture A = `iu_8f4fd3daf3b5` (line 407) &middot; Capture B = `iu_840acea52a12` (line 431)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 407) | Capture B (line 431) |
|---|---|
| f \circ g | Let f(x)=x^2+x and g(x)=9-2x. Identify the rules for the following functions. SEE EXAMPLE 5<br><br>f\circ g |

**Diff (exact)**

- insert: B adds "Let·"
- insert: B adds "(x)=x^2+x"
- insert: B adds "and·g(x)=9-2x.·Identify·the·rules·for·the·following·functions.·SEE·EXAMPLE·5↵↵f"
- similarity: 0.1636
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_840acea52a12`). Flagged drifted duplicate: Capture A (`iu_8f4fd3daf3b5`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q29

Source: Savvas Practice #29 (lesson 5-5, anchors Example 5)
Capture A = `iu_efa33334f2ae` (line 408) &middot; Capture B = `iu_c6efaa1c9bcf` (line 432)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 408) | Capture B (line 432) |
|---|---|
| g \circ f | Let f(x)=x^2+x and g(x)=9-2x. Identify the rules for the following functions. SEE EXAMPLE 5<br><br>g\circ f |

**Diff (exact)**

- insert: B adds "Let·f(x)=x^2+x·and·g(x)=9-2x.·Identify·the·rules·for·the·followin"
- insert: B adds "functions.·SEE·EXAMPLE·5↵↵g"
- similarity: 0.1636
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture B** (`iu_c6efaa1c9bcf`). Flagged drifted duplicate: Capture A (`iu_efa33334f2ae`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q30

Source: Savvas Practice #30 (lesson 5-5, anchors Example 5)
Capture A = `iu_cf23896a9943` (line 409) &middot; Capture B = `iu_9ac353bdcbb0` (line 433)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 409) | Capture B (line 433) |
|---|---|
| A sporting goods store is running a summer sale on its snowboards. Kadia is interested in a snowboard that normally costs $400. The store is offering two special offers.<br><br>In which order should these special offers be applied to the cost of the snowboard in order to benefit Kadia? Explain. \textsc{SEE EXAMPLE 6}<br><br>[IMAGE: Snowboards on display in a store, with two circular stickers indicating offers: "$50 INSTANT REBATE" and "10% DISCOUNT".] | A sporting goods store is running a summer sale on its snowboards. Kadia is interested in a snowboard that normally costs $400. The store is offering two special offers.<br><br>[IMAGE: Snowboards in a store with two circular labels: ``$50 INSTANT REBATE'' and ``10% DISCOUNT.'']<br><br>In which order should these special offers be applied to the cost of the snowboard in order to benefit Kadia? Explain. SEE EXAMPLE 6 |

**Diff (exact)**

- delete: A has extra "↵↵In·which·order·should·these·special·offers·be·applied·to·the·cost·of·the·snowboard·in·order·to·benefit·Kadia?·Explain.·\textsc{SEE·EXAMPLE·6}"
- replace: A has "on·display·in·a·store," where B has "in·a·store"
- replace: A has "stickers·indicating·offer" where B has "label"
- replace: A has """ where B has "``"
- replace: A has ""·and·"" where B has "''·and·``"
- delete: A has extra """
- insert: B adds "''"
- insert: B adds "↵↵In·which·order·should·these·special·offers·be·applied·to·the·cost·of·the·snowboard·in·order·to·benefit·Kadia?·Explain.·SEE·EXAMPLE·6"
- similarity: 0.5748
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_cf23896a9943`). Flagged drifted duplicate: Capture B (`iu_9ac353bdcbb0`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q31

Source: Savvas Practice #31 (lesson 5-5, anchors Example 4)
Capture A = `iu_28b458c2125a` (line 410) &middot; Capture B = `iu_f1ef8ada04a3` (line 434)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 410) | Capture B (line 434) |
|---|---|
| Model With Mathematics The cost (in dollars) to produce x shovels in a factory is given by the function C(x) = 20x + 500. The factory produces 30 shovels in one hour.<br>\begin{enumerate}<br>\item[a.] Find the rule for C(h(x)), where the function h(x) is the number of shovels produced in x hours.<br>\item[b.] Find the cost when h = 8 hours.<br>\item[c.] Explain what the function C(h(x)) represents.<br>\end{enumerate} | Model With Mathematics The cost (in dollars) to produce x shovels in a factory is given by the function C(x)=20x+500. The factory produces 30 shovels in one hour.<br><br>a. Find the rule for C(h(x)), where the function h(x) is the number of shovels produced in x hours.<br><br>b. Find the cost when h=8 hours.<br><br>c. Explain what the function C(h(x)) represents. |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "\begin{enumerate}↵\item[a.]" where B has "↵a."
- replace: A has "\item[" where B has "↵"
- delete: A has extra "]"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "\item[c.]" where B has "↵c."
- delete: A has extra "↵\end{enumerate}"
- similarity: 0.9043
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_28b458c2125a`). Flagged drifted duplicate: Capture B (`iu_f1ef8ada04a3`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q32

Source: Savvas Practice #32 (lesson 5-5, anchors Example 6)
Capture A = `iu_2b9db35c3599` (line 411) &middot; Capture B = `iu_3ff5b496521b` (line 435)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 411) | Capture B (line 435) |
|---|---|
| Use Structure A music store is running the following promotions.<br><br>[IMAGE: A drum set with a sign: "HUGE SAVINGS AT O'RILEY'S MUSIC". Coupons show "$5 off a purchase of $20 or more" and "Save an additional 15% off your total purchase when you open a charge account".]<br><br>\begin{enumerate}<br>\item[a.] Use composition of functions to find the sale price of a $90 purchase when the $5 off discount is applied prior to the 15% off discount.<br>\item[b.] Use composition of functions to find the sale price of a $90 purchase when the 15% off discount is applied prior to the $5 off discount.<br>\item[c.] In which order is the deal better for the consumer? Explain.<br>\end{enumerate} | Use Structure A music store is running the following promotions.<br><br>[IMAGE: Promotional ad reading ``HUGE SAVINGS AT O'RILEY'S MUSIC,'' ``$5 off a purchase of $20 or more,'' and ``Save an additional 15% off your total purchase when you open a charge account.'']<br><br>a. Use composition of functions to find the sale price of a $90 purchase when the $5 off discount is applied prior to the 15% off discount.<br><br>b. Use composition of functions to find the sale price of a $90 purchase when the 15% off discount is applied prior to the $5 off discount.<br><br>c. In which order is the deal better for the consumer? Explain. |

**Diff (exact)**

- replace: A has "A·dru" where B has "Pro"
- replace: A has "·set·with·a·si" where B has "otional·ad·readin"
- replace: A has "n:·"" where B has "·``"
- replace: A has "".·Coupons·show·"" where B has ",''·``"
- replace: A has ""·and·"" where B has ",''·and·``"
- replace: A has ""." where B has ".''"
- replace: A has "\begin{enumerate}↵\item[a.]" where B has "a."
- replace: A has "\item[" where B has "↵"
- delete: A has extra "]"
- replace: A has "\item[c.]" where B has "↵c."
- delete: A has extra "↵\end{enumerate}"
- similarity: 0.8774
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_2b9db35c3599`). Flagged drifted duplicate: Capture B (`iu_3ff5b496521b`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q33

Source: Savvas Practice #33 (lesson 5-5, anchors Example 1)
Capture A = `iu_033c2e43234f` (line 412) &middot; Capture B = `iu_6afc7f93a29c` (line 436)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 412) | Capture B (line 436) |
|---|---|
| Reason From 2000 to 2015, the number of births, b, (in the hundreds) in Fairfield County can be modeled by the function b(x) = 300 - 5x. The number of deaths, d, (in the hundreds) can be modeled by the function d(x) = 10x + 5. The variable x represents the number of years since 2000.<br>\begin{enumerate}<br>\item[a.] Which function operation can be used to represent the net increase in the population?<br>\item[b.] Write and simplify a function which represents the net increase in the population, p, against x, the number of years since 2000. State the domain of this function.<br>\end{enumerate} | Reason From 2000 to 2015, the number of births, b, in the hundreds, in Fairfield County can be modeled by the function b(x)=300-5x. The number of deaths, d, in the hundreds, can be modeled by the function d(x)=10x+5. The variable x represents the number of years since 2000.<br><br>a. Which function operation can be used to represent the net increase in the population?<br><br>b. Write and simplify a function which represents the net increase in the population, p, against x, the number of years since 2000. State the domain of this function. |

**Diff (exact)**

- replace: A has "(in·the·hundreds)" where B has "in·the·hundreds,"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- replace: A has "(in·the·hundreds)" where B has "in·the·hundreds,"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "\begin{enumerate}"
- replace: A has "\item[a.]" where B has "a."
- replace: A has "\item[b.]" where B has "↵b."
- delete: A has extra "↵\end{enumerate}"
- similarity: 0.8839
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_033c2e43234f`). Flagged drifted duplicate: Capture B (`iu_6afc7f93a29c`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q34

Source: Savvas Practice #34 (lesson 5-5, anchors Example 5)
Capture A = `iu_0d5ac07fb4cb` (line 413) &middot; Capture B = `iu_1f21f0032276` (line 437)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 413) | Capture B (line 437) |
|---|---|
| Given that f(x) = x^2 + 8x + 3 and g(x) = -x - 7, which of the following are true? Select all that apply.<br>\begin{itemize}<br>\item[\square] f + g = x^2 + 7x - 4<br>\item[\square] f(g(x)) = x^2 + 6x - 4<br>\item[\square] The domain of (f)/(g) is the set of all real numbers.<br>\item[\square] f(x) · g(x) = -x^3 - 15x^2 + 53x + 21<br>\item[\square] In the composition g \circ f, the output f(x) is used as the input for g.<br>\end{itemize} | Given that f(x)=x^2+8x+3 and g(x)=-x-7, which of the following are true? Select all that apply.<br><br>\square f+g=x^2+7x-4<br><br>\square f(g(x))=x^2+6x-4<br><br>\square The domain of (f)/(g) is the set of all real numbers.<br><br>\square f(x)· g(x)=-x^3-15x^2+53x+21<br><br>\square In the composition g\circ f, the output f(x) is used as the input for g. |

**Diff (exact)**

- replace: A has "·=·x^2·+·" where B has "=x^2+"
- replace: A has "·+·" where B has "+"
- replace: A has "·=·-x·-·" where B has "=-x-"
- replace: A has "\begin{itemize}↵\item[\square]·f·+·g·=·x^2·+·" where B has "↵\square·f+g=x^2+"
- replace: A has "·-·" where B has "-"
- replace: A has "\item[\square]·f(g(x))·=·x^2·+·" where B has "↵\square·f(g(x))=x^2+"
- replace: A has "·-·" where B has "-"
- replace: A has "\item[\square]" where B has "↵\square"
- replace: A has "\item[\square]·f(x)·" where B has "↵\square·f(x)"
- replace: A has "·=·" where B has "="
- replace: A has "·-·" where B has "-"
- replace: A has "·+·" where B has "+"
- replace: A has "·+·" where B has "+"
- replace: A has "\ite" where B has "↵\square·In·the·co"
- replace: A has "[\square]·In·the·composition·g·" where B has "position·g"
- delete: A has extra "↵\end{itemize}"
- similarity: 0.5979
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_0d5ac07fb4cb`). Flagged drifted duplicate: Capture B (`iu_1f21f0032276`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q35

Source: Savvas Practice #35 (lesson 5-5, anchors Example 4)
Capture A = `iu_f095b03d1f03` (line 414) &middot; Capture B = `iu_24bbbfa249d0` (line 438)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 414) | Capture B (line 438) |
|---|---|
| SAT/ACT Find the value of f(g(5)) if f(x) = 4x + 1 and g(x) = x^2 + 6.<br><br>\textcircled{A} 101 \textcircled{B} 124 \textcircled{C} 125 \textcircled{D} 676 \textcircled{E} 682 | SAT/ACT Find the value of f(g(5)) if f(x)=4x+1 and g(x)=x^2+6.<br><br>A 101 B 124 C 125 D 676 E 682 |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "·"
- delete: A has extra "\textcircled{"
- delete: A has extra "}"
- delete: A has extra "\textcircled{"
- delete: A has extra "}"
- delete: A has extra "\textcircled{"
- delete: A has extra "}"
- delete: A has extra "\textcircled{"
- delete: A has extra "}"
- delete: A has extra "\textcircled{"
- delete: A has extra "}"
- similarity: 0.7045
- drift: other_textual

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_f095b03d1f03`). Flagged drifted duplicate: Capture B (`iu_24bbbfa249d0`). Confidence: medium. Rationale: Same slot re-captured with textual drift; suggested keep is the more complete (longer) capture.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q36

Source: Savvas Practice #36 (lesson 5-5, anchors Example 4)
Capture A = `iu_b5f838fc172a` (line 415) &middot; Capture B = `iu_a11fd8fd0f3a` (line 439)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 415) | Capture B (line 439) |
|---|---|
| Performance Task The temperature in degrees Celsius is 32 less than the Fahrenheit temperature, multiplied by five-ninths. The temperature in degrees Kelvin is the number of degrees Celsius plus 273.<br><br>[IMAGE: Three vertical thermometers side-by-side labeled Celsius, ^\circC, Fahrenheit, ^\circF, and Kelvin, K. A red dashed line horizontally connects 0^\circC, 32^\circF, and 273 K. The Celsius scale has markings from -40 to 60. The Fahrenheit scale has markings from -50 to 150. The Kelvin scale has markings from 230 to 330.]<br><br>Part A Derive a conversion formula for finding the number of degrees Kelvin, given the temperature in Fahrenheit.<br><br>Part B Using your conversion formula from part (a), find the temperature in degrees Kelvin when the temperature is 27^\circF. Round to the nearest whole number if necessary. | Performance Task The temperature in degrees Celsius is 32 less than the Fahrenheit temperature, multiplied by five-ninths. The temperature in degrees Kelvin is the number of degrees Celsius plus 273.<br><br>[GRAPH / TIKZ figure]<br><br>Part A Derive a conversion formula for finding the number of degrees Kelvin, given the temperature in Fahrenheit.<br><br>Part B Using your conversion formula from part (a), find the temperature in degrees Kelvin when the temperature is 27^{\circ}F. Round to the nearest whole number if necessary. |

**Diff (exact)**

- insert: B adds "GRAPH·/·T"
- delete: A has extra "MAGE:·Three·vertical·thermometers·side-by-side·labeled·Celsius,·^\circC,·Fahrenheit,·^\circF,·and·"
- replace: A has "elvin,·K.·A·red·dashed·line·horizontally·connects·0^\circC,·32^\circF,·and·273·K.·The·Celsius·scale·has·markings·from·-40·to·60.·The·Fahrenheit·scale·has·markings·from·-50·to·150.·The·Kelvin·scale·has·markings·from·230·to·330." where B has "Z·figure"
- insert: B adds "{"
- insert: B adds "}"
- similarity: 0.7427
- drift: visual_encoding

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_b5f838fc172a`). Flagged drifted duplicate: Capture B (`iu_a11fd8fd0f3a`). Confidence: medium. Rationale: Captures differ in how the visual is encoded (\placeholder vs [IMAGE:]/[GRAPH/TIKZ]) -- suggested keep is the longer capture; reviewer confirm which visual form the pipeline wants.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q12

Source: Savvas Practice #12 (lesson 5-5, anchors Example 5)
Capture A = `iu_0019c0da1a39` (line 391) &middot; Capture B = `iu_a395c491685e` (line 416)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 391) | Capture B (line 416) |
|---|---|
| Generalize Does f \circ g always equal g \circ f? Justify your response. | Generalize Does f\circ g always equal g\circ f? Justify your response. |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.9859
- drift: circ_spacing

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_0019c0da1a39`). Flagged drifted duplicate: Capture B (`iu_a395c491685e`). Confidence: low. Rationale: Cosmetic drift only (whitespace/\circ spacing); text is identical after normalization -- either is acceptable, suggested keep is the A capture; reviewer's call.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

### 5-5-savvas-q17

Source: Savvas Practice #17 (lesson 5-5, anchors Example 5)
Capture A = `iu_cf8c651a572d` (line 396) &middot; Capture B = `iu_fc03297ecf37` (line 420)
Both item_uids are retained -- nothing is merged.

**Side-by-side prompts**

| Capture A (line 396) | Capture B (line 420) |
|---|---|
| Mathematical Connections Relate evaluating (f \circ g)(3) to finding the composition rule (f \circ g)(x). What are the benefits of each? | Mathematical Connections Relate evaluating (f\circ g)(3) to finding the composition rule (f\circ g)(x). What are the benefits of each? |

**Diff (exact)**

- delete: A has extra "·"
- delete: A has extra "·"
- similarity: 0.9926
- drift: circ_spacing

**Recommendation**

Suggested canonical keep: **Capture A** (`iu_cf8c651a572d`). Flagged drifted duplicate: Capture B (`iu_fc03297ecf37`). Confidence: low. Rationale: Cosmetic drift only (whitespace/\circ spacing); text is identical after normalization -- either is acceptable, suggested keep is the A capture; reviewer's call.
Advisory -- final decision is the teacher's; both uids stay live until the teacher acts.

**Decision**

- [ ] Keep Capture A as canonical, retire B
- [ ] Keep Capture B as canonical, retire A
- [ ] Keep BOTH (distinct items)
- [ ] Other / needs SME
- Notes: ____

