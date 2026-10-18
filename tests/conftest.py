from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample"


@pytest.fixture
def resume_text() -> str:
    return (SAMPLE / "resume.txt").read_text(encoding="utf-8")


@pytest.fixture
def job_path() -> str:
    return str(SAMPLE / "job.json")
