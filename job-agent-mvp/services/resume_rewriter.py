import json
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
        candidate_profile: Dict[str, Any],
        target_role: str,
        jd_analysis: Dict[str, Any],
        rewrite_focus: List[str],
    ) -> Dict[str, Any]:
        prompt = self.prompt_path.read_text(encoding="utf-8")

        # 从 keyword_groups 展开所有关键词，传给 LLM 和 fallback
        kw_groups = jd_analysis.get("keyword_groups") or {}
        all_keywords: List[str] = (
            kw_groups.get("tech_keywords", [])
            + kw_groups.get("capability_keywords", [])
            + kw_groups.get("tool_keywords", [])
            + kw_groups.get("domain_keywords", [])
        ) if isinstance(kw_groups, dict) else list(jd_analysis.get("keywords") or [])

        fallback = self._fallback_rewrite(candidate_profile, target_role, all_keywords)

        # user_prompt 传入结构化事实白名单，而非原始文本
        projects_fact = candidate_profile.get("projects") or []
        user_prompt = (
            f"目标岗位方向：{target_role}\n\n"
            f"JD 关键词（按类型分组）：{json.dumps(kw_groups, ensure_ascii=False)}\n\n"
            f"改写重点（来自 match 模块，仅包含有证据支撑的方向）：{rewrite_focus}\n\n"
            f"候选人项目事实白名单（结构化，请严格基于此改写，不得新增事实）：\n"
            f"{json.dumps(projects_fact, ensure_ascii=False, indent=2)}\n\n"
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
    def _fallback_rewrite(
        candidate_profile: Dict[str, Any],
        target_role: str,
        jd_keywords: List[str],
    ) -> Dict[str, Any]:
        # 从结构化 projects 提取 highlights 作为改写基础
        projects = candidate_profile.get("projects") or []
        highlights: List[str] = []
        for proj in projects:
            if isinstance(proj, dict):
                for h in proj.get("highlights", []):
                    highlights.append(h)

        # fallback 不做任何脑补，只做最小化的表达重组
        rewritten: List[str] = []
        for line in highlights[:6]:
            rewritten.append(line)  # 保持原文，不添加任何内容

        notes = [
            "当前为 fallback 模式，仅保留原始事实，未做表达优化",
            "建议配置 LLM 后重新运行以获得完整改写结果",
        ]
        if not jd_keywords:
            notes.append("JD 关键词不足，建议先完善 JD 再进行二次改写")
        else:
            notes.append("如需量化数据，请候选人自行补充真实指标（禁止填写估算数字）")

        return ProjectRewrite(
            rewrite_strategy=[
                "严格基于候选人原始事实，不新增任何数字、功能或技术描述",
                "优先保留原始事实，按岗位相关性重排内容",
                "将 JD 关键词仅在有原文事实支撑时自然融入",
            ],
            rewritten_project_description=rewritten or ["信息不足，无法进行有效改写，请补充项目描述"],
            emphasized_keywords=jd_keywords[:10] if jd_keywords else ["信息不足"],
            added_facts=[],  # fallback 不新增任何事实
            notes=notes,
        ).model_dump()
