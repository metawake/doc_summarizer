import logging
import shutil
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import APIError, AuthenticationError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adapters.pdf_parser import PyMuPDFParser
from app.adapters.repository import SQLiteRepository
from app.adapters.summarizer import OpenAISummarizer
from app.config import settings
from app.database import get_db, init_db
from app.domain import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(exist_ok=True)

static_dir = Path(__file__).parent.parent / "static"

# adapters
pdf_parser = PyMuPDFParser()
summarizer = OpenAISummarizer()


class SummaryResponse(BaseModel):
    id: int | None
    filename: str
    summary: str
    page_count: int
    created_at: str


class HistoryResponse(BaseModel):
    documents: list[SummaryResponse]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="PDF Summary AI", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/upload", response_model=SummaryResponse)
def upload_pdf(file: UploadFile, db: Session = Depends(get_db)) -> SummaryResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    safe_name = Path(file.filename).name
    file_path = UPLOAD_DIR / safe_name
    try:
        with file_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.max_upload_size_mb:
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds {settings.max_upload_size_mb}MB limit",
            )

        logger.info("Processing %s (%.1f MB)", file.filename, file_size_mb)
        start = time.time()

        md_text = pdf_parser.parse(file_path)
        page_count = pdf_parser.get_page_count(file_path)
        summary = summarizer.summarize(md_text)

        elapsed = time.time() - start
        logger.info("Completed %s: %d pages in %.1fs", file.filename, page_count, elapsed)

        repo = SQLiteRepository(db)
        doc = Document(filename=file.filename, summary=summary, page_count=page_count)
        doc = repo.save(doc)

        return SummaryResponse(
            id=doc.id,
            filename=doc.filename,
            summary=doc.summary,
            page_count=doc.page_count,
            created_at=doc.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except AuthenticationError as e:
        logger.error("OpenAI API key is missing or invalid")
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured. Please check the API key.",
        ) from e
    except APIError as e:
        logger.error("OpenAI API error: %s", e)
        msg = "AI service is temporarily unavailable. Please try again later."
        if "insufficient_quota" in str(e):
            msg = "AI service quota exceeded. Please try again later."
        raise HTTPException(status_code=503, detail=msg) from e
    except Exception as e:
        logger.exception("Failed to process %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}") from e
    finally:
        file_path.unlink(missing_ok=True)


@app.get("/api/history", response_model=HistoryResponse)
def get_history(db: Session = Depends(get_db)) -> HistoryResponse:
    repo = SQLiteRepository(db)
    docs = repo.get_recent(limit=5)
    return HistoryResponse(
        documents=[
            SummaryResponse(
                id=d.id,
                filename=d.filename,
                summary=d.summary,
                page_count=d.page_count,
                created_at=d.created_at.isoformat(),
            )
            for d in docs
        ]
    )
