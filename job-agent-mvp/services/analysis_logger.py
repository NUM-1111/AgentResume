"""
analysis_logger.py
------------------
本地文件日志系统：将每次分析结果（JD分析、候选人画像、匹配分析、改写结果）
以 JSON Lines 格式追加写入 logs/ 目录，便于日后复盘分析。

存储格式：
  logs/
    analysis_YYYY-MM.jsonl   # 按月分文件，每行一条完整记录
    index.json               # 轻量索引，记录每条日志的摘要信息

每条记录结构：
  {
    "log_id":        "uuid4",
    "logged_at":     "ISO8601 UTC",
    "target_role":   "...",
    "jd_snippet":    "前100字",
    "candidate_snippet": "前100字",
    "jd_analysis":   {...},
    "candidate_profile": {...},
    "match_analysis": {...},
    "project_rewrite": {...},
    "meta":          {...}
  }
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


# 日志根目录：项目根下的 logs/
_LOG_ROOT = Path(__file__).resolve().parent.parent / "logs"


def _ensure_dir() -> None:
    _LOG_ROOT.mkdir(parents=True, exist_ok=True)


def _monthly_log_path() -> Path:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    return _LOG_ROOT / f"analysis_{month}.jsonl"


def _index_path() -> Path:
    return _LOG_ROOT / "index.json"


def _load_index() -> list:
    p = _index_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_index(index: list) -> None:
    _index_path().write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_analysis(
    *,
    jd_text: str,
    candidate_text: str,
    target_role: str,
    result: Dict[str, Any],
) -> str:
    """
    将一次完整分析结果持久化到本地日志。

    Parameters
    ----------
    jd_text          : 原始 JD 文本
    candidate_text   : 原始候选人文本
    target_role      : 目标岗位
    result           : orchestrator.run() 的返回值（含四个分析块 + meta）

    Returns
    -------
    log_id : str  本条记录的唯一 ID
    """
    _ensure_dir()

    log_id = str(uuid.uuid4())
    logged_at = datetime.now(timezone.utc).isoformat()

    record = {
        "log_id": log_id,
        "logged_at": logged_at,
        "target_role": target_role,
        "jd_snippet": jd_text[:100].strip(),
        "candidate_snippet": candidate_text[:100].strip(),
        "jd_analysis": result.get("jd_analysis", {}),
        "candidate_profile": result.get("candidate_profile", {}),
        "match_analysis": result.get("match_analysis", {}),
        "project_rewrite": result.get("project_rewrite", {}),
        "meta": result.get("meta", {}),
    }

    # 追加写入月度 JSONL 文件
    log_file = _monthly_log_path()
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 更新轻量索引
    index = _load_index()
    index.append(
        {
            "log_id": log_id,
            "logged_at": logged_at,
            "target_role": target_role,
            "jd_snippet": record["jd_snippet"],
            "log_file": log_file.name,
        }
    )
    _save_index(index)

    return log_id


# ---------------------------------------------------------------------------
# 查询工具
# ---------------------------------------------------------------------------

def list_logs(limit: int = 50) -> list:
    """返回最近 limit 条日志的摘要（来自 index.json，倒序）。"""
    index = _load_index()
    return list(reversed(index))[:limit]


def get_log(log_id: str) -> Dict[str, Any] | None:
    """按 log_id 查找完整记录，遍历所有 JSONL 文件。"""
    for jsonl_file in sorted(_LOG_ROOT.glob("analysis_*.jsonl"), reverse=True):
        with jsonl_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("log_id") == log_id:
                        return record
                except json.JSONDecodeError:
                    continue
    return None
