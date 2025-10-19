EcoVoyage Travel — Agent-Powered Business Assistant

EcoVoyage is a fictional, sustainability‑first travel agency with a smart concierge that:
- Answers questions about trips, mission, team, and services
- Captures leads (name, email, notes) via tool-calling
- Logs unknown questions as feedback for follow‑up
- Uses your business summary and PDF as trusted context
- Runs as a friendly Gradio chatbot powered by OpenAI

Project Layout
- `business_bot/` — app, tools, notebook, summary, PDF, and config
  - `app.py` — Gradio ChatInterface app (OpenAI by default)
  - `tools.py` — lead + feedback tools and schemas
  - `business_summary.txt` and `about_business.pdf` — business context
  - `business_agent.ipynb` — notebook demo
  - `requirements.txt` — dependencies
  - `.env.example` — copy to `.env` and set keys

Quickstart (OpenAI)
1) Create a virtualenv and install dependencies:
   `python -m venv .venv`
   `.venv\Scripts\pip install -r business_bot\requirements.txt`

2) Generate the PDF (from the summary):
   `.venv\Scripts\python business_bot\generate_pdf.py`

3) Configure environment (OpenAI):
   - Copy `business_bot\.env.example` to `business_bot\.env`
   - Set in `business_bot\.env`:
     - `PROVIDER=openai`
     - `MODEL=gpt-4o-mini` (or `gpt-4o`, `gpt-4.1-mini`)
     - `OPENAI_API_KEY=sk-...`

4) Run the chatbot:
   `.venv\Scripts\python -m business_bot.app`
   Open the local URL shown (e.g., http://127.0.0.1:7860)

Try These Prompts
- “What’s EcoVoyage Travel’s mission and services?”
- “Plan a 7‑day eco‑friendly Costa Rica itinerary for a family under $2,500.”
- “I’m Alex, alex@example.com — interested in Patagonia in November. Next steps?”
- “What’s your refund policy for volcanic disruptions?” (logs feedback)

Logging
- Leads: `business_bot\logs\leads.jsonl`
- Feedback: `business_bot\logs\feedback.jsonl`

Notes
- OpenAI is the default provider in this project.
- Keep real API keys only in `business_bot\.env` (never commit secrets). `.gitignore` excludes env and logs.

Optional: Gemini
- If you want to try Gemini instead of OpenAI, set in `business_bot\.env`:
  - `PROVIDER=gemini`
  - `MODEL=gemini-1.5-flash-latest` (or `gemini-1.5-pro-latest`)
  - `GEMINI_API_KEY=...`
