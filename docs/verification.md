# Verification

How the results of this skill, and of the AI tools used to build it, were checked.

## 1. Design claims checked against live data (2026-09-24…26)
- The first case example hides a trap: Wikidata Q1666254 (intermittent fasting) has cs/uk/en/de articles but no Polish one. The skill reports the gap instead of comparing different things.
- A monthly request ending mid-month returns a partial last month (end=2025-04-01 gave April = 732 views vs ~20,000 in other months), so the skill uses complete months only.
- The API omits zero-view days and answers 404 for "zero or not loaded"; the skill fills zeros.
- Views of redirects are not counted in the target article; the skill adds up to 10 redirects.
- Rate limits (2026): 10 requests/min without an identifying User-Agent, 200/min with one, at most 3 concurrent; the skill sends sequential requests with a contact User-Agent and caches responses.
- An alternative architecture was evaluated against data before rejecting it (Wikidata SPARQL "subclass of" suggestions, edit-war index, `pytrends`, WeasyPrint): see [ADR-001](adr/0001-architecture.md).

## 2. Tests written before code
Every module was built test-first (red → green → refactor), see the commit history. Unit tests use synthetic series with known answers for every rule and threshold (for example 99 vs 100 views). Acceptance tests run the three case scenarios end to end on recorded, complete API responses (`tests/fixtures/http/`).

```bash
.venv/bin/python -m pytest          # offline suite
.venv/bin/python -m pytest -m live  # against the real API
```

## 3. Independent cross-check of numbers
Output of `tests/live/crosscheck.py` (daily sums used by the skill vs the API's own monthly totals):

| article | our sum of daily views | API monthly total | match | manual check |
|---|---|---|---|---|
| cs: Přerušovaný půst | 2198 | 2198 | yes | [pageviews.wmcloud.org](https://pageviews.wmcloud.org/?project=cs.wikipedia.org&platform=all-access&agent=user&redirects=0&start=2025-09-01&end=2026-08-31&pages=P%C5%99eru%C5%A1ovan%C3%BD_p%C5%AFst) |
| uk: Астрономія | 6708 | 6708 | yes | [pageviews.wmcloud.org](https://pageviews.wmcloud.org/?project=uk.wikipedia.org&platform=all-access&agent=user&redirects=0&start=2025-09-01&end=2026-08-31&pages=%D0%90%D1%81%D1%82%D1%80%D0%BE%D0%BD%D0%BE%D0%BC%D1%96%D1%8F) |
| pl: Język angielski | 97042 | 97042 | yes | [pageviews.wmcloud.org](https://pageviews.wmcloud.org/?project=pl.wikipedia.org&platform=all-access&agent=user&redirects=0&start=2025-09-01&end=2026-08-31&pages=J%C4%99zyk_angielski) |

Manual check on pageviews.wmcloud.org for the first row (2026-09-26, daily data, all platforms, agent = user, redirects not included, 2025-09-01 – 2026-08-31): the tool reports 2 198 views for «Přerušovaný půst» — identical to the skill's 2198.

This cross-check covers downloading and summing. Share per million, growth, trust and seasonality rest on the unit tests (synthetic series with known answers) and on the E2 hand check in §4.

## 4. Full scenario on Claude Haiku 4.5
Seven scenarios (`evals/scenarios.json`): the three case examples E1–E3, follow-ups F1 ("add Slovak") and F2 ("growth matters more than size"), an ambiguous topic T1 (Mercury) and an event-driven topic T2 (solar eclipses). Each ran in a fresh Claude Code subagent on Claude Haiku 4.5 whose prompt announced the installed skill with its name and description (`evals/subagent_prompt.md`), so activation by description was simulated, not tested; the baseline got the same prompt without that block; `evals/check.py` checks the artifacts and the answer, and every answer was also read by hand. Raw tables: `evals/results/`.

| run | skill version | checker | what changed after it |
|---|---|---|---|
| baseline, no skill | — | 0/7 (by construction: only the skill writes `study.json`) | wrong articles (Polish "therapeutic fasting", Slovak religious "Pôst"), invented numbers ("Ukraine +14%", "reliability 97/100"), no report |
| 1 | 31507b8 | 5/7 | run summary now prints spike dates and the seasonal uplift; SKILL.md rules for spikes, a labelled limitation, no self-made percentages |
| 2 | c06baca | 5/7 | SKILL.md asks for a labelled "Довіра:" line |
| 3 | 0417c9a | 5/7 (6/7 with the corrected T2 check) | SKILL.md asks to name the analysed meaning; the T2 check accepts any spike date |
| 4 | 7645d3b | 5/7 | — (the two failures are wording: a synonym for "indirect", a date written as 08-12-2026) |

Numbers in the answers were checked against the engine and, for E2, against the raw API: the four astronomy articles sum to 64 423 → 30 069 views, −53.3%, the same as the skill (the 4-view gap is the one redirect it adds).

What the evals found in the engine, not only in the text: the Spanish "Eclipse solar" had 78 300 views in August 2026 (the total eclipse over Spain on 12 August) against about 16 000 in a typical month. The engine caps single spike days, so a month-long event surge still counts as growth with high trust. The answer now warns about it; the trust rule is on the roadmap (v2).

Still open after the three iterations the plan allows: Haiku sometimes adds comparisons of its own ("more than twice" for 1.5×), an outside fact, or paraphrases the limitation in words the checker does not know. Next steps: have the engine print ready-made comparison sentences, and replace keyword checks with a small rubric graded by a second model.

## 5. How AI tools were used
- **Design (Claude Opus 5.5):** brainstorming, the architecture decision (ADR-001), the specification and the 19-task test-first plan. Every factual claim about external APIs was verified with live requests before it shaped the design; claims that failed (for example, that Wikidata "subclass of" yields reader-relevant related topics) were dropped.
- **Implementation (subagents):** each task was implemented by a separate subagent from a written brief — Claude Haiku 4.5 for tasks that transcribe fully specified code, Claude Sonnet 5 for integration work (commit trailers: 13 Haiku 4.5, 13 Sonnet 5, 9 Opus 5.5 for docs, eval results and small controller fixes).
- **Review:** every task was reviewed by a different subagent against the spec and the brief, reading the diff, not the implementer's report; implementer claims (test counts, outputs) were re-run by the controller, and two reports with wrong numbers were caught that way. Every Important finding that changed behaviour went to the user for a decision (for example: two-page reports instead of clipping, font floors, Python ≥ 3.12 in the wrapper). A final whole-branch review by Claude Opus found four more issues, fixed before release.
- **Tests:** every rule is covered by a test that was seen failing first; generated PDFs and charts were reviewed visually.
- **The agent-facing part (SKILL.md)** was checked by running the case scenarios on Claude Haiku 4.5 and comparing the answers with the computed findings (§4).
