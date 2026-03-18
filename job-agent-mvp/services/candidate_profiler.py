from typing import Any, Dict, List

from utils.parser import parse_candidate_text


class CandidateProfiler:
    def profile(self, candidate_text: str) -> Dict[str, Any]:
        parsed = parse_candidate_text(candidate_text)
        missing_items: List[str] = []

        if not parsed.get("skills"):
            missing_items.append("技能栈信息不足")
        if not parsed.get("projects"):
            missing_items.append("项目经历信息不足")
        if not parsed.get("experiences"):
            missing_items.append("工作/实习经历信息不足")

        parsed["missing_items"] = missing_items
        parsed["summary"] = self._build_summary(parsed)
        return parsed

    @staticmethod
    def _build_summary(profile: Dict[str, Any]) -> str:
        skill_count = len(profile.get("skills", []))
        project_count = len(profile.get("projects", []))
        exp_count = len(profile.get("experiences", []))
        return (
            f"候选人材料中提取到技能 {skill_count} 项，"
            f"项目条目 {project_count} 条，经历条目 {exp_count} 条。"
        )

