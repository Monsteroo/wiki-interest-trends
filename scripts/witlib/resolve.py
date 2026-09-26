"""Topic resolution: Wikidata item -> article per language, disambiguation, substitutes and related topics."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlencode

from .api import ApiClient

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
META_TTL = 7 * 24 * 3600
CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def wiki_api(lang: str) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"


def build_url(base: str, params: dict[str, str]) -> str:
    return base + "?" + urlencode({**params, "format": "json", "formatversion": "2"})


@dataclass
class Candidate:
    qid: str
    label: str
    description: str


@dataclass
class ResolveResult:
    qid: str | None
    label: str
    description: str
    candidates: list[Candidate] = field(default_factory=list)
    articles: dict[str, str | None] = field(default_factory=dict)
    disambiguation: list[str] = field(default_factory=list)
    substitutes: dict[str, list[str]] = field(default_factory=dict)
    related: list[dict] = field(default_factory=list)
    related_source: str | None = None


def search_entities(client: ApiClient, text: str, limit: int = 3) -> list[Candidate]:
    first = "uk" if CYRILLIC.search(text) else "en"
    for lang in dict.fromkeys([first, "en"]):
        url = build_url(WIKIDATA_API, {"action": "wbsearchentities", "search": text, "language": lang,
                                       "uselang": lang, "type": "item", "limit": str(limit)})
        found = [Candidate(x["id"], x.get("label", ""), x.get("description", ""))
                 for x in client.get_json(url, ttl=META_TTL).get("search", [])]
        if found:
            return found
    return []


def get_entities(client: ApiClient, qids: list[str], langs: list[str], label_langs: tuple[str, ...] = ("uk", "en")) -> dict[str, dict]:
    if not qids:
        return {}
    url = build_url(WIKIDATA_API, {"action": "wbgetentities", "ids": "|".join(qids), "props": "labels|descriptions|sitelinks",
                                   "languages": "|".join(label_langs), "sitefilter": "|".join(f"{lang}wiki" for lang in langs)})
    entities = {}
    for qid, entity in client.get_json(url, ttl=META_TTL).get("entities", {}).items():
        if "missing" in entity:
            continue
        entities[qid] = {
            "labels": {k: v["value"] for k, v in entity.get("labels", {}).items()},
            "descriptions": {k: v["value"] for k, v in entity.get("descriptions", {}).items()},
            "sitelinks": {site[:-4]: link["title"] for site, link in entity.get("sitelinks", {}).items()},
        }
    return entities


def page_info(client: ApiClient, lang: str, titles: list[str]) -> dict[str, dict]:
    titles = list(dict.fromkeys(titles))
    url = build_url(wiki_api(lang), {"action": "query", "titles": "|".join(titles), "prop": "pageprops|redirects",
                                     "ppprop": "disambiguation|wikibase_item", "rdnamespace": "0", "rdlimit": "max",
                                     "redirects": "1"})
    query = client.get_json(url, ttl=META_TTL).get("query", {})
    normalized = {n["from"]: n["to"] for n in query.get("normalized", [])}
    redirected = {r["from"]: r["to"] for r in query.get("redirects", [])}
    pages = {p["title"]: p for p in query.get("pages", [])}
    info = {}
    for title in titles:
        name = normalized.get(title, title)
        name = redirected.get(name, name)
        page = pages.get(name)
        if page is None or page.get("missing") or page.get("invalid"):
            info[title] = {"exists": False, "title": name, "disambiguation": False, "qid": None, "redirects": []}
            continue
        props = page.get("pageprops", {})
        info[title] = {"exists": True, "title": page["title"], "disambiguation": "disambiguation" in props,
                       "qid": props.get("wikibase_item"), "redirects": [r["title"] for r in page.get("redirects", [])]}
    return info


def search_titles(client: ApiClient, lang: str, query: str, limit: int = 3) -> list[str]:
    url = build_url(wiki_api(lang), {"action": "query", "list": "search", "srsearch": query, "srnamespace": "0", "srlimit": str(limit)})
    return [x["title"] for x in client.get_json(url, ttl=META_TTL).get("query", {}).get("search", [])]


def resolve_topic(client: ApiClient, text: str, langs: list[str], qid: str | None = None, with_related: bool = True) -> ResolveResult:
    candidates = [] if qid else search_entities(client, text)
    chosen = qid or (candidates[0].qid if candidates else None)
    if chosen is None:
        return ResolveResult(qid=None, label=text, description="", articles={lang: None for lang in langs})
    prefer = ("uk", "en") if CYRILLIC.search(text) else ("en", "uk")
    entity = get_entities(client, [chosen], langs).get(chosen, {"labels": {}, "descriptions": {}, "sitelinks": {}})
    result = ResolveResult(
        qid=chosen,
        label=next((entity["labels"][lang] for lang in prefer if lang in entity["labels"]), text),
        description=next((entity["descriptions"][lang] for lang in prefer if lang in entity["descriptions"]), ""),
        candidates=candidates,
        articles={lang: entity["sitelinks"].get(lang) for lang in langs},
    )
    for lang, title in result.articles.items():
        if title and page_info(client, lang, [title])[title]["disambiguation"]:
            result.disambiguation.append(lang)
    english = entity["labels"].get("en")
    for lang, title in result.articles.items():
        if title is None:
            found: list[str] = []
            for query in dict.fromkeys(q for q in (english, text) if q):
                found += [t for t in search_titles(client, lang, query) if t not in found]
                if len(found) >= 3:
                    break
            result.substitutes[lang] = found[:3]
    if with_related:
        _add_related(client, result, langs)
    return result


def _add_related(client: ApiClient, result: ResolveResult, langs: list[str], limit: int = 8) -> None:
    source = next((lang for lang in langs if result.articles.get(lang) and lang not in result.disambiguation), None)
    if source is None:
        return
    titles = search_titles(client, source, f"morelike:{result.articles[source]}", limit=limit)
    if not titles:
        return
    infos = page_info(client, source, titles)
    picked: list[tuple[str, str]] = []
    for title in titles:
        item = infos[title]
        if item["exists"] and not item["disambiguation"] and item["qid"] and item["qid"] != result.qid \
                and item["qid"] not in [q for q, _ in picked]:
            picked.append((item["qid"], item["title"]))
    entities = get_entities(client, [q for q, _ in picked], langs)
    result.related_source = source
    result.related = [{"qid": q, "title": t, "langs": [lang for lang in langs if lang in entities.get(q, {}).get("sitelinks", {})]}
                      for q, t in picked]
