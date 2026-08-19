"""知识库向量分块模型：向量直接存储在 PostgreSQL（pgvector 扩展）中。"""
import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VectorChunk(Base):
    """单个文档分块 + 其嵌入向量（pgvector 列，维度 = settings.embedding_dim）。"""

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    # upload | url | research
    source_type: Mapped[str] = mapped_column(String(20), default="upload")
    url: Mapped[str] = mapped_column(String(1000), default="")
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(get_settings().embedding_dim), nullable=False
    )
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
