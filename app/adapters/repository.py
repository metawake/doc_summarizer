from sqlalchemy.orm import Session

from app.domain import Document
from app.models import DocumentRecord


class SQLiteRepository:
    """Persists documents to SQLite via SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, document: Document) -> Document:
        record = DocumentRecord(
            filename=document.filename,
            summary=document.summary,
            page_count=document.page_count,
            created_at=document.created_at,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        document.id = record.id
        return document

    def get_recent(self, limit: int = 5) -> list[Document]:
        records = (
            self.db.query(DocumentRecord)
            .order_by(DocumentRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            Document(
                id=r.id,
                filename=r.filename,
                summary=r.summary,
                page_count=r.page_count,
                created_at=r.created_at,
            )
            for r in records
        ]
