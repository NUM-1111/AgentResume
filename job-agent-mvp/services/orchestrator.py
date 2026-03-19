from datetime import datetime, timezone
from typing import Any, Dict

from services.candidate_profiler import CandidateProfiler
from services.jd_analyzer import JDAnalyzer
from services.llm_client import LLMClient
from services.match_evaluator import MatchEvaluator
from services.resume_rewriter import ResumeRewriter


class JobAgentOrchestrator:
    def __init__(self) -> None:
        llm_client = LLMClient()
        self.llm_client = llm_client
        self.jd_analyzer = JDAnalyzer(llm_client)
        self.candidate_profiler = CandidateProfiler()
        self.match_evaluator = MatchEvaluator(llm_client)
        self.resume_rewriter = ResumeRewriter(llm_client)

    def run(self, *, jd_text: str, candidate_text: str, target_role: str) -> Dict[str, Any]:
        jd_analysis = self.jd_analyzer.analyze(jd_text=jd_text, target_role=target_role)
        candidate_profile = self.candidate_profiler.profile(candidate_text)
        match_analysis = self.match_evaluator.evaluate(
            jd_analysis=jd_analysis,
            candidate_profile=candidate_profile,
            target_role=target_role,
        )
        project_rewrite = self.resume_rewriter.rewrite(
            candidate_text=candidate_text,
            target_role=target_role,
            jd_keywords=jd_analysis.get("keywords", []),
        )

        sources = {
            "jd_analysis": jd_analysis.pop("_source", "unknown"),
            "match_analysis": match_analysis.pop("_source", "unknown"),
            "project_rewrite": project_rewrite.pop("_source", "unknown"),
        }

        return {
            "jd_analysis": jd_analysis,
            "candidate_profile": candidate_profile,
            "match_analysis": match_analysis,
            "project_rewrite": project_rewrite,
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model_enabled": self.llm_client.enabled,
                "model": self.llm_client.model,
                "base_url": self.llm_client.base_url,
                "sources": sources,
            },
        }

