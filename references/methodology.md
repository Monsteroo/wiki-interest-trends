# Methodology

How `scripts/wit run` turns pageviews into verdicts. The code computes everything below; the agent only explains it.

## Data
- Source: Wikimedia Pageviews API with `agent=user` (spiders and automated traffic excluded) and `access=all-access`.
- Articles for a topic in a language: the Wikidata sitelink (or the `substitutes` title), the articles of `related` items that exist in that language, and up to 10 redirects to the main article. Wikimedia does not count views of redirects towards the target article, so they are added explicitly.
- Daily views for the last 60 complete months, never earlier than 2015-07. Days without data count as zero (the API omits them).
- Complete months only. On the 1st–2nd day of a month the previous month is skipped because it may not be loaded yet. `--as-of` fixes the date for reproducible reports.
- Language-edition totals (`aggregate`, `agent=user`) are used for normalisation.

## Measures
- `views`: average views per month over the last 12 months.
- `share`: views per million views of the whole language edition. It removes the effect of a growing or shrinking Wikipedia and makes small and large editions comparable. This is the default measure.

## Growth
- Year-over-year growth = mean of the last 12 months / mean of the previous 12 months − 1. It is computed for both measures; the verdict uses `measure`. Comparing whole years cancels seasonality.
- For `months` ≥ 36 the report also gives annualised growth between the first and the last 12 months of the window.
- Months up (down): in how many of the last 12 months the value is above (below) the same month a year earlier.

## Spikes
A day is a spike when it has at least 20 views and more than max(5 × median, median + 10 × MAD) of the previous 28 days. `growth_clean` is the growth recomputed with spike days replaced by that median.

## Verdict
| verdict | rule |
|---|---|
| growing | growth ≥ +10% and up in at least 7 of 12 months |
| declining | growth ≤ −10% and down in at least 7 of 12 months |
| no clear trend | otherwise |
| no data | no article, a disambiguation page, or zero views |

## Trust
Trust starts at high. Each rule can lower it and adds its reason to the summary and the report.

| rule | condition | effect |
|---|---|---|
| R1 volume | under 100 views a month / 100–499 | low / at most medium |
| R2 consistency | growing or declining in only 7–8 of 12 months | at most medium |
| R3 event | without spike days the growth drops under 10% or under half (for a decline: mirrored) | low |
| R4 new article | the first month with views falls inside the two compared years | low |
| R5 substitute | a substitute article is used | at most medium |
| N1 divergence | views and share move in opposite directions, both by at least 5% | note only |

## Seasonality
Computed on spike-free data of up to five yearly cycles (at least three, and at least 100 views a month). Each cycle is divided by its own mean and the month-of-year profile is averaged. The peak is stable when it is the top month in at least 60% of cycles and at least 20% above the yearly mean.

## Ranking
Only when `priorities` are given. For growth, interest (share) and reach (views) every series gets a rank; score = Σ weight × (n − rank) / (n − 1). Trust is shown next to the score but is not part of it.

## Limitations
- A language edition is not a country: it is read in many countries, and people also read other editions.
- Pageviews measure interest, not willingness to pay.
- Automated traffic is filtered by Wikimedia heuristics, not perfectly.
- A topic is measured through a few articles; substitutes and related articles are indirect measures.
