# PDF Summary AI

Upload PDFs, get AI summaries. Handles docs up to 50MB/100 pages, including tables and images.

## Architecture

Hexagonal layout — ports (Protocols) define boundaries, adapters implement them:

- `PDFParser` → pymupdf4llm (markdown extraction with table support)
- `Summarizer` → OpenAI gpt-4o-mini (map-reduce chunking for long docs)
- `DocumentRepository` → SQLite

```
app/
  ports.py, domain.py       # core interfaces + domain model
  adapters/                  # concrete implementations
  main.py                    # FastAPI routes
  config.py, database.py     # settings + db setup
static/index.html            # frontend
tests/
```

## Run locally

```bash
cp .env.example .env   # add your OPENAI_API_KEY

uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
cp .env.example .env   # add your OPENAI_API_KEY
docker compose up --build
```

Then open http://localhost:8000

## Tests

```bash
pytest -v
```

## API

- `GET /health` — health check
- `POST /api/upload` — upload PDF (multipart, field: `file`), returns summary
- `GET /api/history` — last 5 processed docs

## Decisions

- pymupdf4llm over PyPDF2 — actually handles tables and images
- OpenAI SDK directly, no LangChain — less magic, easier to reason about
- SQLite — no extra container for a demo
- Map-reduce chunking — split long docs, summarize chunks, combine

## Would improve

- Background processing (task queue) for large files
- Streaming responses
- Section-aware chunking instead of naive paragraph splits
- Vision API for embedded images
- Pagination on history
