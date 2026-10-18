"""High-level API shared by the CLI and the Streamlit app."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .config import Config
from .matcher import JobDescription, match
from .parser import ResumeParseError, load_text, parse_resume
from .report import build_report


def load_job(path: str) -> JobDescription:
    p = Path(path)
    if not p.is_file():
        raise ResumeParseError(f"job file not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ResumeParseError(f"invalid job JSON: {exc}") from exc
    try:
        return JobDescription(**data)
    except TypeError as exc:
        raise ResumeParseError(f"invalid job fields: {exc}") from exc
    except ValueError as exc:
        raise ResumeParseError(str(exc)) from exc


def analyse_text(text: str, job: JobDescription, cfg: Optional[Config] = None) -> Dict[str, Any]:
    cfg = cfg or Config().validate()
    resume = parse_resume(text, cfg.skills_file)
    return build_report(resume, job, match(resume, job, cfg))


def analyse_file(
    resume_path: str, job: JobDescription, cfg: Optional[Config] = None
) -> Dict[str, Any]:
    return analyse_text(load_text(resume_path), job, cfg)
