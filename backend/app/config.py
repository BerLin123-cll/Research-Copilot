"""应用全局配置：从环境变量 / .env 加载。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # 同时支持从 backend/ 与项目根目录运行时加载 .env
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- 通用 ----------
    app_name: str = "Research Copilot"
    app_env: str = "development"  # development | production
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # ---------- LLM（OpenAI 兼容，默认 DeepSeek） ----------
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 8192

    # ---------- Embedding（默认 local：fastembed 开源免费本地模型） ----------
    embedding_provider: str = "local"  # local=fastembed 本地模型 | openai=OpenAI 兼容 API
    embedding_model: str = "BAAI/bge-small-zh-v1.5"  # 本地模型名；效果优先可换 intfloat/multilingual-e5-large
    embedding_dim: int = 512  # 向量维度：需与 EMBEDDING_MODEL 匹配（bge-small-zh-v1.5=512，multilingual-e5-large=1024）；换模型需同步修改并重建向量表
    embedding_base_url: str = "https://api.openai.com/v1"  # 仅 openai 模式
    embedding_api_key: str = ""  # 仅 openai 模式

    # ---------- 数据库（默认 PostgreSQL + pgvector，生产/上线推荐） ----------
    database_url: str = "postgresql+asyncpg://research:research@localhost:5432/research"
    sync_database_url: str = "postgresql+psycopg2://research:research@localhost:5432/research"
    # 向量表 document_chunks 由 alembic 迁移/启动初始化自动创建（vector 扩展 + 表 + HNSW 索引）

    # ---------- Agent 参数 ----------
    agent_max_iterations: int = 3
    web_search_max_results: int = 8
    arxiv_max_results: int = 5
    fetch_timeout: float = 15.0
    playwright_enabled: bool = False
    rag_top_k: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50
    # 是否将研究过程中收集的资料自动写入知识库（供后续深度问答）
    save_research_to_kb: bool = True
    # 单个研究任务写入知识库的最大分块数（防止膨胀）
    research_kb_max_chunks: int = 30

    # ---------- 搜索新鲜度 ----------
    # DDG 时间过滤：""（不限）| d=一天内 | w=一周内 | m=一个月内 | y=一年内
    web_search_timelimit: str = ""
    # 同时发起的 DuckDuckGo 搜索并发数上限（防止同 IP 被限流）
    web_search_max_concurrency: int = 2
    # arXiv 排序：relevance=相关度 | submitted_date=最新提交优先 | updated_date=最近更新优先
    arxiv_sort_by: str = "relevance"

    # ---------- 并发与超时 ----------
    # 同时运行的研究任务上限（超出排队等待，状态保持 pending）
    max_concurrent_research: int = 3
    # 单个研究任务整图执行的看门狗超时（秒），超时标记为 failed
    agent_task_timeout: float = 900.0
    # LLM 单次请求超时（秒）与失败重试次数（429/5xx 指数退避）
    llm_timeout: float = 120.0
    llm_max_retries: int = 3
    # 同步阻塞工具（DDG / arXiv）单次调用超时（秒）
    tool_timeout: float = 30.0

    # ---------- 端口 ----------
    backend_port: int = 8000
    frontend_port: int = 8080

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
