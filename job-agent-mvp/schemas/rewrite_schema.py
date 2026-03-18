from typing import List

from pydantic import BaseModel, Field


class ProjectRewrite(BaseModel):
    rewrite_strategy: List[str] = Field(default_factory=list, description="改写策略")
    rewritten_project_description: List[str] = Field(
        default_factory=list,
        description="改写后的项目描述",
    )
    emphasized_keywords: List[str] = Field(default_factory=list, description="强调的关键词")
    notes: List[str] = Field(default_factory=list, description="注意事项")

