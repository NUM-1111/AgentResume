from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.analysis_logger import get_log, list_logs
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


# ---------------------------------------------------------------------------
# 日志查询接口
# ---------------------------------------------------------------------------

@app.get("/logs")
def logs(limit: int = 50) -> dict:
    """返回最近 limit 条分析日志的摘要列表。"""
    return {"logs": list_logs(limit=limit)}


@app.get("/logs/{log_id}")
def log_detail(log_id: str) -> dict:
    """按 log_id 返回完整分析记录。"""
    record = get_log(log_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"log_id '{log_id}' not found")
    return record

