# Resume Analyzer

A full-stack web app that scores a resume on structure, wording, and measurable impact, matches it against a target job description, and gives AI-generated feedback with rewritten bullet points.

**Live demo:** _add your deployed URL here after deployment_

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-black)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Drag-and-drop upload** for PDF, DOCX, or TXT resumes
- **Rule-based scoring engine** (always runs, no API key required) checking:
  - Contact info completeness (email, phone, LinkedIn/GitHub)
  - Presence of core resume sections
  - Use of strong action verbs vs. weak/passive phrasing
  - Quantified, measurable achievements
  - Resume length
  - Keyword match against a pasted job description
- **AI-powered feedback layer** using the Claude API: a plain-language summary, strengths, improvements, and rewritten bullet points -- with automatic, transparent fallback to the rule-based feedback if no API key is configured or the request fails
- **Fully responsive UI** built with vanilla HTML/CSS/JS, no frontend framework or build step
- **Export report** button for a print-friendly version of the results
- Nothing is stored: files are processed in memory for a single request and discarded

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python, Flask, Gunicorn |
| Resume parsing | PyPDF2, python-docx |
| AI feedback | Anthropic Claude API (optional) |
| Frontend | HTML5, CSS3 (custom properties, no framework), vanilla JS |
| Deployment | Render (free tier) |

## Project structure

```
resume-analyzer/
├── app.py                  # Flask routes and API
├── utils/
│   ├── parser.py           # Text extraction from PDF/DOCX/TXT
│   └── analyzer.py         # Rule-based scoring + Claude API integration
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/script.js
├── requirements.txt
├── Procfile                # gunicorn start command for deployment
├── render.yaml             # one-click Render deployment config
└── .env.example
```

## Running locally

```bash
git clone https://github.com/<your-username>/resume-analyzer.git
cd resume-analyzer

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # optional: add ANTHROPIC_API_KEY to enable AI feedback

python app.py
```

Visit `http://localhost:5000`.

The app works fully without an API key -- it just uses rule-based feedback instead of AI-generated feedback. To enable AI feedback, get a key from the [Anthropic Console](https://console.anthropic.com/) and add it to `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Deployment

This project deploys for free on [Render](https://render.com):

1. Push this repo to GitHub (see below).
2. On Render, click **New > Web Service** and connect the repo. Render will detect `render.yaml` automatically.
3. Add your `ANTHROPIC_API_KEY` as an environment variable in the Render dashboard (optional).
4. Deploy. Render gives you a live `.onrender.com` URL.

## How it's scored

Each category is scored 0-100 and combined into a weighted overall score. When a job description is provided, keyword match is included and the other weights shrink proportionally so the score stays meaningful for that specific role.

## License

MIT
