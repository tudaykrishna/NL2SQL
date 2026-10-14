# NL2SQL

Chat with a SQL database in plain English. NL2SQL is a multi-agent system built on
[Microsoft Semantic Kernel](https://github.com/microsoft/semantic-kernel) and Azure OpenAI.
It reads your schema, writes SQL, checks it, runs it against SQLite, fixes errors, and
explains the result. It runs as a FastAPI backend with a Streamlit chat UI.

## How it works

```
 Streamlit UI  ──POST /api/chat──▶  FastAPI  ──▶  Orchestrator Agent
                                                     │
                       ┌─────────────────────────────┼──────────────────────────────┐
                       ▼                             ▼                              ▼
              Classify request           SchemaGroundingPlugin            LLM sub-agents
         (CHIT_CHAT / FOLLOW_UP /     • get_schema_info()              • QueryBuilderAgent
                NL2SQL)               • execute_sql_script(sql)        • EvaluationAgent
                                               │                       • DebugAgent
                                               ▼                       • ExplanationAgent
                                          db.sqlite
```

For an `NL2SQL` request, the orchestrator runs this pipeline:

1. **Schema grounding**: `get_schema_info` reads the `table_description` and
   `table_columns` metadata tables.
2. **Query building**: the QueryBuilderAgent writes SQL using only that schema.
3. **Evaluation**: the EvaluationAgent checks syntax, schema correctness and date
   normalization, with retries.
4. **Execution**: `execute_sql_script` runs the SQL on the SQLite database.
5. **Debugging**: if execution fails, the DebugAgent suggests fixes, with retries.
6. **Explanation**: the ExplanationAgent writes the natural-language answer.

The orchestrator returns one JSON object:

```json
{
  "decision": "CHIT_CHAT | FOLLOW_UP | NL2SQL",
  "reason": "...",
  "action": ["Step1", "Step2"],
  "pipeline_log": [],
  "final_response": "...",
  "sql_debug": { "final_sql": "...", "execution_error": "..." }
}
```

Dates in generated SQL and responses are normalized to `DD-MM-YYYY`.

## Project structure

```
NL2SQL/
├── main.py                      # FastAPI app entry point (mounts routers)
├── agents/agent.py              # Kernel, Azure OpenAI service, and agent definitions
├── Prompt/Prompt.py             # System prompts for all agents
├── Tools/Plugin.py              # SchemaGroundingPlugin (schema lookup + SQL execution)
├── router/
│   ├── nl2sql.py                # POST /api/chat (one chat thread per user)
│   └── heaalth.py               # GET  /api/health
├── schemas/chatrequest.py       # Pydantic request model
├── UI/ui.py                     # Streamlit chat front end
├── requirements/
│   ├── csv_to_SQLite.py         # Load a folder of CSVs into SQLite + metadata tables
│   └── csv_to_postgres.py       # Same, for PostgreSQL
└── db.sqlite                    # Sample HR database
```

## Sample database

`db.sqlite` contains four synthetic HR datasets with 3,000 rows each:

| Table | Contents |
|---|---|
| `employee_data` | Employee records |
| `employee_engagement_survey_data` | Engagement survey responses |
| `recruitment_data` | Recruitment and candidate records |
| `training_and_development_data` | Training program participation |

It also contains the two metadata tables the agents use for schema grounding:

- `table_description(table_name, description)`
- `table_columns(table_name, column_name)`

## Setup

### 1. Install dependencies

Requires Python 3.10+.

```bash
python -m venv sk
# Windows: sk\Scripts\activate    macOS/Linux: source sk/bin/activate
pip install semantic-kernel fastapi uvicorn pydantic python-dotenv streamlit requests pandas
# Only needed for csv_to_postgres.py:
pip install sqlalchemy psycopg2-binary
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
incubator_key=<your-azure-openai-api-key>
incubator_endpoint=<your-azure-openai-endpoint>
model=<your-azure-openai-deployment-name>
```

### 3. (Optional) Use your own data

Put your CSV files in a folder and run:

```bash
python requirements/csv_to_SQLite.py
# You will be asked for the CSV folder and the SQLite output path
```

Each CSV becomes a table, and `table_description` / `table_columns` are filled in
automatically. Add a short description for each table in `table_description`, because
the agents rely on it to pick the right tables. Then set `DB_PATH` in `Tools/Plugin.py`
to point at your database (default: `./db.sqlite`).

For PostgreSQL:

```bash
python requirements/csv_to_postgres.py /path/to/csv_folder postgresql://user:pass@host:port/dbname
```

## Running

Start the API from the project root:

```bash
uvicorn main:app --reload
```

In a second terminal, start the UI:

```bash
streamlit run UI/ui.py
```

The UI expects the API at `http://127.0.0.1:8000/api/chat`. Pick or add a user in the
sidebar; each user keeps their own conversation thread.

## API

### `GET /api/health`

```json
{ "status": "ok" }
```

### `POST /api/chat`

```json
{
  "message": "How many employees are in each department?",
  "user": "User1",
  "db_dialect": "sqlite",
  "max_rows": 1000,
  "max_eval_retries": 3,
  "max_debug_retries": 3
}
```

`message` and `user` are required. The other fields are optional; `last_query`,
`last_sql` and `last_result_summary` can also be passed for follow-up context. The
response is the orchestrator's JSON output as a string.

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show the top 5 departments by headcount", "user": "User1"}'
```

## Tech stack

- **Semantic Kernel**: agents and plugin/function calling
- **Azure OpenAI**: LLM backend
- **FastAPI** + **Uvicorn**: REST API
- **Streamlit**: chat UI
- **SQLite** (PostgreSQL loader included)
