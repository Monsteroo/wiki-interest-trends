# study.json fields

| field | type | default | meaning |
|---|---|---|---|
| `question` | text, ≤ 500 characters | required | the user's question, verbatim; printed on the report |
| `topics` | 1–3 objects | required | what to compare |
| `label` | text, ≤ 80 characters | required | topic name used in the report |
| `wikidata` | `Q…` | required | Wikidata id printed by `resolve` |
| `related` | list of `Q…`, ≤ 10 | `[]` | extra articles for broad topics, counted where they exist |
| `substitutes` | `{language: article title}` | `{}` | article to use where the topic has no article; flagged as a substitute |
| `languages` | 1–8 codes | required | Wikipedia editions such as `pl`, `cs`, `uk`; names like "Polish" are accepted |
| `months` | 12–120 | 24 | analysis window in complete months |
| `measure` | `share` or `views` | `share` | measure used for verdicts and charts |
| `priorities` | weights for `growth`, `interest`, `reach` | none | turns on the ranking of audiences |
| `report_language` | `uk` or `en` | from the question | language of the PDF |
| `summary` | text, ≤ 600 characters | template | your summary; numbers only as `{key.metric}` |
| `next_steps` | ≤ 5 texts, ≤ 200 characters each | template | your recommendations; same rule |

Limit: topics × languages ≤ 8.

## Placeholders
`{key.metric}`. The key is the language code when there is one topic (`cs`), `t1`…`t3` when there are several topics and one language, otherwise `t1.cs`. Metrics: `growth`, `growth_clean`, `views`, `share`, `months_up`, `trust`, `verdict`, `peak_month`, `rank`, `title`. `run` prints the valid keys. Percentages and numbers of 100 or more typed without a placeholder are rejected.

## Follow-up edits
| the user says | edit |
|---|---|
| "add Slovak" | append `"sk"` to `languages` |
| "last five years" | `"months": 60` |
| "growth matters more" | raise `priorities.growth` |
| "absolute numbers" | `"measure": "views"` |
| "use article X for Polish" | `"substitutes": {"pl": "X"}` |

## Examples
```json
{"question": "Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.",
 "topics": [{"label": "Інтервальне голодування", "wikidata": "Q1666254"}], "languages": ["pl", "cs"], "months": 24}
```
```json
{"question": "Порівняй інтерес до вивчення англійської в pl, cs, uk, tr, id: які аудиторії дослідити наступними?",
 "topics": [{"label": "Вивчення англійської", "wikidata": "Q1860", "related": ["Q490396", "Q487425", "Q130192"]}],
 "languages": ["pl", "cs", "uk", "tr", "id"], "priorities": {"growth": 0.4, "interest": 0.3, "reach": 0.3}}
```
