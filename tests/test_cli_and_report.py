import json

import pytest

from resume_analyzer.cli import main
from resume_analyzer.matcher import JobDescription
from resume_analyzer.parser import ResumeParseError
from resume_analyzer.report import build_report, save_report, to_markdown
from resume_analyzer.service import analyse_text, load_job


def test_analyse_text_end_to_end(resume_text, job_path):
    report = analyse_text(resume_text, load_job(job_path))
    assert report["candidate"]["name"] == "Aman Rao"
    assert "raw_text" not in report["candidate"]
    assert report["match"]["overall_score"] >= 75
    assert "kubernetes" not in report["match"]["bonus_skills"]


def test_markdown_and_save(resume_text, tmp_path):
    report = analyse_text(resume_text, JobDescription(required_skills=["python"]))
    md = to_markdown(report)
    assert "Overall score" in md
    paths = save_report(report, str(tmp_path / "out"), "x")
    assert json.loads(paths["json"].read_text())["match"]["overall_score"] > 0
    assert paths["markdown"].exists()


def test_load_job_errors(tmp_path):
    with pytest.raises(ResumeParseError):
        load_job(str(tmp_path / "nope.json"))
    bad = tmp_path / "bad.json"
    bad.write_text("{oops")
    with pytest.raises(ResumeParseError):
        load_job(str(bad))
    bad.write_text('{"unknown_field": 1}')
    with pytest.raises(ResumeParseError):
        load_job(str(bad))
    bad.write_text('{"min_education": "wizard"}')
    with pytest.raises(ResumeParseError):
        load_job(str(bad))


def test_cli_saves_reports(tmp_path, job_path):
    resume = "data/sample/resume.txt"
    code = main([resume, "-j", job_path, "-o", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "resume.json").exists() and (tmp_path / "resume.md").exists()


def test_cli_stdout(capsys, job_path):
    assert main(["data/sample/resume.txt", "-j", job_path, "--stdout", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["match"]["overall_score"] > 0
    assert main(["data/sample/resume.txt", "-j", job_path, "--stdout"]) == 0
    assert "Overall score" in capsys.readouterr().out


def test_cli_bad_inputs(tmp_path, job_path, capsys):
    assert main(["missing.txt", "-j", job_path, "-o", str(tmp_path)]) == 1
    assert main(["data/sample/resume.txt", "-j", "nope.json"]) == 2
    assert main(["data/sample/resume.txt", "-j", job_path, "-c", "nope.json"]) == 2
    assert "error:" in capsys.readouterr().err


def test_build_report_shape(resume_text):
    from resume_analyzer.config import Config
    from resume_analyzer.matcher import match
    from resume_analyzer.parser import parse_resume
    r = parse_resume(resume_text)
    job = JobDescription(title="X")
    rep = build_report(r, job, match(r, job, Config().validate()))
    assert set(rep) == {"generated_at", "tool_version", "job", "candidate", "match"}
