import json
import os
from typing import Any, Dict, Optional, Type

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.enabled = bool(self.api_key)

        self._client: Optional[OpenAI] = None
        if self.enabled:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_model: Type[BaseModel],
        fallback_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        统一结构化输出入口。
        - 有 API Key: 优先调用 LLM + JSON Schema 约束
        - 无 API Key 或调用失败: 返回本地 fallback
        """
        if not self.enabled or not self._client:
            return fallback_data

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_model.__name__,
                        "schema": schema_model.model_json_schema(),
                    },
                },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            validated = schema_model.model_validate(data)
            return validated.model_dump()
        except Exception:
            return fallback_data

