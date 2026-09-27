# wiki-interest-trends

An [Agent Skill](https://agentskills.io/specification) that helps B2C founders decide which topics to build and which languages to launch in, using Wikipedia pageviews. The agent turns a question into a small study form; the skill's Python code downloads the data, computes growth and how far to trust it, finds seasonality, ranks audiences by your priorities and produces charts plus a PDF report that fits on one page (two only if the content does not fit).

Designed and tested for a cheap, fast model (Claude Haiku 4.5): the agent makes one decision (the form) and writes the conclusion; every number comes from the code.

## Install
Requires Python 3.12+ and internet access.

```bash
git clone https://github.com/Monsteroo/wiki-interest-trends ~/.claude/skills/wiki-interest-trends
```
or clone into `<project>/.claude/skills/`. On first use `scripts/wit` either runs through `uv` or creates a pinned virtualenv in `~/.cache/wiki-interest-trends/` (about a minute). Optional: `export WIT_CONTACT=<your email or URL>` for the Wikimedia User-Agent.

## Try it
Ask your agent, for example:
- «Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.»
- «Ми думаємо додати курс з астрономії. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?»
- «Порівняй інтерес до вивчення англійської в польській, чеській, українській, турецькій та індонезійській Wikipedia: які аудиторії варто дослідити наступними й чому?»

Or run it yourself:
```bash
scripts/wit resolve "intermittent fasting" --langs pl,cs --question "Compare interest in pl and cs" --save wiki-studies/fasting
scripts/wit run wiki-studies/fasting
```

## How it works
```
question → agent → scripts/wit resolve  (Wikidata topic, article per language, substitutes, related topics)
                 → study.json            (the assumptions, editable for follow-ups)
                 → scripts/wit run       (data → growth, trust, seasonality, ranking → charts → report.pdf)
                 → answer                (numbers copied from the run summary)
```
Details: [references/methodology.md](references/methodology.md) · decisions: [docs/adr/0001-architecture.md](docs/adr/0001-architecture.md) · spec: [docs/specs/](docs/specs/) · roadmap: [references/roadmap.md](references/roadmap.md).

## How it was verified
- Unit and acceptance tests written before the code, on synthetic series and on recorded real API responses: `.venv/bin/python -m pytest`.
- Live checks against the real API: `.venv/bin/python -m pytest -m live`.
- The case scenarios run end to end on Claude Haiku 4.5: without the skill no report and invented numbers in 5 of 7 answers (read by hand); with it 5/7 by the keyword checker (the two failures are wording; hand reading still found a few comparisons the model made up), every report on one page: `evals/`, details in [docs/verification.md](docs/verification.md#4-full-scenario-on-claude-haiku-45).
- Independent cross-check of numbers and notes on how AI tools were used: [docs/verification.md](docs/verification.md).

## Development
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt  # python3 must be 3.12+
.venv/bin/python -m pytest
```

## License
MIT — see [LICENSE](LICENSE).
