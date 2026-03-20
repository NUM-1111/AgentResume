# Job Agent MVP — 项目概况

> 生成时间：2026-03-20  
> 路径：`job-agent-mvp/`

---

## 项目定位

一个面向求职场景的 **AI Pipeline Agent**。输入职位描述（JD）+ 候选人背景文本 + 目标岗位方向，自动完成 JD 解析 → 简历结构化 → 匹配分析 → 简历改写的完整流程，输出结构化 JSON。

核心约束：**不捏造事实**，所有改写内容必须有原始依据。

---

## 技术栈

| 层 | 技术 |
|---|---|
| API 服务 | FastAPI + Uvicorn |
| UI | Streamlit |
| LLM 接口 | OpenAI Python SDK（兼容 OpenAI 协议） |
| 输出校验 | Pydantic v2 |
| 配置 | python-dotenv |
| 日志 | 自定义 JSONL 文件日志 |
| 运行时 | Python 3.14 |

LLM 配置通过 `.env` 注入：`OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`（默认 `gpt-4o-mini`）。

---

## 目录结构

```
job-agent-mvp/
├── main.py                  # FastAPI 入口，POST /analyze
├── app.py                   # Streamlit UI 入口
├── requirements.txt
│
├── services/
│   ├── orchestrator.py      # Pipeline 总调度
│   ├── llm_client.py        # LLM 适配层（含 fallback 逻辑）
│   ├── jd_analyzer.py       # Step 1：JD 解析
│   ├── candidate_profiler.py# Step 2：简历结构化（规则）
│   ├── match_evaluator.py   # Step 3：匹配分析
│   ├── resume_rewriter.py   # Step 4：简历改写
│   └── analysis_logger.py   # JSONL 日志持久化
│
├── schemas/
│   ├── jd_schema.py         # JDAnalysis, SkillItem, KeywordGroups, CandidateFocusItem
│   ├── match_schema.py      # MatchAnalysis, MatchPoint
│   └── rewrite_schema.py    # ProjectRewrite
│
├── prompts/
│   ├── jd_analysis.md
│   ├── match_analysis.md
│   └── project_rewrite.md
│
├── utils/
│   ├── parser.py            # 简历文本解析（分段、技能提取、项目解析）
│   └── formatter.py         # JSON 格式化工具
│
├── sample_data/             # 示例 JD 和候选人背景
├── logs/                    # index.json + analysis_YYYY-MM.jsonl
├── test_resource/           # 历次测试输出
└── docs/                    # 文档（含本文件）
```

---

## Pipeline 流程

```
输入：jd_text + candidate_text + target_role
        │
        ▼
  orchestrator.run()
        │
        ├─ Step 1  JDAnalyzer.analyze()
        │          LLM → JDAnalysis
        │          · responsibilities（职责列表）
        │          · required_skills（SkillItem：priority / verifiable）
        │          · keyword_groups（tech / capability / tool / domain）
        │          · candidate_focus（候选人应关注的方向）
        │          · risk_flags（风险提示）
        │
        ├─ Step 2  CandidateProfiler.profile()
        │          规则解析 → 结构化 profile
        │          · skills（独立 token 列表）
        │          · projects（name / period / role / tech_stack / highlights）
        │          · work_experiences
        │          · basic_info
        │          · missing_items（缺失项检测）
        │
        ├─ Step 3  MatchEvaluator.evaluate()
        │          LLM → MatchAnalysis
        │          · high_match_points / weak_match_points（含 evidence_level）
        │          · gap_items / risk_points / needs_verification
        │          · rewrite_focus（改写方向建议）
        │
        └─ Step 4  ResumeRewriter.rewrite()
                   LLM → ProjectRewrite
                   · rewritten_projects（改写后项目描述）
                   · added_facts（自审字段：声明新增内容）
                        │
                        ▼
              Result dict + meta（model / sources / log_id）
                        │
                        ▼
              AnalysisLogger → logs/analysis_YYYY-MM.jsonl
```

---

## 关键设计

**双模式运行**：每个 LLM 模块都有本地 fallback（规则兜底）。无 API Key 时系统仍可运行，`meta.sources` 字段记录每个模块实际走的路径（`"llm"` 或 `"fallback:<reason>"`）。

**Schema 驱动输出**：所有 LLM 输出通过 Pydantic 模型校验，JSON Schema 注入 system prompt，兼容 OpenAI 及任意 OpenAI 协议兼容接口（如 DeepSeek）。

**证据等级分级**：`MatchPoint.evidence_level` 为 `strong | medium | weak | inferred`，防止将关键词出现等同于能力证明。

**事实边界约束**：改写模块硬约束不捏造数字、功能、技术。`added_facts` 为自审字段，若 LLM 新增任何原文没有的内容，必须在此声明。

---

## 当前状态

已完成第一轮优化（`docs/第一次优化/`）：

| 模块 | 优化前问题 | 优化后 |
|---|---|---|
| candidate_profiler | 按行分割，技能不独立 | 结构化解析，skills 为独立 token |
| jd_analyzer | 输出摘要，下游不可驱动 | 分解为 SkillItem 结构，关键词分桶 |
| match_evaluator | 过度推断，无证据分级 | 引入 evidence_level + needs_verification |
| resume_rewriter | 捏造数字和功能 | added_facts 自审，空列表为合格 |

已知遗留问题：简历解析器 regex 在软换行处可能错误切分句子。

---

## 对外接口

### FastAPI

```
POST /analyze
Content-Type: application/json

{
  "jd_text": "...",
  "candidate_text": "...",
  "target_role": "..."
}
```

返回完整 pipeline 结果 + `meta.sources` + `meta.log_id`。

### Streamlit UI

运行 `streamlit run app.py`，提供表单输入和结果展示界面。

---

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 LLM（可选，无 key 走 fallback）
cp .env.example .env  # 填入 OPENAI_API_KEY 等

# API 模式
uvicorn main:app --reload

# UI 模式
streamlit run app.py
```
