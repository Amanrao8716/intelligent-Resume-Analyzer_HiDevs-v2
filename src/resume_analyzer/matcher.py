"""Weighted matching of a parsed resume against a job description."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import Config
from .parser import EDU_RANK, ParsedResume
from .skills import canonicalise_many

STOPWORDS = {
    "the", "and", "for", "with", "you", "our", "are", "will", "have", "has", "that", "this",
    "from", "your", "who", "was", "can", "all", "any", "but", "not", "job", "role", "team",
    "work", "years", "year", "experience", "skills", "required", "preferred", "must",
}


@dataclass
class JobDescription:
    title: str = "Untitled role"
    required_skills: List[str] = field(default_factory=list)
    nice_to_have_skills: List[str] = field(default_factory=list)
    min_years_experience: float = 0.0
    min_education: str = "unknown"
    description: str = ""

    def __post_init__(self) -> None:
        if self.min_years_experience < 0:
            raise ValueError("min_years_experience cannot be negative")
        if self.min_education not in EDU_RANK:
            raise ValueError(f"min_education must be one of {sorted(EDU_RANK)}")


@dataclass
class MatchResult:
    overall_score: float
    breakdown: Dict[str, float]
    matched_skills: List[str]
    missing_skills: List[str]
    bonus_skills: List[str]
    recommendation: str


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z][a-z+#.]{2,}", text.lower()) if t not in STOPWORDS}


def _skill_score(resume: ParsedResume, job: JobDescription, taxonomy: Optional[str]):
    required = canonicalise_many(job.required_skills, taxonomy)
    nice = canonicalise_many(job.nice_to_have_skills, taxonomy)
    have = set(canonicalise_many(resume.skills, taxonomy))
    matched = [s for s in required if s in have]
    missing = [s for s in required if s not in have]
    bonus = [s for s in nice if s in have]
    if not required and not nice:
        return 100.0, matched, missing, bonus
    # required skills carry 85% of the weight, nice-to-have 15%
    req_part = (len(matched) / len(required)) if required else 1.0
    nice_part = (len(bonus) / len(nice)) if nice else (1.0 if required else 0.0)
    return 100 * (0.85 * req_part + 0.15 * nice_part), matched, missing, bonus


def _experience_score(resume: ParsedResume, job: JobDescription) -> float:
    if job.min_years_experience <= 0:
        return 100.0
    return min(100.0, 100 * resume.years_experience / job.min_years_experience)


def _education_score(resume: ParsedResume, job: JobDescription) -> float:
    need = EDU_RANK[job.min_education]
    if need == 0:
        return 100.0
    have = EDU_RANK.get(resume.education_level, 0)
    if have >= need:
        return 100.0
    return 100.0 * have / need


def _keyword_score(resume: ParsedResume, job: JobDescription) -> float:
    jd_tokens = _tokens(job.description)
    if not jd_tokens:
        return 100.0
    overlap = len(jd_tokens & _tokens(resume.raw_text))
    return 100.0 * overlap / len(jd_tokens)


def recommend(score: float, cfg: Config) -> str:
    if score >= cfg.strong_threshold:
        return "Strong match - proceed to interview"
    if score >= cfg.maybe_threshold:
        return "Possible match - review manually"
    return "Weak match - not recommended"


def match(resume: ParsedResume, job: JobDescription, cfg: Optional[Config] = None) -> MatchResult:
    cfg = cfg or Config().validate()
    skill, matched, missing, bonus = _skill_score(resume, job, cfg.skills_file)
    parts = {
        "skills": skill,
        "experience": _experience_score(resume, job),
        "education": _education_score(resume, job),
        "keywords": _keyword_score(resume, job),
    }
    overall = sum(parts[k] * cfg.weights[k] for k in parts)
    overall = round(max(0.0, min(100.0, overall)), 1)
    return MatchResult(
        overall_score=overall,
        breakdown={k: round(v, 1) for k, v in parts.items()},
        matched_skills=matched,
        missing_skills=missing,
        bonus_skills=bonus,
        recommendation=recommend(overall, cfg),
    )
