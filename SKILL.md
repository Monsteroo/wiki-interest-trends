---
name: wiki-interest-trends
description: Analyses Wikipedia pageview trends across language editions to help product teams decide which topics to build and which languages or markets to launch in. Compares interest between languages or topics, tells whether growth is real and how far to trust it, finds seasonality (when to launch), ranks audiences by the user's priorities, and produces charts plus a shareable PDF report (one page whenever it fits). Use when the user asks about interest in a topic on Wikipedia, compares languages or markets, plans localization, chooses a course or content topic, asks about growth trends or seasonality, or wants a short data-backed report.
license: MIT
compatibility: Requires Python 3.12+ and internet access to Wikimedia APIs. Uses uv when available, otherwise creates a virtualenv on first run (about a minute).
metadata:
  version: "1.0.0"
---

# Wikipedia interest trends

You turn a product question into a small study form (`study.json`), run the engine and explain its output.
**The engine computes every number. Never calculate, estimate or invent numbers yourself, and never write your own analysis code or scrape the web for this task.**

`<skill>` below is the absolute path of this skill's folder. Give every command a 10-minute timeout: the first run prepares Python and downloads data; later runs use the cache and take seconds.

## Workflow

### 1. Find the topic
```bash
<skill>/scripts/wit resolve "<topic in the user's words>" --langs pl,cs --question "<the user's question, verbatim>" --save wiki-studies/<short-name>
```
Read the output:
- `TOPIC`: check that this is the meaning the user wants. If `other candidates` show a different plausible meaning (e.g. Mercury the planet vs the element), ask the user which one, then rerun with `--qid Q…`.
- `ARTICLES`: a language marked `no article` has no article on this topic. Tell the user. If a substitute candidate is clearly the same subject, you may add it to `substitutes` and say so; otherwise leave it, because the gap itself is a finding.
- `RELATED`: neighbouring topics with Wikidata ids. For a broad topic ("astronomy", "learning English") add 2–4 of them that exist in all requested languages to `related` and tell the user you did. For a narrow topic, only mention them.

### 2. Adjust the form
Edit `wiki-studies/<short-name>/study.json`. Keep only what the user asked for.
- The user wants to choose audiences, or gives priorities → `"priorities": {"growth": 0.4, "interest": 0.3, "reach": 0.3}` (weights follow their words).
- "last five years" → `"months": 60`; absolute numbers → `"measure": "views"`.
Field reference: [references/study-fields.md](references/study-fields.md)

### 3. Run
```bash
<skill>/scripts/wit run wiki-studies/<short-name>
```
If it prints `ERROR` and `FIX`, apply the FIX and run again. The summary has one line per series: views per month, share per million views, YoY growth and growth without spikes, months up out of 12, verdict, trust with its main reason, seasonality. Then come `RANKING`, `WARNINGS`, `FILES` and the placeholder `KEYS`.

### 4. Answer the user
Answer in the user's language, briefly:
1. The answer to the question: the verdict per language or topic, with the YoY growth figure.
2. A line that starts with "Довіра:" (or "Trust:" when answering in English): the level (high, medium or low) and its reason. Low trust means the signal is weak; say so and do not build a recommendation on it alone.
3. Spikes: if a series line lists `spikes:`, name the biggest spike date, say the growth may be driven by that event and suggest re-checking in 3–6 months. Never call such growth steady.
4. The seasonal peak month and the ranking, if present.
5. A line that starts with "Обмеження:" (or "Limitation:" when answering in English) naming at least one: a Wikipedia language is not a country; pageviews show interest, not willingness to pay; substitutes and related articles are indirect measures.
6. The path to `report.pdf`.

Copy numbers exactly as printed. Do not turn counts into percentages yourself (write "up 9 of 12 months", not "75%").

### 5. Optional: your own report text
Add `"summary"` (≤ 600 characters) and `"next_steps"` (≤ 5 items) to the form and write every number as a placeholder `{key.metric}`, e.g. `{cs.growth}`, `{cs.trust}`, `{cs.peak_month}`, `{pl.rank}`. The keys and metrics are listed in the run summary. Run again. The engine rejects percentages and numbers ≥ 100 typed without placeholders.

## Follow-up requests
Edit the same `study.json` and run again; cached data makes it fast.
- Add a language: append its code to `languages`.
- Change the period: `months`.
- "Growth matters more": raise `priorities.growth`.

Start a new folder only for a new question.

## Examples
Polish vs Czech interest in intermittent fasting. Polish has no article, so the gap is reported:
```json
{"question": "Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.",
 "topics": [{"label": "Інтервальне голодування", "wikidata": "Q1666254"}], "languages": ["pl", "cs"], "months": 24}
```

Growth of interest in astronomy in Ukrainian Wikipedia and how far to trust it. It is a broad topic, so a related article is added:
```json
{"question": "Чи зростає інтерес до астрономії в україномовній Wikipedia і наскільки цьому можна довіряти?",
 "topics": [{"label": "Астрономія", "wikidata": "Q333", "related": ["Q544"]}], "languages": ["uk"]}
```

Which audiences to research next for an English-learning app. This uses an indirect topic plus a ranking:
```json
{"question": "Порівняй інтерес до вивчення англійської в pl, cs, uk, tr, id: які аудиторії дослідити наступними?",
 "topics": [{"label": "Вивчення англійської", "wikidata": "Q1860", "related": ["Q490396", "Q487425", "Q130192"]}],
 "languages": ["pl", "cs", "uk", "tr", "id"], "priorities": {"growth": 0.4, "interest": 0.3, "reach": 0.3}}
```
Tell the user that "English language" articles are an indirect measure of interest in learning English.

## Troubleshooting
| message | what to do |
|---|---|
| `languages: unknown language 'polish'; did you mean 'pl'?` | use the code |
| `topics[1].wikidata: … is not a Wikidata id` | run `resolve` and copy the `Q…` id |
| `summary contains '15%'` | replace the number with a placeholder such as `{cs.growth}` |
| exit code 3 (network) | wait a minute and rerun; downloaded data is cached |
| exit code 4 (no data) | the topic has no article in any requested language: set `substitutes` or report the gap |
| exit code 5 (environment) | Python 3.12+ is missing: tell the user |

How growth, trust, seasonality and ranking are computed: [references/methodology.md](references/methodology.md). What comes next: [references/roadmap.md](references/roadmap.md).
