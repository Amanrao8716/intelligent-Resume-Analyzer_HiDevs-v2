"""Command-line interface: ``python -m resume_analyzer``."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .config import ConfigError, load_config
from .parser import ResumeParseError
from .report import save_report, to_markdown
from .service import analyse_file, load_job

log = logging.getLogger("resume_analyzer")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="resume-analyzer",
                                description="Score a resume against a job description.")
    p.add_argument("resume", nargs="+", help="resume file(s): .txt, .md or .pdf")
    p.add_argument("-j", "--job", required=True, help="job description JSON file")
    p.add_argument("-c", "--config", help="JSON config file (weights, thresholds, ...)")
    p.add_argument("-o", "--output-dir", help="where to write reports (overrides config)")
    p.add_argument("--format", choices=["json", "markdown", "both"], default="both")
    p.add_argument("--stdout", action="store_true", help="print the report instead of saving")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.output_dir:
            cfg.output_dir = args.output_dir
        logging.basicConfig(level=logging.DEBUG if args.verbose else cfg.log_level,
                            format="%(levelname)s %(message)s")
        job = load_job(args.job)
    except (ConfigError, ResumeParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    failures = 0
    for resume_path in args.resume:
        try:
            report = analyse_file(resume_path, job, cfg)
        except ResumeParseError as exc:
            log.error("%s: %s", resume_path, exc)
            failures += 1
            continue
        if args.stdout:
            print(json.dumps(report, indent=2) if args.format == "json" else to_markdown(report))
        else:
            paths = save_report(report, cfg.output_dir, Path(resume_path).stem)
            log.info("%s -> score %s (%s)", resume_path, report["match"]["overall_score"],
                     ", ".join(str(v) for v in paths.values()))
    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
