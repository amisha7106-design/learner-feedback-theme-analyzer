# Learner Feedback Theme Analyzer — Project 019

A Python + Streamlit + NLP + SQLite prototype that helps education teams review learner feedback, identify sentiment signals and recurring themes, and prepare evidence-grounded quality-improvement reports.

## Features
- Dark navy / blue-violet responsive Streamlit interface inspired by the supplied original HTML design.
- Student feedback form and CSV import with validation.
- NLP text cleaning, language detection, sentiment analysis and TF-IDF theme clustering.
- Teacher dashboard with sentiment and theme charts.
- SQLite persistence for courses, trainers, feedback forms/responses, themes, reports and audit events.
- Evidence-bounded OpenAI report generation when an API key is configured; transparent offline report fallback otherwise.
- CSV template and Markdown report downloads.

## Run locally (Windows)
1. Install Python 3.10 or newer.
2. Extract the ZIP and open the `learner-feedback-theme-analyzer` folder in VS Code.
3. Open Terminal and run:
   ```powershell
   python -m venv .venv
   .venv\\Scripts\\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Open the local URL printed in the terminal.

## Optional OpenAI integration
Create a `.env` file in this project folder (do not upload it to GitHub):
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```
Without a key, the app uses a clearly labelled local report template. Never commit API keys or real learner personal data.

## Deploy on Streamlit Community Cloud
1. Push this project folder to a GitHub repository (include `app.py`, `src/`, `data/sample_feedback.csv`, `requirements.txt`, `.streamlit/config.toml`, `tests/`, and README).
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**, select the repository and branch, and set **Main file path** to `app.py` (or the relative path if you placed it in a subfolder).
4. In **App settings → Secrets**, add:
   ```toml
   OPENAI_API_KEY = "your_api_key_here"
   OPENAI_MODEL = "gpt-4.1-mini"
   ```
5. Deploy. Test the public app using synthetic sample feedback first.
6. ##PROJECT DEMO LINK WATCH MY PROJECT DEMO https://drive.google.com/file/d/1m9W-S7ZpRVwGX1RtHD_YuyDRca2L1GDY/view?usp=drive_link

### Important deployment note
Streamlit Community Cloud local filesystems are not guaranteed to be durable across app restarts/redeployments. This prototype uses SQLite for demonstration. For production use, move the database to a managed persistent database and add authentication/role-based access before collecting real learner feedback.

## Test
```bash
python -m pytest -q
```

## Data and responsible use
Use anonymized, synthetic or institution-approved data. The report generator sends a limited set of feedback excerpts to OpenAI only when an API key is configured. Review your institution's privacy rules and obtain approval before enabling external AI processing. AI summaries are decision-support and require human review.

## Project structure
```text
app.py
src/
  analyzer.py
  config.py
  database.py
  llm_report.py
  main.py
  nlp.py
  utils.py
data/
  sample_feedback.csv
tests/
.streamlit/config.toml
requirements.txt
README.md
```
