"""Streamlit UI: ``streamlit run app.py``."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st  # noqa: E402

from resume_analyzer.config import load_config  # noqa: E402
from resume_analyzer.matcher import JobDescription  # noqa: E402
from resume_analyzer.parser import ResumeParseError  # noqa: E402
from resume_analyzer.report import to_markdown  # noqa: E402
from resume_analyzer.service import analyse_text  # noqa: E402

st.set_page_config(page_title="Intelligent Resume Analyzer", page_icon="📄", layout="wide")
st.title("📄 Intelligent Resume Analyzer")

cfg = load_config()

with st.sidebar:
    st.header("Job requirements")
    title = st.text_input("Job title", "Backend Developer Intern")
    required = st.text_area("Required skills (comma separated)", "python, sql, git, rest api")
    nice = st.text_area("Nice-to-have skills", "docker, aws")
    years = st.number_input("Minimum years of experience", 0.0, 30.0, 0.0, 0.5)
    edu = st.selectbox("Minimum education", ["unknown", "diploma", "bachelor", "master", "phd"], 2)
    jd = st.text_area("Job description (optional, used for keyword match)")

upload = st.file_uploader("Upload resume (.txt, .md, .pdf)", type=["txt", "md", "pdf"])
pasted = st.text_area("...or paste resume text", height=200)

if st.button("Analyse", type="primary"):
    text = pasted
    try:
        if upload is not None:
            if upload.name.lower().endswith(".pdf"):
                from pypdf import PdfReader
                text = "\n".join((p.extract_text() or "") for p in PdfReader(upload).pages)
            else:
                text = upload.read().decode("utf-8", errors="replace")
        job = JobDescription(
            title=title,
            required_skills=[s for s in required.split(",") if s.strip()],
            nice_to_have_skills=[s for s in nice.split(",") if s.strip()],
            min_years_experience=years, min_education=edu, description=jd)
        report = analyse_text(text, job, cfg)
    except (ResumeParseError, ValueError) as exc:
        st.error(str(exc))
    else:
        m = report["match"]
        c1, c2 = st.columns(2)
        c1.metric("Overall score", f"{m['overall_score']}/100")
        c2.success(m["recommendation"])
        st.bar_chart(m["breakdown"])
        st.write("**Matched:**", ", ".join(m["matched_skills"]) or "-")
        st.write("**Missing:**", ", ".join(m["missing_skills"]) or "-")
        st.download_button("Download JSON", json.dumps(report, indent=2), "report.json")
        st.download_button("Download Markdown", to_markdown(report), "report.md")
