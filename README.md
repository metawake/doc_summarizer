# PDF Summary AI

Upload PDFs, get AI summaries. Handles docs up to 50MB / 100 pages, including tables and images.

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

Default port is 8000. Override with `PORT=8080 docker compose up`.

Container runs as non-root user and has a healthcheck on `/health`.

## Tests

```bash
pytest -v
```

11 tests covering parser, chunking logic, API endpoints. Test stubs were written before implementations (see commit history).

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/upload` | Upload PDF (multipart, field: `file`), returns summary |
| `GET` | `/api/history` | Last 5 processed documents |

## Architecture

Hexagonal (ports & adapters). Core logic talks to the outside world through Protocol interfaces. Concrete implementations are swappable.

```
app/
  ports.py            # PDFParser, Summarizer, DocumentRepository protocols
  domain.py           # Document dataclass
  adapters/
    pdf_parser.py     # pymupdf4llm
    summarizer.py     # OpenAI + map-reduce chunking
    repository.py     # SQLite via SQLAlchemy
  main.py             # FastAPI routes, wiring
  config.py           # pydantic-settings, all config via env
  database.py         # SQLAlchemy setup
static/index.html     # single-page frontend (Tailwind CDN)
tests/
```

Why hexagonal for a small project: makes it easy to swap things. Replace SQLite with Postgres - write a new adapter, nothing else changes. Same for switching summarization providers.

## Key decisions

- **pymupdf4llm** over PyPDF2 - the spec requires table and image support. PyPDF2 strips tables and ignores images. pymupdf4llm outputs markdown with table structure preserved.
- **OpenAI SDK directly**, no LangChain - less abstraction, full control over the chunking logic. Easier to debug and explain.
- **Map-reduce chunking** - long docs are split by paragraphs (token-counted via tiktoken), each chunk summarized, then combined into a final summary. Handles 100-page docs without hitting token limits.
- **SQLite** - one less container. Pragmatic for a demo with 5 records.
- **Summary prompt in config** - overridable via `SUMMARY_PROMPT` env var. Prompt tuning shouldn't require code changes.

## Configuration

All via environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Required |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for summarization |
| `SUMMARY_PROMPT` | (see config.py) | System prompt, overridable |
| `MAX_UPLOAD_SIZE_MB` | `50` | Upload size limit |
| `DATABASE_URL` | `sqlite:///./documents.db` | DB connection |
| `PORT` | `8000` | Host port (Docker) |

## Assumptions

- OpenAI API key has sufficient quota and billing is active.
- PDFs are text-based or have extractable text layers. Scanned-image-only PDFs would need OCR (not in scope).
- "Last 5 documents" means last 5 by processing time, no pagination needed.
- Single-user demo - no auth, no concurrent upload handling.

## Out of scope (would add with more time)

- **RAG pipeline** - store chunk embeddings in a vector DB (e.g. Weaviate, Pinecone) for semantic retrieval instead of brute-force summarization. The chunking logic already here is the same splitting strategy used for embedding generation.
- **Structured LLM output** - use Pydantic models with OpenAI's structured output mode to validate and type summary responses, catch malformed completions.
- **Output guardrails** - validate summary quality against source text, enforce format and length constraints, flag hallucinations.
- **Evaluation pipeline** - measure summary quality systematically (e.g. DeepEval) rather than manual spot-checking.
- **Multi-model support** - swap between GPT-4o and Claude via the adapter pattern the architecture already supports.
- **Background processing** - task queue for large files so the request doesn't block.
- **Streaming responses** - show summary as it generates, token by token.

## Development approach

This project favors clarity and working software over architectural complexity, matching the 2-3 hour scope. Tradeoffs are deliberate - the commit history shows the progression from interfaces to implementations.
