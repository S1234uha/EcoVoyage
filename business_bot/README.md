EcoVoyage Travel — Agent-Powered Business

Contents
- business_summary.txt — narrative about the business
- about_business.pdf — generated from the summary (run generate_pdf.py)
- business_agent.ipynb — notebook demo of the agent + tools
- app.py — Gradio ChatInterface app
- tools.py — tool functions and OpenAI tool schemas
- requirements.txt — project deps
- .env.example — copy to .env and set keys

Quickstart
1) Create a virtualenv and install deps:
   python -m venv .venv
   .venv\\Scripts\\pip install -r business_bot/requirements.txt

2) Generate the PDF (from the summary):
   .venv\\Scripts\\python business_bot/generate_pdf.py

3) Provide API key:
   copy business_bot/.env.example to .env and set OPENAI_API_KEY

4) Run the Gradio app:
   .venv\\Scripts\\python -m business_bot.app

Gemini setup
- In `.env`, use:
  - `PROVIDER=gemini`
  - `MODEL=gemini-1.5-flash` (or `gemini-1.5-pro`)
  - `GEMINI_API_KEY=...`

Notes
- Tools log to business_bot/logs/ as JSONL files.
- The agent uses OpenAI’s tool-calling to record leads and feedback.
