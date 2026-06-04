# Agent Arena

**AI Agent Comparison + Failure Analysis Dashboard**  
Built for Harbor Buildathon 2026

---

## What it does

Runs multiple AI agents on the same task and analyzes why they succeed or fail.

- **Leaderboard** — compare agents side by side
- **Trajectory Viewer** — inspect every step an agent took
- **AI Analysis** — Gemini AI diagnoses failure type, root cause, and suggests improvements

## Tech Stack

- Python
- Streamlit
- Plotly
- Pandas
- Gemini AI API
- Harbor SDK

## How to run

1. Clone the repo
2. Install dependencies:
3. pip install streamlit pandas plotly google-generativeai python-dotenv requests
4. Create a `.env` file with your Gemini API key:
5. Run the app:
   streamlit run app.py
## Built by

Pranjal Patil — Harbor Buildathon 2026
