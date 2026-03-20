from typing import List, Literal

from pydantic import BaseModel, Field


class MatchPoint(BaseModel):
    """单条匹配点的结构化表示，含证据等级"""
    point: str = Field(description="匹配点描述，简洁说明候选人具备什么")
    evidence: str = Field(description="支撑该结论的简历原文依据，直接引用或转述")
    evidence_level: Literal["strong", "medium", "weak", "inferred"] = Field(
        description=(
            "证据等级："
            "strong=简历中有明确的代码/架构/功能实现描述；"
            "medium=有相关功能描述但细节不足；"
            "weak=只有一个功能点或间接相关；"
            "inferred=从其他能力推断，无直接证据"
        )
    )
    jd_requirement: str = Field(
        default="",
        description="对应 JD 中的哪条要求"
    )


class MatchAnalysis(BaseModel):
    high_match_points: List[MatchPoint] = Field(
        default_factory=list,
        description="高匹配点，每条含证据和证据等级"
    )
    weak_match_points: List[str] = Field(
        default_factory=list,
        description="弱匹配点：候选人有相关经历但深度不足或无法直接验证"
    )
    gap_items: List[str] = Field(
        default_factory=list,
        description="明确缺口：JD 要求但候选人材料中完全没有体现"
    )
    risk_points: List[str] = Field(
        default_factory=list,
        description="风险点：可能在面试或实际工作中暴露的问题"
    )
    needs_verification: List[str] = Field(
        default_factory=list,
        description="需要面试验证的项：简历中有描述但无法仅凭文字判断真实能力深度"
    )
    optimization_suggestions: List[str] = Field(
        default_factory=list,
        description="优化建议：候选人可以采取的具体行动"
    )
    rewrite_focus: List[str] = Field(
        default_factory=list,
        description="改写重点：告知 rewrite 模块应优先强化哪些方向"
    )
