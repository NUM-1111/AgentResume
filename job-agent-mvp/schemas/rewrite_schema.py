from typing import List

from pydantic import BaseModel, Field


class ProjectRewrite(BaseModel):
    rewrite_strategy: List[str] = Field(
        default_factory=list,
        description="改写策略：说明本次改写遵循的原则"
    )
    rewritten_project_description: List[str] = Field(
        default_factory=list,
        description="改写后的项目描述，每条对应一个 bullet point，只强化表达，不新增事实"
    )
    emphasized_keywords: List[str] = Field(
        default_factory=list,
        description="本次改写中自然融入的 JD 关键词，必须有原文事实支撑"
    )
    added_facts: List[str] = Field(
        default_factory=list,
        description=(
            "自查字段：列出改写中新增的、原文没有的内容（数字、功能、技术描述等）。"
            "如果严格遵守了事实边界，此字段应为空列表。"
            "此字段用于人工审核，不会展示给候选人。"
        )
    )
    notes: List[str] = Field(
        default_factory=list,
        description="注意事项：标注哪些地方候选人需要补充真实数据或细节"
    )
