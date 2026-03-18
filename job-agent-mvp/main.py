from fastapi import FastAPI
from pydantic import BaseModel, Field

from services.orchestrator import JobAgentOrchestrator


app = FastAPI(title="Job Agent MVP", version="0.1.0")
orchestrator = JobAgentOrchestrator()


class AnalyzeRequest(BaseModel):
    jd_text: str = Field(..., min_length=10, description="岗位 JD 文本")
    candidate_text: str = Field(..., min_length=10, description="候选人背景文本")
    target_role: str = Field(..., min_length=2, description="目标岗位方向")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest) -> dict:
    return orchestrator.run(
        jd_text=payload.jd_text,
        candidate_text=payload.candidate_text,
        target_role=payload.target_role,
    )

