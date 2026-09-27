# Roadmap

## v1 — this version
One to three topics in up to eight language editions; growth, trust with reasons, seasonality, ranking by the user's priorities; a PDF report on one page (two only if the content does not fit); follow-ups by editing `study.json` with cached data. Verified by unit and acceptance tests on recorded API responses and by scenarios run on Claude Haiku 4.5.

## v2 — more precise answers
- Suggest related articles automatically and rank them by traffic (today: `morelike` suggestions confirmed by the user).
- Bot filter: compare mobile and desktop trends; desktop-only surges are a typical automated-traffic signature.
- Follow page moves (MediaWiki `logevents`) so renamed articles keep their history.
- Forecast with a prediction interval for the next 6–12 months.
- Event months in the trust rules: v1 caps single spike days, but a month-long surge around an event (Spanish "Eclipse solar", August 2026: 78 300 views against about 16 000 in a typical month) still counts as growth with high trust. Lower trust when one month holds most of the year's growth; found by the Haiku eval, see `evals/results/`.

## v3 — more data
- Replace per-article API calls with the bulk pageview dumps (`dumps.wikimedia.org/other/pageview_complete`, about 5 GB per month) loaded into a local DuckDB/Parquet store with incremental monthly updates: hundreds of articles × all languages without API limits.
- Discovery mode: "what is rising in language X or around topic Y", with SPARQL over Wikidata to group articles into topics.
- A persistent SQLite cache shared between studies; parallel fetching within Wikimedia's limit of three concurrent requests.

## v4 — countries and outside signals
- The differentially private country × page dataset (`analytics.wikimedia.org/published/datasets/country_project_page`, daily since 2023-02) to measure interest by country, not only by language.
- The official Google Trends API as a second signal once it leaves the application-only alpha (announced 2025-07). The unofficial `pytrends` library is archived and not suitable.
- Edit activity as a signal of content freshness. Not as "controversy": on popular topics most reverts are vandalism clean-up.

## How the skill grows safely
- Every new rule starts as a failing test on synthetic data; every new kind of request becomes a scenario in `evals/scenarios.json` that must pass on a cheap model before release.
- Recorded API responses keep reports reproducible in regression tests.
