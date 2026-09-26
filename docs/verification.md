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

## 4. Full scenario on Claude Haiku 4.5
Filled in after the eval runs (Task 18).

## 5. How AI tools were used
- Claude (Opus) was used for brainstorming, the architecture decision, the specification, the plan and the code, following test-driven development.
- Every factual claim about external APIs was verified with live requests before it shaped the design; claims that failed (for example, that Wikidata "subclass of" yields reader-relevant related topics) were dropped.
- Every rule is covered by a test that was seen failing first; generated PDFs and charts were reviewed visually.
- The agent-facing part (SKILL.md) was checked by running the case scenarios on a cheap model and comparing the answers with the computed findings.
