from typing import List, Literal

from pydantic import BaseModel, Field

# 技能项
class SkillItem(BaseModel):
    """单条技能要求的结构化表示"""
    skill: str = Field(description="技能点名称，简洁独立，不含完整句子")
    priority: Literal["high", "medium", "low"] = Field(
        description="重要程度：high=硬性要求，medium=期望具备，low=加分项"
    )
    verifiable: bool = Field(
        description="是否可通过简历/项目直接验证"
    )
    evidence_hint: str = Field(
        default="",
        description="验证该技能时应关注的简历证据方向，例如'项目中是否有RAG链路实现'"
    )


# 关键词分组
class KeywordGroups(BaseModel):
    """关键词按类型分组，便于下游 match 模块区分权重"""
    tech_keywords: List[str] = Field(
        default_factory=list,
        description="具体技术词，如 RAG、vLLM、LangChain、Milvus"
    )
    capability_keywords: List[str] = Field(
        default_factory=list,
        description="能力词，如 任务拆解、多agent协作、系统级权衡"
    )
    tool_keywords: List[str] = Field(
        default_factory=list,
        description="工具/平台名，如 Cursor、Claude Code、Docker、GitHub"
    )
    domain_keywords: List[str] = Field(
        default_factory=list,
        description="领域/概念词，如 AI原生架构、工程确定性、高可用架构"
    )


# 候选人投递时应重点强调的方向，带优先级
class CandidateFocusItem(BaseModel):
    """候选人投递时应重点强调的方向，带优先级"""
    focus: str = Field(description="应强调的能力或经历方向")
    priority: Literal["high", "medium", "low"] = Field(
        description="优先级：high=必须体现，medium=建议体现，low=锦上添花"
    )
    reason: str = Field(
        default="",
        description="为什么这个方向重要，对应 JD 中的哪条要求"
    )


# JD 分析
class JDAnalysis(BaseModel):
    job_title: str = Field(default="未明确", description="岗位名称")
    job_direction: str = Field(default="未明确", description="岗位方向")
    responsibilities: List[str] = Field(
        default_factory=list,
        description="岗位职责，每条为独立职责描述"
    )
    required_skills: List[SkillItem] = Field(
        default_factory=list,
        description="必备技能，每条结构化，含优先级和可验证性"
    )
    bonus_skills: List[str] = Field(
        default_factory=list,
        description="加分项，保持原文描述"
    )
    keyword_groups: KeywordGroups = Field(
        default_factory=KeywordGroups,
        description="关键词按类型分组"
    )
    candidate_focus: List[CandidateFocusItem] = Field(
        default_factory=list,
        description="候选人应重点强调的能力，带优先级和原因"
    )
    jd_risk_flags: List[str] = Field(
        default_factory=list,
        description="JD 中对候选人可能构成风险的高门槛要求，如'从零设计AI原生架构'"
    )
