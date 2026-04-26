# Demography Insights — Suburb Finder AI

A Streamlit-based SaaS app that lets authenticated users query Australian demographic data using natural language. Questions are answered by a LangChain SQL agent backed by Google Gemini and Google BigQuery.

---

## Project Structure

```
demography-insights/
├── app.py                    # Main Streamlit entry point
│
├── agent/
│   ├── bigquery_client.py    # Authenticated BigQuery client for agent queries
│   ├── explore_data.py       # Data exploration utilities
│   ├── prompts.py            # Few-shot prompt prefix + LangChain SQL agent setup
│   ├── sql_agent.py          # (reserved)
│   └── tools.py              # Custom LangChain tools
│
├── auth/
│   ├── bigquery_auth.py      # Verifies users against BigQuery customer table
│   ├── login.py              # Streamlit sidebar login UI
│   ├── rbac.py               # Tier-based query limits (free / basic / pr)
│   └── users.py              # Local usage tracking (read/write users.json)
│
├── db/
│   └── bigquery_client.py    # Shared BigQuery client for auth queries
│
├── chat_history/             # Per-user conversation history (JSON files)
│
├── eval/
│   ├── golden_dataset.json   # Reference Q&A pairs for evaluation
│   ├── judge.py              # LLM-as-judge scoring logic
│   └── run_eval.py           # Evaluation runner script
│
├── .streamlit/
│   └── config.toml           # Streamlit theme and server config
│
├── users.json                # Runtime usage store (created automatically)
├── .env                      # Environment variables — not committed
├── service_account.json      # GCP service account key — not committed
└── requirements.txt          # Python dependencies
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io) |
| LLM | Google Gemini (`gemini-2.5-flash-lite`) via `langchain-google-genai` |
| Agent framework | [LangChain](https://www.langchain.com) SQL agent |
| Data warehouse | [Google BigQuery](https://cloud.google.com/bigquery) |
| BQ connector | `sqlalchemy-bigquery` + `google-cloud-bigquery` |
| Auth backend | BigQuery (`demografy.ref_tables.dev_customers`) |
| Observability | [LangSmith](https://smith.langchain.com) tracing |
| Env management | `python-dotenv` |

**Data source:** `demografy.prod_tables.a_master_view` — Australian suburb-level KPIs including prosperity, diversity, education, rental access, social housing, and more.

---

## How Authentication & Tiers Work

1. Users log in with a **User ID + email** pair that is verified against BigQuery.
2. Each user is assigned a **tier** (`free`, `basic`, or `pr`) stored in BigQuery.
3. Question limits per tier are configured via environment variables:
   - `free` — 3 questions per 24 hours
   - `basic` — 20 questions per 24 hours
   - `pr` — 50 questions per 24 hours (`-1` = unlimited)
4. Usage is tracked locally in `users.json` and resets **24 hours after the last login**.
5. A warning banner appears when the user has consumed 80 %+ of their limit.

---

## Setup

### Prerequisites

- Python 3.11+
- A Google Cloud project with BigQuery enabled
- A GCP service account with BigQuery read access
- A Gemini API key
- A LangSmith API key (optional, for tracing)

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd demography-insights
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
GOOGLE_APPLICATION_CREDENTIALS=./service_account.json
GEMINI_API_KEY=your_gemini_api_key
BIGQUERY_PROJECT=your_gcp_project_id

# LangSmith tracing (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=your_project_name

# Tier question limits (-1 = unlimited)
FREE_TIER_LIMIT=5
BASIC_TIER_LIMIT=20
PR_TIER_LIMIT=50
```

### 3. Add the GCP service account key

Place your service account JSON file at the path referenced by `GOOGLE_APPLICATION_CREDENTIALS` (default: `./service_account.json`). This file is gitignored — do not commit it.

### 4. Run the app

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

---

## Running the Evaluation Suite

```bash
python eval/run_eval.py
```

This runs the golden dataset through the agent and scores responses using an LLM-as-judge (`eval/judge.py`).