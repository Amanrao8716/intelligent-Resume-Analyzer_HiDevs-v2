import pytest

from resume_analyzer.config import Config
from resume_analyzer.matcher import JobDescription, match
from resume_analyzer.parser import ParsedResume


def resume(**kw):
    base = dict(skills=["python", "sql"], years_experience=2.0, education_level="bachelor",
                raw_text="python sql backend services")
    base.update(kw)
    return ParsedResume(**base)


def test_perfect_match():
    job = JobDescription(required_skills=["Python", "SQL"], min_years_experience=2,
                         min_education="bachelor", description="python sql backend")
    res = match(resume(), job)
    assert res.overall_score >= 90
    assert res.missing_skills == []
    assert res.recommendation.startswith("Strong")


def test_missing_skills_lower_score():
    job = JobDescription(required_skills=["python", "kubernetes", "aws"])
    res = match(resume(), job)
    assert res.missing_skills == ["kubernetes", "aws"]
    assert res.matched_skills == ["python"]
    assert res.breakdown["skills"] < 60


def test_aliases_resolve_in_job():
    job = JobDescription(required_skills=["py", "PostgreSQL"])
    assert match(resume(), job).missing_skills == []


def test_experience_capped_at_100():
    job = JobDescription(min_years_experience=1)
    assert match(resume(years_experience=10), job).breakdown["experience"] == 100.0


def test_partial_experience():
    job = JobDescription(min_years_experience=4)
    assert match(resume(years_experience=2), job).breakdown["experience"] == 50.0


def test_education_shortfall():
    job = JobDescription(min_education="master")
    assert match(resume(), job).breakdown["education"] == pytest.approx(66.7, abs=0.1)


def test_bonus_skills():
    job = JobDescription(required_skills=["python"], nice_to_have_skills=["sql", "aws"])
    assert match(resume(), job).bonus_skills == ["sql"]


def test_custom_weights_change_score():
    job = JobDescription(required_skills=["python", "aws"], min_years_experience=2)
    heavy_skills = Config(weights={"skills": 1, "experience": 0, "education": 0, "keywords": 0}).validate()
    heavy_exp = Config(weights={"skills": 0, "experience": 1, "education": 0, "keywords": 0}).validate()
    assert match(resume(), job, heavy_exp).overall_score > match(resume(), job, heavy_skills).overall_score


def test_score_bounds_and_weak_recommendation():
    job = JobDescription(required_skills=["rust", "go"], min_years_experience=5,
                         min_education="phd", description="rust go systems")
    res = match(resume(skills=[], years_experience=0, education_level="unknown", raw_text="x"), job)
    assert 0 <= res.overall_score <= 100
    assert res.recommendation.startswith("Weak")


def test_invalid_job():
    with pytest.raises(ValueError):
        JobDescription(min_years_experience=-1)
    with pytest.raises(ValueError):
        JobDescription(min_education="wizard")
