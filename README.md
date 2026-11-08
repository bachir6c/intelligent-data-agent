# Intelligent Data Agent V2

A Python agent for SQL banking data and local reference documents. FastAPI exposes
its tools and Streamlit provides the chat and document upload interface.

## Features

- Read-only SQL, schema inspection and tool-based error recovery.
- Pandas statistical analysis, anomaly and trend detection.
- Matplotlib charts shared between FastAPI and Streamlit containers.
- Retrieval-augmented answers from UTF-8 `.txt` and `.md` documents, with
  `[filename#chunk]` references. BM25 keyword ranking retrieves overlapping
  passages; the Groq model uses these passages to generate answers.
- Hybrid questions can use SQL facts and document context in the same tool loop.
- Pytest tests and a GitHub Actions workflow for tests and Docker image builds.

## Run with Docker

Use Python 3.11 for local development. For Docker, start Docker Desktop with Linux
containers. From this project folder:

1. Create `.env` containing `GROQ_API_KEY=your-key`. Optionally set `GROQ_MODEL`.
2. Ensure `data/banking.db` exists. Existing data is mounted read-only by the API.
3. Run `docker compose up --build`.
4. Open http://localhost:8501. API docs: http://localhost:8000/docs.
5. Stop with Ctrl+C and `docker compose down`. Local data and documents remain.

`Dockerfile` builds the Python environment. `compose.yaml` starts the API and UI,
waits for API health, and mounts persistent charts and reference documents.
`.dockerignore` keeps secrets, datasets and local environments out of builds.
Only the API receives the Groq key. Published ports bind to localhost.

Local Streamlit defaults to `http://127.0.0.1:8000/query`; Docker sets
`API_URL=http://api:8000/query`. Uploaded documents live in `data/documents/` on
the host, mounted at `/app/documents` in the API container. They are not committed.

## Document demonstration

Upload `docs/sample_documents/demo_policy.txt` through the sidebar, then ask:

- According to the demonstration policy, when do Mobile transfers require supervisor approval? Cite the source.
- Count completed Mobile transactions for agency 4 in February 2025, then explain the review policy using the uploaded document. Cite the document.
- What does the uploaded policy say about mortgage interest rates?

The last question should produce an explicit statement that the document does not
provide that information. The example is synthetic and is not real bank policy.
Duplicate filenames return an error; rename a file before uploading another version.

Supported files: UTF-8 text/Markdown, maximum 1 MB each. PDFs, scanned documents,
embeddings, multilingual semantic matching and per-user collections are not
implemented. Retrieval is keyword-based: use words present in the documents.
Document instructions are treated as untrusted data in the agent prompt; this is
not a guarantee against all prompt-injection attacks. This is a local, single-user
demo, without authentication or public hosting hardening.

## Tests

Activate a working Python environment, then run:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests -v
```

Tests generate a seeded banking database in a temporary directory. They do not
need your private database or a real Groq API key. Tests cover SQL validation,
analysis anomalies, API behavior, document ranking and uploads, chart handoff,
and simulated hybrid/tool-retry conversations. Simulated model tests check the
tool loop; live model behavior must also be checked separately.

`.github/workflows/tests.yml` runs tests and builds Docker on pushes and pull
requests. Adding the file does not prove that a hosted run has succeeded: push
it to GitHub and inspect the Actions tab. No Groq secret is needed for CI.

## Benchmark

`benchmarks/questions.json` contains 50 original evaluation cases. The existing
`benchmarks/results.json` records 50/50 passing in a historical run; it is not a
fresh validation of every later change and does not evaluate document retrieval.
The checks are programmed assertions, not proof of general model accuracy.

By default the benchmark resumes and skips previously passed cases. To rerun
all cases without overwriting historical results:

```powershell
python src/run_benchmark.py --fresh --output benchmarks/results-current.json
```

This calls Groq using your configured key and may incur usage or hit rate limits.

## Creating demo data from scratch

Only in a new project copy with no data you need to keep, run these scripts in
order. Generation replaces existing dataset contents:

```powershell
python src/create_database.py
python src/generate_data.py
python src/inject_anomalies.py
python src/add_anomalies.py
```

## Structure

- `src/agent.py`: model tool definitions, routing and execution loop.
- `src/document_tools.py`: text storage, chunking and BM25 retrieval.
- `src/agent_service.py`: structured answers and chart path handling.
- `src/sql_tools.py`, `src/analysis_tools.py`, `src/visualization_tools.py`: data tools.
- `api/main.py`: health, query and document upload endpoints.
- `streamlit_app.py`: chat, charts and document upload.
- `tests/`: isolated automated checks.
- `benchmarks/`: evaluation cases and saved results.
