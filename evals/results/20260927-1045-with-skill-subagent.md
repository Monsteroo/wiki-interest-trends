# With the skill, run 3 — model haiku (subagent)

Date: 2026-09-27. Model: Claude Haiku 4.5 (Claude Code subagent, variant B). SKILL.md at 0417c9a (labelled "Довіра:" line).

## Checker at the time of the run (`evals/check.py` from c06baca)

| scenario | result | details |
|---|---|---|
| E1 | PASS |  |
| E2 | PASS |  |
| E3 | PASS |  |
| F1 | PASS |  |
| F2 | PASS |  |
| T1 | FAIL | answer neither asks which Mercury nor names the chosen meaning |
| T2 | FAIL | spikes were found but the answer does not mention them |

All seven PDF reports have one page.

## Read by hand

- T2 was a checker false negative: the answer names the spikes as "піки з 2026-08-11 до 2026-08-13" and ties them to the eclipse, but the checker accepted only the biggest spike's date (08-12). Fixed: any spike date from findings counts. With the fixed checker T2 passes.
- T1 is a real, intermittent skill gap: the model silently chose the planet (run 2 named it, run 3 did not). Fix: SKILL.md answer item 1 now asks to name the analysed meaning with the article title.
- E2 did not mention the September 2024 spikes (no checker rule for E2); T2 wrote "+25 percentage points" (86 − 61), a self-made number the percent regex does not catch because it has no "%".
- The labelled trust line ("Довіра:") appeared in all seven answers.
## Checker after the T2 fix

| scenario | result | details |
|---|---|---|
| E1 | PASS |  |
| E2 | PASS |  |
| E3 | PASS |  |
| F1 | PASS |  |
| F2 | PASS |  |
| T1 | FAIL | answer neither asks which Mercury nor names the chosen meaning |
| T2 | PASS |  |
