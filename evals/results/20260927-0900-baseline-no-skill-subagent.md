# Baseline without the skill — model haiku (subagent)

Date: 2026-09-27. Model: Claude Haiku 4.5 (Claude Code subagent, variant B). Prompt: `evals/subagent_prompt.md` without the skill block.
Work folders were outside the repository so the model could not find the skill; F1/F2 were sent as follow-ups to the E1/E3 agents.

## Checker (`evals/check.py`)

| scenario | result | details |
|---|---|---|
| E1 | FAIL | no wiki-studies/*/study.json was created |
| E2 | FAIL | no wiki-studies/*/study.json was created |
| E3 | FAIL | no wiki-studies/*/study.json was created |
| F1 | FAIL | no wiki-studies/*/study.json was created |
| F2 | FAIL | no wiki-studies/*/study.json was created |
| T1 | FAIL | no wiki-studies/*/study.json was created |
| T2 | FAIL | no wiki-studies/*/study.json was created |

## What went wrong (read by hand, numbers checked against the Wikimedia API)

| scenario | failure |
|---|---|
| E1 | Took the wrong Polish article: "Głodówka lecznicza" (therapeutic fasting) instead of reporting that Polish Wikipedia has no intermittent-fasting article; claimed +514% for Polish. Also wrote files into the repository root, ignoring the work folder. |
| F1 | Took Slovak "Pôst" (religious fasting; its peaks are Lent) and claimed +982.5%, "the largest interest in Central Europe". |
| E2 | Invented a "reliability 97/100" score; claimed +4.8% growth and "green light". The same topic measured by the skill falls by 53% in views (checked independently, see docs/verification.md). |
| E3 | Answered from general knowledge: labour force, "English skill gap 60%", "ROI 5/5 stars"; no pageview comparison, no report file. |
| F2 | Invented growth rates ("Ukraine +14% a year", "EdTech CAGR 15%"); the pageview data shows Ukrainian interest falling. |
| T1 | Did not ask which Mercury; used 3 months of data and claimed +1,089% growth. |
| T2 | Used real data (April 2024 eclipse spike) but no trust level, no report, no stated limitation. |

No scenario produced a study form, a chart file or a PDF; five of seven contain numbers that do not come from the data.
