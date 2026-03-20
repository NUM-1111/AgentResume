from typing import Any, Dict, List

from utils.parser import parse_candidate_text


# 缺失项检查清单（固定检查项）
_MISSING_CHECKLIST = [
    ("work_experiences", "工作/实习经历"),
    ("education",        "学历信息"),
    ("github_link",      "GitHub / 作品集链接"),
    ("quantified_data",  "量化数据（如效率提升、风险降低等指标）"),
]

# 候选人信息结构化模块
class CandidateProfiler:
    def profile(self, candidate_text: str) -> Dict[str, Any]:
        parsed = parse_candidate_text(candidate_text)
        missing_items = self._check_missing(parsed, candidate_text)
        parsed["missing_items"] = missing_items
        parsed["summary"] = self._build_summary(parsed)
        return parsed

    # 缺失项检查
    @staticmethod
    def _check_missing(parsed: Dict[str, Any], raw_text: str) -> List[str]:
        missing: List[str] = []

        # 1. 工作/实习经历
        if not parsed.get("work_experiences"):
            missing.append("工作/实习经历（当前仅有项目经历，无全职/实习记录）")

        # 2. 学历信息
        basic_info = parsed.get("basic_info", {})
        if not basic_info.get("education"):
            missing.append("学历信息（未检测到本科/硕士/博士等学历描述）")

        # 3. GitHub / 作品集链接
        if not any(k in raw_text.lower() for k in ["github", "gitlab", "gitee", "作品集", "portfolio"]):
            missing.append("GitHub / 作品集链接（未在简历中发现代码仓库或作品集地址）")

        # 4. 量化数据
        has_numbers = bool(__import__("re").search(r"\d+%|\d+x|\d+倍|\d+ms|\d+s\b", raw_text))
        if not has_numbers:
            missing.append("量化数据（项目描述中未发现可量化的成果指标，如效率提升%、延迟降低ms等）")

        # 5. 技能不足
        if not parsed.get("skills"):
            missing.append("技能栈信息不足（未能从简历中提取到独立技能点）")

        # 6. 项目经历不足
        if not parsed.get("projects"):
            missing.append("项目经历信息不足")

        return missing

    # 总结
    @staticmethod
    def _build_summary(profile: Dict[str, Any]) -> str:
        skill_count = len(profile.get("skills", []))
        project_count = len(profile.get("projects", []))
        work_count = len(profile.get("work_experiences", []))
        missing_count = len(profile.get("missing_items", []))

        parts = [
            f"提取到独立技能点 {skill_count} 项",
            f"结构化项目 {project_count} 个",
        ]
        if work_count:
            parts.append(f"工作/实习经历 {work_count} 条")
        else:
            parts.append("无工作/实习经历")

        if missing_count:
            parts.append(f"缺失项 {missing_count} 处（见 missing_items）")

        return "，".join(parts) + "。"
