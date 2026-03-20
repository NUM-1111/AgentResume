from pathlib import Path
from typing import Any, Dict, List, Set

from schemas.match_schema import MatchAnalysis, MatchPoint
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
        # required_skills 是 List[SkillItem dict]，提取 skill 字段
        raw_required = jd_analysis.get("required_skills") or []
        skill_names = [
            s["skill"] if isinstance(s, dict) else str(s)
            for s in raw_required
        ]

        # keyword_groups 是 KeywordGroups dict，展开所有分组
        kw_groups = jd_analysis.get("keyword_groups") or {}
        if isinstance(kw_groups, dict):
            all_keywords = (
                kw_groups.get("tech_keywords", [])
                + kw_groups.get("capability_keywords", [])
                + kw_groups.get("tool_keywords", [])
                + kw_groups.get("domain_keywords", [])
            )
        else:
            all_keywords = list(jd_analysis.get("keywords") or [])

        jd_skills: Set[str] = set(skill_names + all_keywords)
        candidate_skills: Set[str] = set(candidate_profile.get("skills") or [])

        # 只有在候选人 skills 中明确出现的才算高匹配，证据等级为 weak（fallback 无法判断深度）
        matched = sorted([s for s in jd_skills if s in candidate_skills])[:6]
        unmatched = sorted([s for s in jd_skills if s not in candidate_skills])[:8]

        high_match_points: List[MatchPoint] = [
            MatchPoint(
                point=f"候选人技能列表中包含：{s}",
                evidence=f"skills 字段中存在 '{s}'",
                evidence_level="weak",
                jd_requirement=s,
            )
            for s in matched
        ]

        # needs_verification：所有 weak 证据的匹配点都需要面试验证
        needs_verification = [p.point for p in high_match_points]

        risk_points: List[str] = []
        if candidate_profile.get("missing_items"):
            risk_points.append("候选人信息存在缺失项，当前评估结论可靠性有限")
        if not matched:
            risk_points.append("JD 与候选人显式技能重合较少，需重点补充证据")

        # rewrite_focus 只写有真实证据支撑的方向
        rewrite_focus: List[str] = []
        if matched:
            rewrite_focus.append(f"强化已匹配技能的项目描述：{', '.join(matched[:3])}")
        rewrite_focus.append("优先改写与 JD 必备技能直接相关的项目片段，保持事实边界")

        return MatchAnalysis(
            high_match_points=high_match_points or [
                MatchPoint(
                    point="暂无显式高匹配点，建议补充更细粒度经历描述",
                    evidence="候选人 skills 与 JD 关键词无直接重合",
                    evidence_level="inferred",
                    jd_requirement="",
                )
            ],
            weak_match_points=unmatched[:6] or ["未发现明显弱匹配点，需结合更完整材料复核"],
            gap_items=unmatched[6:] or ["信息不足，待补充完整 JD 需求映射"],
            risk_points=risk_points or ["信息整体可用，但建议补充量化结果以提升可信度"],
            needs_verification=needs_verification or ["建议面试中验证所有技能的实际应用深度"],
            optimization_suggestions=[
                "将已有项目按 JD 关键词重排，先写最相关经历",
                "每段项目补充动作-结果-指标三段式表达（仅填写真实数据）",
                "补齐与目标岗位方向直接相关的技术细节",
            ],
            rewrite_focus=rewrite_focus,
        ).model_dump()
