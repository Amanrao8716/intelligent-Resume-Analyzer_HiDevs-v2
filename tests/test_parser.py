from datetime import date

import pytest

from resume_analyzer.parser import (
    ResumeParseError,
    extract_education,
    extract_email,
    extract_experience_years,
    extract_name,
    extract_phone,
    extract_skills,
    load_text,
    parse_resume,
)

TODAY = date(2026, 1, 1)


def test_email_and_phone(resume_text):
    assert extract_email(resume_text) == "aman.rao@example.com"
    assert "98765" in extract_phone(resume_text)


def test_missing_contact():
    assert extract_email("no contact here") is None
    assert extract_phone("no contact here") is None


def test_name(resume_text):
    assert extract_name(resume_text) == "Aman Rao"
    assert extract_name("RESUME\n12345\n") is None


def test_skills_use_aliases_and_word_boundaries():
    skills = extract_skills("I know py, k8s, C++ and JS. Also nodejs.")
    assert {"python", "kubernetes", "c++", "javascript", "node.js"} <= set(skills)
    # 'c' must not match inside words like 'cat' / 'practice'
    assert "c" not in extract_skills("I practice with a cat")


def test_skills_not_found_inside_other_words():
    assert "java" not in extract_skills("javascript only")


def test_explicit_years_win():
    assert extract_experience_years("I have 3 years of experience", TODAY) == 3.0


def test_year_ranges_merge_overlaps():
    text = "Job A 2020 - 2022\nJob B 2021 - 2023"
    assert extract_experience_years(text, TODAY) == 3.9  # Jan 2020 .. Dec 2023 = 47 months


def test_present_range():
    assert extract_experience_years("Jan 2025 - Present", TODAY) == 1.0


def test_no_experience():
    assert extract_experience_years("fresh graduate", TODAY) == 0.0


@pytest.mark.parametrize("text,level", [
    ("PhD in physics", "phd"), ("M.Tech CSE", "master"), ("B.E. Computer Science", "bachelor"),
    ("Diploma in IT", "diploma"), ("high school", "unknown"),
    ("B.Tech and M.Sc", "master"),
])
def test_education(text, level):
    assert extract_education(text) == level


def test_parse_resume_full(resume_text):
    r = parse_resume(resume_text, today=TODAY)
    assert r.name == "Aman Rao"
    assert {"python", "sql", "git", "docker", "aws"} <= set(r.skills)
    assert r.education_level == "bachelor"
    assert r.years_experience > 0
    assert "raw_text" not in r.__dict__ or r.raw_text


def test_empty_resume_raises():
    with pytest.raises(ResumeParseError):
        parse_resume("   \n ")


def test_load_text_missing_file(tmp_path):
    with pytest.raises(ResumeParseError):
        load_text(str(tmp_path / "nope.txt"))


def test_load_text_txt(tmp_path):
    f = tmp_path / "r.txt"
    f.write_text("hello", encoding="utf-8")
    assert load_text(str(f)) == "hello"


def test_load_text_bad_pdf(tmp_path):
    f = tmp_path / "bad.pdf"
    f.write_bytes(b"not a pdf")
    with pytest.raises(ResumeParseError):
        load_text(str(f))
