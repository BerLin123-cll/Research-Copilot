"""文本嵌入服务。

默认 **local 模式**：fastembed + 开源免费本地模型（BAAI/bge-small-zh-v1.5，
ONNX 推理、无需 GPU、无需 API Key，模型首次使用自动下载），中文效果优秀。
可选 **openai 模式**：OpenAI 兼容 Embedding API（text-embedding-3-small 等）。
通过环境变量 EMBEDDING_PROVIDER 切换。
"""
import asyncio
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class LocalEmbedder:
    """fastembed 本地模型（开源免费）。"""

    def __init__(self) -> None:
        s = get_settings()
        self.model_name = s.embedding_model
        self._dim = s.embedding_dim
        self._model: Any = None
        # e5 系列（intfloat/*）官方要求 query/passage 前缀，否则检索效果明显下降
        self._e5 = self.model_name.startswith("intfloat/")

    @property
    def dim(self) -> int:
        return self._dim

    def _get_model(self) -> Any:
        if self._model is None:
            from fastembed import TextEmbedding

            logger.info("加载本地嵌入模型 %s（首次使用会自动下载，约 100MB）…", self.model_name)
            self._model = TextEmbedding(model_name=self.model_name)
            try:
                meta = self._model.get_model_meta()
                meta_dim = getattr(meta, "dim", None)
                if meta_dim:
                    self._dim = int(meta_dim)
                    logger.info("嵌入模型 %s 向量维度: %s", self.model_name, self._dim)
            except Exception:  # noqa: BLE001
                pass
        return self._model

    @staticmethod
    def _embed_sync(model: Any, texts: list[str]) -> list[list[float]]:
        # fastembed 的 embed 返回生成器，且为同步推理
        return [list(map(float, v)) for v in model.embed(texts)]

    async def embed(self, texts: list[str], prefix: str = "passage") -> list[list[float]]:
        """批量生成向量（放入线程池避免阻塞事件循环）。

        prefix: passage（文档分块，默认）| query（检索问题）| none（e5 模型不加前缀）
        """
        if not texts:
            return []
        if self._e5 and prefix != "none":
            tag = "query: " if prefix == "query" else "passage: "
            texts = [tag + t for t in texts]
        model = self._get_model()
        return await asyncio.to_thread(self._embed_sync, model, texts)

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed([text], prefix="query")
        return vectors[0] if vectors else []


class OpenAIEmbedder:
    """OpenAI 兼容 Embedding API（可选模式）。"""

    def __init__(self) -> None:
        s = get_settings()
        self.settings = s
        self.client = AsyncOpenAI(
            api_key=s.embedding_api_key or "sk-placeholder",
            base_url=s.embedding_base_url,
        )
        self.model = s.embedding_model
        self._dim = s.embedding_dim

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            resp = await self.client.embeddings.create(model=self.model, input=texts)
            ordered = sorted(resp.data, key=lambda x: x.index)
            return [item.embedding for item in ordered]
        except Exception as e:  # noqa: BLE001
            logger.error("embedding 失败: %s", e)
            raise

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed([text])
        return vectors[0] if vectors else []


def _build_embedder() -> LocalEmbedder | OpenAIEmbedder:
    s = get_settings()
    if s.embedding_provider == "openai":
        return OpenAIEmbedder()
    return LocalEmbedder()


# 全局单例
embedder = _build_embedder()
