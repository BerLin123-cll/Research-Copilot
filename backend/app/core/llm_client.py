"""LLM 统一封装：基于 OpenAI 兼容接口（DeepSeek / OpenAI / Claude 网关等）。

通过环境变量切换 base_url / model / api_key 即可无缝切换供应商。
"""
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings


class LLMClient:
    def __init__(self) -> None:
        s = get_settings()
        self.settings = s
        # api_key 为空时使用占位符，避免本地开发报错（请求时会真实失败）
        self.client = AsyncOpenAI(
            api_key=s.llm_api_key or "sk-placeholder",
            base_url=s.llm_base_url,
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
        """发送对话请求，返回文本内容。json_mode=True 时要求模型输出 JSON 对象。"""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = await self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""


# 全局单例
llm = LLMClient()
