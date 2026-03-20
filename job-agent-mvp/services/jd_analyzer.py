from pathlib import Path
from typing import Dict, List

from schemas.jd_schema import (
    CandidateFocusItem,
    JDAnalysis,
    KeywordGroups,
    SkillItem,
)
from services.llm_client import LLMClient
from utils.parser import dedupe_keep_order, extract_bullets, normalize_text


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
        # 将 required_skills 转为结构化 SkillItem 列表
        raw_skills = self._pick_by_keywords(
            lines,
            ["熟悉", "掌握", "精通", "python", "sql", "llm", "机器学习", "深度学习", "数据"],
            limit=8,
        )
        required_skills = [
            SkillItem(
                skill=s[:60],
                priority="medium",
                verifiable=False,
                evidence_hint="请在简历中查找相关项目或技术描述",
            )
            for s in raw_skills
        ]

        bonus_skills = self._pick_by_keywords(
            lines,
            ["加分", "优先", "bonus", "nice to have", "开源", "竞赛", "论文"],
            limit=6,
        )

        # keyword_groups：按类型分桶
        keyword_groups = self._build_keyword_groups(low, target_role)

        return JDAnalysis(
            job_title=self._infer_title(lines, target_role),
            job_direction=target_role or "未明确",
            responsibilities=responsibilities or ["未在 JD 中明确说明"],
            required_skills=required_skills or [
                SkillItem(
                    skill="未在 JD 中明确说明",
                    priority="medium",
                    verifiable=False,
                    evidence_hint="",
                )
            ],
            bonus_skills=bonus_skills or ["未在 JD 中明确说明"],
            keyword_groups=keyword_groups,
            candidate_focus=[
                CandidateFocusItem(
                    focus="突出与岗位关键词直接相关的真实项目经历",
                    priority="high",
                    reason="JD 要求有完整项目级开发经验",
                ),
                CandidateFocusItem(
                    focus="优先强调可量化结果与业务影响",
                    priority="medium",
                    reason="量化成果更具说服力",
                ),
                CandidateFocusItem(
                    focus="补充与 JD 要求相关的技术细节",
                    priority="low",
                    reason="技术细节体现深度",
                ),
            ],
            jd_risk_flags=[],
        ).model_dump()

    @staticmethod
    def _infer_title(lines: List[str], target_role: str) -> str:
        for line in lines[:10]:
            if "工程师" in line or "scientist" in line.lower() or "developer" in line.lower():
                return line[:40]
        return target_role or "未明确"

    @staticmethod
    def _pick_by_keywords(lines: List[str], keywords: List[str], limit: int) -> List[str]:
        hits: List[str] = []
        for line in lines:
            low = line.lower()
            if any(k in low for k in keywords):
                hits.append(line)
        return dedupe_keep_order(hits)[:limit]

    @staticmethod
    def _build_keyword_groups(text_lower: str, target_role: str) -> KeywordGroups:
        """按类型将关键词分桶，fallback 版本基于固定词表匹配"""
        tech_candidates = [
            "rag", "vllm", "ollama", "langchain", "milvus", "faiss", "chroma",
            "llm", "gpt", "bert", "transformer", "embedding", "vector",
            "sql", "python", "java", "docker", "kubernetes", "redis",
            "sft", "rl", "cv", "nlp", "sse", "jwt",
        ]
        capability_candidates = [
            "任务拆解", "多agent协作", "系统级权衡", "边界治理", "依赖编排",
            "上下文管理", "记忆管理", "规划与推理", "工具集成", "知识增强",
            "根因分析", "调试定位", "灰度发布", "监控告警", "自动恢复",
        ]
        tool_candidates = [
            "cursor", "claude code", "github", "docker", "ci", "lint",
            "静态分析", "git", "linux",
        ]
        domain_candidates = [
            "ai原生架构", "工程确定性", "高可用架构", "mttr", "slo",
            "数据契约", "ci阻断", "分层验证", "agent系统", "prompt engineering",
        ]

        return KeywordGroups(
            tech_keywords=[k for k in tech_candidates if k in text_lower],
            capability_keywords=[k for k in capability_candidates if k in text_lower],
            tool_keywords=[k for k in tool_candidates if k in text_lower],
            domain_keywords=[k for k in domain_candidates if k in text_lower],
        )
