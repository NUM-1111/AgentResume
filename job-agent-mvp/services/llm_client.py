import json
import logging
import os
from typing import Any, Dict, Optional, Tuple, Type

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.enabled = bool(self.api_key)

        self._client: Optional[OpenAI] = None
        if self.enabled:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info("LLMClient 已启用，模型: %s，接口: %s", self.model, self.base_url)
        else:
            logger.warning("LLMClient 未启用：OPENAI_API_KEY 为空，将使用本地 fallback")

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_model: Type[BaseModel],
        fallback_data: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str]:
        """
        统一结构化输出入口。
        返回 (result_dict, source)，source 为 "llm" 或 "fallback:<原因>"
        """
        if not self.enabled or not self._client:
            return fallback_data, "fallback:no_api_key"

        try:
            # 将 JSON Schema 注入 system prompt，兼容不支持 json_schema response_format 的接口（如 DeepSeek）
            schema_hint = (
                f"\n\n请严格按照以下 JSON Schema 输出，只返回合法 JSON，不要有任何额外文字：\n"
                f"{json.dumps(schema_model.model_json_schema(), ensure_ascii=False, indent=2)}"
            )
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt + schema_hint},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            validated = schema_model.model_validate(data)
            return validated.model_dump(), "llm"
        except Exception as exc:
            reason = type(exc).__name__ + ": " + str(exc)
            logger.error("LLM 调用失败，降级到 fallback。原因: %s", reason)
            return fallback_data, f"fallback:{reason}"
