"""Report generation (JSON + Markdown)."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from . import __version__
from .matcher import JobDescription, MatchResult
from .parser import ParsedResume


def build_report(resume: ParsedResume, job: JobDescription, result: MatchResult) -> Dict[str, Any]:
    candidate = asdict(resume)
    candidate.pop("raw_text", None)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool_version": __version__,
        "job": {k: v for k, v in asdict(job).items() if k != "description"},
        "candidate": candidate,
        "match": asdict(result),
    }


def to_markdown(report: Dict[str, Any]) -> str:
    c, m, j = report["candidate"], report["match"], report["job"]
    lines = [
        f"# Resume Analysis: {c.get('name') or 'Unknown candidate'}",
        "",
        f"**Role:** {j['title']}  ",
        f"**Overall score:** {m['overall_score']}/100  ",
        f"**Recommendation:** {m['recommendation']}",
        "",
        "## Score breakdown",
        "",
        "| Category | Score |",
        "|---|---|",
    ]
    lines += [f"| {k} | {v} |" for k, v in m["breakdown"].items()]
    lines += [
        "",
        f"**Matched skills:** {', '.join(m['matched_skills']) or '-'}  ",
        f"**Missing skills:** {', '.join(m['missing_skills']) or '-'}  ",
        f"**Bonus skills:** {', '.join(m['bonus_skills']) or '-'}",
        "",
        "## Candidate",
        "",
        f"- Email: {c.get('email') or '-'}",
        f"- Phone: {c.get('phone') or '-'}",
        f"- Experience: {c['years_experience']} years",
        f"- Education: {c['education_level']}",
    ]
    return "\n".join(lines) + "\n"


def save_report(report: Dict[str, Any], out_dir: str, stem: str = "report") -> Dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / f"{stem}.json"
    md_path = out / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
