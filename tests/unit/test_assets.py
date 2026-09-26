import json
from pathlib import Path

from witlib.study import parse_study

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("question", "topics", "label", "wikidata", "related", "substitutes", "languages", "months", "measure",
          "priorities", "report_language", "summary", "next_steps")


def test_study_template_is_a_valid_form():
    study = parse_study(json.loads((ROOT / "assets" / "study-template.json").read_text(encoding="utf-8")))
    assert study.languages == ["pl", "cs"]


def test_field_reference_covers_every_form_field():
    text = (ROOT / "references" / "study-fields.md").read_text(encoding="utf-8")
    assert [name for name in FIELDS if f"`{name}`" not in text] == []


def test_methodology_documents_every_trust_rule():
    text = (ROOT / "references" / "methodology.md").read_text(encoding="utf-8")
    assert [rule for rule in ("R1", "R2", "R3", "R4", "R5", "N1") if rule not in text] == []


def test_roadmap_and_readme_exist():
    assert "v2" in (ROOT / "references" / "roadmap.md").read_text(encoding="utf-8")
    assert "scripts/wit" in (ROOT / "README.md").read_text(encoding="utf-8")
