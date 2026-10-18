"""Resume parsing: text loading and field extraction."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from .skills import alias_map, skill_pattern

log = logging.getLogger(__name__)


class ResumeParseError(Exception):
    """Raised when a resume cannot be read or is empty."""


@dataclass
class ParsedResume:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    years_experience: float = 0.0
    education_level: str = "unknown"
    raw_text: str = ""


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){9,11}\d(?!\d)")
YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.I)
MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"
RANGE_RE = re.compile(
    rf"(?:(?P<m1>{MONTH})\.?\s+)?(?P<y1>(?:19|20)\d{{2}})\s*(?:-|–|—|to)\s*"
    rf"(?:(?:(?P<m2>{MONTH})\.?\s+)?(?P<y2>(?:19|20)\d{{2}})|(?P<present>present|current|now|ongoing))",
    re.I,
)
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

EDU_LEVELS = [
    ("phd", re.compile(r"\b(ph\.?d|doctorate)\b", re.I)),
    ("master", re.compile(r"\b(m\.?tech|m\.?sc|m\.?s|mca|mba|master'?s?)\b", re.I)),
    ("bachelor", re.compile(r"\b(b\.?e|b\.?tech|b\.?sc|bca|b\.?s|bachelor'?s?)\b", re.I)),
    ("diploma", re.compile(r"\bdiploma\b", re.I)),
]
EDU_RANK = {"unknown": 0, "diploma": 1, "bachelor": 2, "master": 3, "phd": 4}
EDU_LINE_RE = re.compile(r"\b(university|institute|college|school|degree|gpa|cgpa)\b", re.I)
SECTION_WORDS = {"resume", "curriculum vitae", "cv", "summary", "objective", "profile"}


def load_text(path: str) -> str:
    """Read .txt/.md or .pdf into plain text."""
    p = Path(path)
    if not p.is_file():
        raise ResumeParseError(f"file not found: {p}")
    try:
        if p.suffix.lower() == ".pdf":
            return _read_pdf(p)
        return p.read_text(encoding="utf-8", errors="replace")
    except ResumeParseError:
        raise
    except OSError as exc:
        raise ResumeParseError(f"cannot read {p}: {exc}") from exc


def _read_pdf(p: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise ResumeParseError("pypdf is required for PDF resumes (pip install pypdf)") from exc
    try:
        reader = PdfReader(str(p))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:
        raise ResumeParseError(f"cannot parse PDF {p.name}: {exc}") from exc


def extract_email(text: str) -> Optional[str]:
    m = EMAIL_RE.search(text)
    return m.group(0).lower() if m else None


def extract_phone(text: str) -> Optional[str]:
    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 13:
            return m.group(0).strip()
    return None


def extract_name(text: str) -> Optional[str]:
    """Heuristic: first short alphabetic line that is not a section header/contact."""
    for line in text.splitlines()[:8]:
        s = line.strip().strip("#*|: ")
        if not s or "@" in s or any(ch.isdigit() for ch in s):
            continue
        if s.lower() in SECTION_WORDS:
            continue
        words = s.split()
        if 1 < len(words) <= 4 and all(re.fullmatch(r"[A-Za-z.'-]+", w) for w in words):
            return " ".join(w.capitalize() if w.isupper() else w for w in words)
    return None


def extract_skills(text: str, taxonomy_path: Optional[str] = None) -> List[str]:
    found = set()
    for term, canon in alias_map(taxonomy_path).items():
        if canon not in found and skill_pattern(term).search(text):
            found.add(canon)
    return sorted(found)


def extract_experience_years(text: str, today: Optional[date] = None) -> float:
    """Prefer an explicit "N years" claim; otherwise sum merged date ranges."""
    today = today or date.today()
    explicit = [float(m.group(1)) for m in YEARS_RE.finditer(text) if float(m.group(1)) < 50]
    if explicit:
        return round(max(explicit), 1)

    spans: List[Tuple[int, int]] = []
    # ignore date ranges on education lines (e.g. "B.E., 2022 - 2026")
    work_text = "\n".join(
        ln for ln in text.splitlines()
        if not EDU_LINE_RE.search(ln) and extract_education(ln) == "unknown"
    )
    for m in RANGE_RE.finditer(work_text):
        y1 = int(m.group("y1"))
        m1 = MONTHS.get((m.group("m1") or "jan")[:3].lower(), 1)
        if m.group("present"):
            y2, m2 = today.year, today.month
        else:
            y2 = int(m.group("y2"))
            m2 = MONTHS.get((m.group("m2") or "dec")[:3].lower(), 12)
        start, end = y1 * 12 + m1, y2 * 12 + m2
        if end >= start and y1 <= today.year:
            spans.append((start, end))
    if not spans:
        return 0.0
    spans.sort()
    merged = [list(spans[0])]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return round(sum(e - s for s, e in merged) / 12, 1)


def extract_education(text: str) -> str:
    best = "unknown"
    for level, pat in EDU_LEVELS:
        if pat.search(text) and EDU_RANK[level] > EDU_RANK[best]:
            best = level
    return best


def parse_resume(text: str, taxonomy_path: Optional[str] = None,
                 today: Optional[date] = None) -> ParsedResume:
    if not text or not text.strip():
        raise ResumeParseError("resume is empty")
    return ParsedResume(
        name=extract_name(text),
        email=extract_email(text),
        phone=extract_phone(text),
        skills=extract_skills(text, taxonomy_path),
        years_experience=extract_experience_years(text, today),
        education_level=extract_education(text),
        raw_text=text,
    )
