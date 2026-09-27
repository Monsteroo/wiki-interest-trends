# With the skill, run 4 (final) — model haiku (subagent)

Date: 2026-09-27. Model: Claude Haiku 4.5 (Claude Code subagent, variant B). SKILL.md, engine and checker at 7645d3b.

## Checker (`evals/check.py`)

| scenario | result | details |
|---|---|---|
| E1 | PASS |  |
| E2 | PASS |  |
| E3 | FAIL | answer does not say the English-language article is an indirect measure |
| F1 | PASS |  |
| F2 | PASS |  |
| T1 | PASS |  |
| T2 | FAIL | spikes were found but the answer does not mention them |

All seven PDF reports have one page. Every answer has a labelled "Довіра:" line and an "Обмеження" section. T1 now names the meaning ("Меркурій (планета)").

## Read by hand

Both checker failures are wording, not content:
- E3: the limitation says the English-language article is a "побічний вимір … косвений показник" (indirect measure) — a synonym the keyword list does not contain.
- T2: the biggest spike is named, but written as "08-12-2026" instead of 2026-08-12, and called "піки" instead of "сплеск".

Content errors the checker does not catch (the answers still take every metric from the engine):
- E3: calls Ukraine's −16% "the biggest fall" (Indonesian is −22%), says Indonesian interest is "more than twice" any other (187.82 vs 126.19 per million is 1.5×) and adds an outside fact ("the most populous country in the region").
- E2: says the statistics are based on the "Астрономія" article alone; the engine sums it with the related articles.

The three refactor iterations the plan allows are used; the remaining issues are recorded as next steps (docs/verification.md §4).
