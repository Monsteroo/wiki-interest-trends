# With the skill, run 1 — model haiku (subagent)

Date: 2026-09-27. Model: Claude Haiku 4.5 (Claude Code subagent, variant B). Prompt: `evals/subagent_prompt.md` with the skill block. SKILL.md at 31507b8.

## Checker (`evals/check.py`)

| scenario | result | details |
|---|---|---|
| E1 | PASS |  |
| E2 | FAIL | answer names no limitation; percentages not found in findings: [71] |
| E3 | PASS |  |
| F1 | PASS |  |
| F2 | PASS |  |
| T1 | PASS |  |
| T2 | FAIL | percentages not found in findings: [75] |

## Read by hand

- E1/F1: reports that Polish (and Slovak) Wikipedia has no article instead of taking a wrong one; Czech −48% YoY, medium trust.
- E2: −36% share / −53% views for astronomy + 3 related articles. Checked independently: the raw monthly API sums for the 4 articles give 64 423 → 30 069 views (−53.3%); the 4-view gap is the one redirect the skill adds.
- E2 fail: "71%" is the seasonal uplift from findings.json (an engine number the run summary does not print); the limitation was written in the model's own words, none of the checker's keywords.
- T1: picked the planet (Q308) and said so; −12% YoY, high trust.
- T2 fail: "75%" is the model's own arithmetic (9 of 12 months). Worse, not caught by the checker: August 2026 has 78 300 views (the total solar eclipse over Spain on 2026-08-12, spikes on 08-11..13 in findings.json), yet the answer says the growth "is not the result of one-off events". The run summary does not print spikes, so the model could not see them.

Changes for run 2: print spike dates and the seasonal uplift in the run summary; SKILL.md rules for spikes, for a labelled limitation and against turning counts into percentages; stricter T2 check.
