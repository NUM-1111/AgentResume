# Job Agent MVP

一个面向求职投递流程的任务型智能助手 MVP，聚焦 3 个核心能力：

1. JD 解析
2. 简历匹配分析
3. 项目经历改写

## 1. 项目定位

输入岗位 JD、候选人背景和目标岗位方向，系统输出结构化结果：

- 岗位职责/技能关键词/经验要求提取
- 候选人与岗位的匹配点评估
- 基于目标岗位风格的项目经历改写

## 2. 核心原则

- 不编造候选人不存在的经历、项目、成果和技术栈
- 可以优化表达，但不能修改事实
- 信息不足时显式说明缺失项
- 优先快速可落地，便于后续扩展

## 3. 技术栈

- 后端 API: FastAPI
- 前端页面: Streamlit
- LLM 接口: 统一封装在 `services/llm_client.py`
- 输出约束: Pydantic Schema（可直接转 JSON Schema）

## 4. 目录结构

```text
job-agent-mvp/
  app.py
  main.py
  requirements.txt
  .env.example
  README.md
  prompts/
    jd_analysis.md
    match_analysis.md
    project_rewrite.md
  services/
    llm_client.py
    jd_analyzer.py
    candidate_profiler.py
    match_evaluator.py
    resume_rewriter.py
    orchestrator.py
  schemas/
    jd_schema.py
    match_schema.py
    rewrite_schema.py
  sample_data/
    sample_jd.txt
    sample_candidate.md
  utils/
    parser.py
    formatter.py
```

## 5. 环境与启动

### 5.1 环境要求

- **Python 3.10+**（推荐 3.12）
- 依赖见 `requirements.txt`（与代码中的 `import` 一致：FastAPI、Uvicorn、Streamlit、Pydantic、python-dotenv、OpenAI SDK、httpx）

### 5.2 推荐：仓库根目录一键配置（虚拟环境 + 依赖 + `.env` 占位）

在 **`AgentResume` 仓库根目录**（与 `job-agent-mvp` 同级）执行其一：

| 方式 | 命令 |
|------|------|
| PowerShell | `.\setup.ps1` |
| CMD | `setup.bat` |

脚本会：

1. 在 `job-agent-mvp\.venv` 创建虚拟环境（优先使用 Windows 的 `py -3`，否则 `python`）
2. 执行 `pip install -r requirements.txt`
3. 若存在 `.env.example` 且尚无 `.env`，则复制为 `.env`（可再编辑 API Key）

完成后在同一目录启动：

| 方式 | 命令 |
|------|------|
| PowerShell | `.\start.ps1` |
| CMD | `start.bat` |

启动脚本会使用 **`.venv` 内的 Python** 分别拉起 FastAPI（8000）与 Streamlit（8501）。

### 5.3 手动配置（与早期文档步骤一致，便于对照）

在终端进入 **`job-agent-mvp`** 目录：

**Windows（PowerShell 示例）**

```powershell
cd job-agent-mvp
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# 按需编辑 .env 中的 OPENAI_API_KEY 等
```

**macOS / Linux**

```bash
cd job-agent-mvp
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

**启动服务**（需已激活上述虚拟环境，且在 `job-agent-mvp` 下）：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

另开终端（同样激活 `.venv`）：

```bash
streamlit run app.py --server.port 8501
```

接口：

- `GET /health`
- `POST /analyze`

### 5.4 配置环境变量（LLM）

复制 `.env.example` 为 `.env`，按需填写（无 Key 时仍可走本地降级逻辑）：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（可选，默认 OpenAI 官方）
- `OPENAI_MODEL`（可选，默认 `gpt-4o-mini`）

## 6. 输入输出说明

`POST /analyze` 请求示例：

```json
{
  "jd_text": "岗位 JD 文本...",
  "candidate_text": "候选人信息文本...",
  "target_role": "AI算法工程师"
}
```

响应包含：

- `jd_analysis`
- `candidate_profile`
- `match_analysis`
- `project_rewrite`
- `meta`（时间戳与模型信息）

## 7. 无 API Key 的行为

为保证 MVP 可运行：当未配置 API Key 时，系统会走本地降级逻辑，返回基于规则的占位分析结果，并明确提示质量受限。配置 API Key 后会自动切换为 LLM 分析。

## 8. 后续扩展建议

- 增加多轮追问与补全缺失信息
- 引入向量检索支持候选人多份材料整合
- 增加导出简历片段（Markdown / Docx）
- 接入任务状态与会话存储
