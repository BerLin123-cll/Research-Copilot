"""文档资料模型（知识库）。"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255))
    # upload | url
    source_type: Mapped[str] = mapped_column(String(20), default="upload")
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # processing | ready | failed
    status: Mapped[str] = mapped_column(String(20), default="processing", index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "source_type": self.source_type,
            "url": self.url,
            "status": self.status,
            "chunk_count": self.chunk_count,
            "meta": self.meta,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
