from pathlib import Path
from typing import Dict, List

from schemas.jd_schema import JDAnalysis
from services.llm_client import LLMClient
from utils.parser import dedupe_keep_order, extract_bullets, normalize_text

# 这个类是用来解析JD的
class JDAnalyzer:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self.prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "jd_analysis.md"

    def analyze(self, jd_text: str, target_role: str) -> Dict:
        prompt = self.prompt_path.read_text(encoding="utf-8")
        fallback = self._fallback_jd_analysis(jd_text, target_role)

        user_prompt = (
            f"目标岗位方向：{target_role}\n\n"
            f"岗位 JD 原文：\n{jd_text}\n\n"
            "请严格按 JSON Schema 输出。"
        )
        data, source = self.llm_client.generate_structured(
            system_prompt=prompt,
            user_prompt=user_prompt,
            schema_model=JDAnalysis,
            fallback_data=fallback,
        )
        data["_source"] = source
        return data

    def _fallback_jd_analysis(self, jd_text: str, target_role: str) -> Dict:
        text = normalize_text(jd_text)
        lines = extract_bullets(text)
        low = text.lower()

        responsibilities = self._pick_by_keywords(
            lines,
            ["负责", "构建", "设计", "优化", "落地", "协同", "deliver", "build", "design"],
            limit=8,
        )
        required_skills = self._pick_by_keywords(
            lines,
            ["熟悉", "掌握", "精通", "python", "sql", "llm", "机器学习", "深度学习", "数据"],
            limit=8,
        )
        bonus_skills = self._pick_by_keywords(
            lines,
            ["加分", "优先", "bonus", "nice to have", "开源", "竞赛", "论文"],
            limit=6,
        )
        keywords = dedupe_keep_order(self._extract_keywords(low, target_role))

        return JDAnalysis(
            job_title=self._infer_title(lines, target_role),
            job_direction=target_role or "未明确",
            responsibilities=responsibilities or ["未在 JD 中明确说明"],
            required_skills=required_skills or ["未在 JD 中明确说明"],
            bonus_skills=bonus_skills or ["未在 JD 中明确说明"],
            keywords=keywords or ["信息不足"],
            candidate_focus=[
                "突出与岗位关键词直接相关的真实项目经历",
                "优先强调可量化结果与业务影响",
                "补充与 JD 要求相关的技术细节",
            ],
        ).model_dump()

    # 这个函数是用来推断岗位名称的
    @staticmethod
    def _infer_title(lines: List[str], target_role: str) -> str:
        for line in lines[:10]:
            if "工程师" in line or "scientist" in line.lower() or "developer" in line.lower():
                return line[:40]
        return target_role or "未明确"

    # 这个函数是用来选择关键词的
    @staticmethod
    def _pick_by_keywords(lines: List[str], keywords: List[str], limit: int) -> List[str]:
        hits: List[str] = []
        for line in lines:
            low = line.lower()
            if any(k in low for k in keywords):
                hits.append(line)
        return dedupe_keep_order(hits)[:limit]

    # 这个函数是用来提取关键词的
    @staticmethod
    def _extract_keywords(text_lower: str, target_role: str) -> List[str]:
        candidates = [
            "python",
            "fastapi",
            "sql",
            "llm",
            "rag",
            "机器学习",
            "深度学习",
            "数据分析",
            "a/b test",
            "推荐系统",
            "prompt engineering",
            "沟通协作",
            target_role.strip().lower() if target_role else "",
        ]
        return [k for k in candidates if k and k in text_lower]

