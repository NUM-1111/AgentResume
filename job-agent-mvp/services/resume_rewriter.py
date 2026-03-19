from pathlib import Path
from typing import Any, Dict, List

from schemas.rewrite_schema import ProjectRewrite
from services.llm_client import LLMClient
from utils.parser import extract_bullets


class ResumeRewriter:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self.prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "project_rewrite.md"

    def rewrite(
        self,
        *,
        candidate_text: str,
        target_role: str,
        jd_keywords: List[str],
    ) -> Dict[str, Any]:
        prompt = self.prompt_path.read_text(encoding="utf-8")
        fallback = self._fallback_rewrite(candidate_text, target_role, jd_keywords)

        user_prompt = (
            f"目标岗位方向：{target_role}\n\n"
            f"JD 关键词：{jd_keywords}\n\n"
            f"候选人项目原文：\n{candidate_text}\n\n"
            "请按 JSON Schema 输出项目改写结果。"
        )
        data, source = self.llm_client.generate_structured(
            system_prompt=prompt,
            user_prompt=user_prompt,
            schema_model=ProjectRewrite,
            fallback_data=fallback,
        )
        data["_source"] = source
        return data

    @staticmethod
    def _fallback_rewrite(candidate_text: str, target_role: str, jd_keywords: List[str]) -> Dict[str, Any]:
        bullets = extract_bullets(candidate_text)
        selected = bullets[:6]
        rewritten: List[str] = []

        for line in selected:
            rewritten.append(f"围绕{target_role or '目标岗位'}，在真实项目中完成：{line}")

        notes = ["仅对表达做优化，不新增任何未出现的项目事实"]
        if not jd_keywords:
            notes.append("JD 关键词不足，建议先完善 JD 再进行二次改写")
        else:
            notes.append("建议在面试中用具体数据佐证关键词相关贡献")

        return ProjectRewrite(
            rewrite_strategy=[
                "优先保留原始事实，按岗位相关性重排内容",
                "每条经历尽量写成动作-方法-结果结构",
                "将 JD 关键词自然映射到真实工作场景",
            ],
            rewritten_project_description=rewritten or ["信息不足，无法进行有效改写，请补充项目描述"],
            emphasized_keywords=jd_keywords[:10] if jd_keywords else ["信息不足"],
            notes=notes,
        ).model_dump()

