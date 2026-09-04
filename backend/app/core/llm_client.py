"""LLM 统一封装：基于 OpenAI 兼容接口（DeepSeek / OpenAI / Claude 网关等）。

通过环境变量切换 base_url / model / api_key 即可无缝切换供应商。
"""
import asyncio
import logging
from typing import Any

from openai import APITimeoutError, APIStatusError, AsyncOpenAI, RateLimitError

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        s = get_settings()
        self.settings = s
        # api_key 为空时使用占位符，避免本地开发报错（请求时会真实失败）
        self.client = AsyncOpenAI(
            api_key=s.llm_api_key or "sk-placeholder",
            base_url=s.llm_base_url,
            # 单次请求超时（秒），防止 LLM 长时间无响应拖住任务
            timeout=s.llm_timeout,
            # 禁用 SDK 默认重试，使用下方自定义指数退避重试（避免重复叠加）
            max_retries=0,
        )
        self.model = s.llm_model
        self.temperature = s.llm_temperature
        self.max_tokens = s.llm_max_tokens

    async def chat(
        self,
        messages: list[dict[str, str]],
        json_mode: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """发送对话请求，返回文本内容。json_mode=True 时要求模型输出 JSON 对象。

        429 / 超时 / 5xx 时按指数退避自动重试（最多 llm_max_retries 次）。
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        retries = self.settings.llm_max_retries
        last_err: Exception | None = None
        for attempt in range(retries + 1):
            try:
                resp = await self.client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except (RateLimitError, APITimeoutError) as e:
                last_err = e
            except APIStatusError as e:
                # 只对 5xx 服务端错误重试；4xx（如 401/400）重试无意义，快速失败
                if e.status_code < 500:
                    raise
                last_err = e
            if attempt >= retries:
                break
            wait = min(2**attempt, 30)  # 1s → 2s → 4s …（上限 30s）
            logger.warning(
                "LLM 请求失败（第 %d/%d 次）: %s，%ds 后重试", attempt + 1, retries + 1, last_err, wait
            )
            await asyncio.sleep(wait)
        raise last_err or RuntimeError("LLM 请求失败")


# 全局单例
llm = LLMClient()
