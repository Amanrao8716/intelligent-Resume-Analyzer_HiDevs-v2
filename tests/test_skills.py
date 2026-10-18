import json

from resume_analyzer.skills import (
    canonical_skill,
    canonicalise_many,
    load_taxonomy,
    normalise_skill,
)


def test_normalise():
    assert normalise_skill("  Machine   LEARNING ") == "machine learning"


def test_canonical_aliases():
    assert canonical_skill("JS") == "javascript"
    assert canonical_skill("Unknown Thing") == "unknown thing"


def test_canonicalise_many_dedupes():
    assert canonicalise_many(["py", "Python", "", "sql"]) == ["python", "sql"]


def test_custom_taxonomy(tmp_path):
    f = tmp_path / "t.json"
    f.write_text(json.dumps({"Rust": ["rustlang"]}))
    assert load_taxonomy(str(f)) == {"rust": ["rustlang"]}
    assert canonical_skill("RustLang", str(f)) == "rust"
