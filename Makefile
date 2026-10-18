.PHONY: install test lint run ui
install:
	pip install -r requirements-dev.txt
test:
	pytest
lint:
	ruff check .
run:
	PYTHONPATH=src python -m resume_analyzer data/sample/resume.txt -j data/sample/job.json --stdout
ui:
	streamlit run app.py
