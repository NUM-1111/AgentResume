from typing import List

from pydantic import BaseModel, Field


class JDAnalysis(BaseModel):
    job_title: str = Field(default="未明确", description="岗位名称")
    job_direction: str = Field(default="未明确", description="岗位方向")
    responsibilities: List[str] = Field(default_factory=list, description="岗位职责")
    required_skills: List[str] = Field(default_factory=list, description="必备技能")
    bonus_skills: List[str] = Field(default_factory=list, description="加分项")
    keywords: List[str] = Field(default_factory=list, description="JD 关键词列表")
    candidate_focus: List[str] = Field(
        default_factory=list,
        description="候选人应重点强调的能力",
    )

