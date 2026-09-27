import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def frontmatter(text):
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    head, body = text[4:].split("\n---\n", 1)
    fields = {}
    for line in head.splitlines():
        if re.match(r"^[a-z-]+:", line):
            key, _, value = line.partition(":")
            fields[key] = value.strip()
    return fields, body


def test_skill_md_follows_the_agent_skills_spec():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    fields, _body = frontmatter(text)
    assert fields["name"] == ROOT.name == "wiki-interest-trends"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fields["name"]) and len(fields["name"]) <= 64
    assert 1 <= len(fields["description"]) <= 1024
    assert len(fields.get("compatibility", "")) <= 500
    assert len(text.splitlines()) < 500


def test_skill_md_links_point_to_existing_files():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert [link for link in re.findall(r"\]\(([^)#]+)\)", text) if not (ROOT / link).exists()] == []
