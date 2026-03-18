from typing import List

from pydantic import BaseModel, Field


class MatchAnalysis(BaseModel):
    high_match_points: List[str] = Field(default_factory=list, description="高匹配点")
    weak_match_points: List[str] = Field(default_factory=list, description="弱匹配点")
    gap_items: List[str] = Field(default_factory=list, description="缺口项")
    risk_points: List[str] = Field(default_factory=list, description="风险点")
    optimization_suggestions: List[str] = Field(
        default_factory=list,
        description="优化建议",
    )
    rewrite_focus: List[str] = Field(default_factory=list, description="改写重点")

