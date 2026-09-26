"""Cross-check our daily sums against the API's own monthly totals and print links for a manual check."""
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from witlib.api import ApiClient  # noqa: E402
from witlib.series import PAGEVIEWS, fetch_daily  # noqa: E402

CASES = [("cs", "Přerušovaný půst"), ("uk", "Астрономія"), ("pl", "Język angielski")]
START, END = date(2025, 9, 1), date(2026, 8, 31)


def main():
    client = ApiClient()
    print("| article | our sum of daily views | API monthly total | match | manual check |")
    print("|---|---|---|---|---|")
    for lang, title in CASES:
        ours = sum(fetch_daily(client, lang, title, START, END).values())
        encoded = quote(title.replace(" ", "_"), safe="")
        url = f"{PAGEVIEWS}/per-article/{lang}.wikipedia.org/all-access/user/{encoded}/monthly/{START:%Y%m%d}00/{END:%Y%m%d}00"
        theirs = sum(item["views"] for item in client.get_json(url)["items"])
        link = (f"https://pageviews.wmcloud.org/?project={lang}.wikipedia.org&platform=all-access&agent=user"
                f"&redirects=0&start={START}&end={END}&pages={encoded}")
        print(f"| {lang}: {title} | {ours} | {theirs} | {'yes' if ours == theirs else 'NO'} | [pageviews.wmcloud.org]({link}) |")


if __name__ == "__main__":
    main()
