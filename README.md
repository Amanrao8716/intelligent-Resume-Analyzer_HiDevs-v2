# Intelligent Resume Analyzer

![CI](https://github.com/Amanrao8716/Intelligent-Resume-Analyzer_HiDevs/actions/workflows/ci.yml/badge.svg)

Parses a resume (`.txt`, `.md`, `.pdf`), extracts structured data, scores it against a
job description with **configurable weights**, and writes a JSON + Markdown report.
Use it from the **command line** or a **Streamlit web UI**.

## Features
- Extracts name, email, phone, skills, years of experience and education level
- Skill **taxonomy with aliases** (`js` -> `javascript`, `k8s` -> `kubernetes`) and word-boundary
  matching (so `c` never matches inside `practice`)
- Experience from explicit claims (`3 years`) or merged date ranges (`Jan 2025 - Present`);
  education date ranges are ignored
- Weighted score: skills 55%, experience 25%, education 10%, keyword overlap 10% (all configurable)
- Required vs nice-to-have skills, matched / missing / bonus lists, hiring recommendation
- Batch mode: analyse many resumes in one command
- Clear errors and exit codes (0 ok, 1 a resume failed, 2 bad config/job file)
- 50 automated tests (~98% coverage), linting and GitHub Actions CI, Dockerfile

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .

# CLI
resume-analyzer data/sample/resume.txt -j data/sample/job.json --stdout
resume-analyzer a.pdf b.txt -j job.json -o reports/ -c config.example.json

# Web UI
streamlit run app.py

# Tests + lint
pytest
ruff check .
```

## Job file (`job.json`)
```json
{
  "title": "Backend Developer Intern",
  "required_skills": ["Python", "SQL", "Git", "REST API"],
  "nice_to_have_skills": ["Docker", "AWS"],
  "min_years_experience": 1,
  "min_education": "bachelor",
  "description": "free text used for keyword overlap"
}
```
`min_education`: `unknown | diploma | bachelor | master | phd`.

## Configuration
Copy `config.example.json` and pass it with `--config`, or set
`RESUME_ANALYZER_CONFIG`, `RESUME_ANALYZER_OUTPUT_DIR`, `RESUME_ANALYZER_LOG_LEVEL`.
Weights are auto-normalised to sum to 1. A custom skills taxonomy can be supplied via
`"skills_file": "my_skills.json"` (`{"rust": ["rustlang"]}`).

## Architecture
```
src/resume_analyzer/
  config.py    settings: defaults < JSON file < env vars, validated
  skills.py    taxonomy, aliases, normalisation
  parser.py    text loading (txt/pdf) + field extraction
  matcher.py   JobDescription, weighted scoring, recommendation
  report.py    JSON / Markdown report building and saving
  service.py   high-level API used by CLI and UI
  cli.py       argparse command line
app.py         Streamlit UI
tests/         pytest suite
```
Flow: `load_text -> parse_resume -> match -> build_report -> save_report`.

## Docker
```bash
docker build -t resume-analyzer . && docker run -p 8501:8501 resume-analyzer
```

## Limitations
Extraction is rule-based (regex + taxonomy), so unusual layouts and skills outside the
taxonomy can be missed. Extend the taxonomy through `skills_file`; spaCy-based entity
extraction would be the next step.
## 🎥 Project Demo

Watch the project demo here:

[![Resume Analyzer Demo](https://img.youtube.com/vi/mlpkI6vsRyY/0.jpg)](https://youtu.be/mlpkI6vsRyY)

**▶️ [Click here to watch the full demo on YouTube](https://youtu.be/mlpkI6vsRyY)**
