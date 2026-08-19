"""FastAPI 应用入口。"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import knowledge, research, websocket
from app.config import get_settings
from app.core.database import init_db
from app.rag import vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 开发环境快速建表（生产环境请用 alembic upgrade head）
    if settings.app_env == "development":
        try:
            await init_db()
            logger.info("数据库表已就绪")
        except Exception as e:  # noqa: BLE001
            logger.warning("数据库初始化失败（请检查 DATABASE_URL）: %s", e)
    # 确保 pgvector 向量表（PostgreSQL 扩展 + document_chunks 表 + HNSW 索引）就绪
    try:
        await vector_store.ensure_vector_table()
        logger.info("pgvector 向量表就绪")
    except Exception as e:  # noqa: BLE001
        logger.warning("向量表初始化失败（知识库功能将降级）: %s", e)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router)
app.include_router(knowledge.router)
app.include_router(websocket.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
