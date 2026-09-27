# With the skill, run 2 — model haiku (subagent)

Date: 2026-09-27. Model: Claude Haiku 4.5 (Claude Code subagent, variant B). SKILL.md and engine at c06baca (spikes and seasonal uplift in the run summary; answer rules for spikes, a labelled limitation, no self-made percentages; stricter T2 check).

## Checker (`evals/check.py`)

| scenario | result | details |
|---|---|---|
| E1 | PASS |  |
| E2 | PASS |  |
| E3 | PASS |  |
| F1 | PASS |  |
| F2 | PASS |  |
| T1 | FAIL | answer does not state trust |
| T2 | FAIL | answer does not state trust |

All seven PDF reports have one page.

## Read by hand

- T2 now names the spike (2026-08-11..13, the eclipse) and advises re-checking in 3–6 months; no self-made percentages anywhere.
- T1 and T2 fail only because the trust level was written as "Надійність: висока" — correct content, a word the checker does not know. Fix for run 3: SKILL.md asks for labelled lines "Довіра:" / "Trust:" like "Обмеження:".
- Known methodology limit (roadmap v2): the engine caps single spike days, but a month-long event surge (Spanish "Eclipse solar", August 2026: 78 300 views against ~16 000 typical) still counts as growth with high trust. The answer now warns about it; the trust rule itself does not yet.
