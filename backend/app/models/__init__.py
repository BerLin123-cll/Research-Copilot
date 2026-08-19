"""数据模型注册（确保 Base.metadata 收集所有表）。"""
from app.models.chat import ChatMessage
from app.models.document import Document
from app.models.report import Report
from app.models.research import ResearchTask
from app.models.vector_chunk import VectorChunk

__all__ = ["ChatMessage", "Document", "Report", "ResearchTask", "VectorChunk"]
