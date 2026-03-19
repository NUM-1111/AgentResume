from pathlib import Path
from typing import Any, Dict, List, Set

from schemas.match_schema import MatchAnalysis
from services.llm_client import LLMClient


class MatchEvaluator:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self.prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "match_analysis.md"

    def evaluate(
        self,
        *,
        jd_analysis: Dict[str, Any],
        candidate_profile: Dict[str, Any],
        target_role: str,
    ) -> Dict[str, Any]:
        prompt = self.prompt_path.read_text(encoding="utf-8")
        fallback = self._fallback_match(jd_analysis, candidate_profile, target_role)

        user_prompt = (
            f"目标岗位方向：{target_role}\n\n"
            f"JD 解析结果：{jd_analysis}\n\n"
            f"候选人信息：{candidate_profile}\n\n"
            "请按 JSON Schema 给出匹配分析。"
        )

        data, source = self.llm_client.generate_structured(
            system_prompt=prompt,
            user_prompt=user_prompt,
            schema_model=MatchAnalysis,
            fallback_data=fallback,
        )
        data["_source"] = source
        return data

    @staticmethod
    def _fallback_match(
        jd_analysis: Dict[str, Any],
        candidate_profile: Dict[str, Any],
        target_role: str,
    ) -> Dict[str, Any]:
        jd_skills: Set[str] = set((jd_analysis.get("required_skills") or []) + (jd_analysis.get("keywords") or []))
        candidate_skills: Set[str] = set(candidate_profile.get("skills") or [])

        high_match = sorted([s for s in jd_skills if s in candidate_skills])[:8]
        weak_match = sorted([s for s in jd_skills if s not in candidate_skills])[:8]
        risk_points: List[str] = []

        if candidate_profile.get("missing_items"):
            risk_points.append("候选人信息存在缺失项，当前评估结论可靠性有限")
        if not high_match:
            risk_points.append("JD 与候选人显式技能重合较少，需重点补充证据")

        return MatchAnalysis(
            high_match_points=high_match or ["暂无显式高匹配点，建议补充更细粒度经历描述"],
            weak_match_points=weak_match or ["未发现明显弱匹配点，需结合更完整材料复核"],
            gap_items=weak_match or ["信息不足，待补充完整 JD 需求映射"],
            risk_points=risk_points or ["信息整体可用，但建议补充量化结果以提升可信度"],
            optimization_suggestions=[
                "将已有项目按 JD 关键词重排，先写最相关经历",
                "每段项目补充动作-结果-指标三段式表达",
                "补齐与目标岗位方向直接相关的技术细节",
            ],
            rewrite_focus=[
                f"围绕{target_role or '目标岗位'}强化相关能力",
                "优先改写和 JD 必备技能相关的项目片段",
            ],
        ).model_dump()

