import json
import os
from typing import Any, Dict, Optional, Type

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()

# 这个类是用来调用LLM的，它有以下几个功能：
# 1. 它有api_key和base_url，这两个是用来调用LLM的。
# 2. 它有model，这个是用来选择LLM模型的。
# 3. 它有enabled，这个是用来判断是否启用LLM的。
# 4. 它有client，这个是用来调用LLM的。
# 5. 它有generate_structured，这个是用来生成结构化输出的。
# 6. 它有fallback_data，这个是用来返回本地fallback的。
# 7. 它有schema_model，这个是用来约束输出的。
# 8. 它有system_prompt，这个是用来提示LLM的。
# 9. 它有user_prompt，这个是用来输入的。
# 10. 它有response_format，这个是用来约束输出的。
# 11. 它有messages，这个是用来输入的。
# 12. 它有content，这个是用来输出的。
# 13. 它有data，这个是用来输出的。
# 14. 它有validated，这个是用来输出的。
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

