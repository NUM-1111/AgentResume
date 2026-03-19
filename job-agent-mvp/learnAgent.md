# learnAgent.md — 用“傻瓜式”方式理解 Job Agent MVP

目标：读完这份文档，你能**口述整个项目**、理解一个 Agent 应用的**全流程与结构**，并能自己照着搭一个类似的“任务型 Agent”。

> 本项目是一个 **Workflow/Pipeline 型 Agent**：把大任务拆成几个固定步骤（模块），按顺序执行，产出结构化结果。它不是“自由对话型聊天机器人”。

---

## 1. 这个项目到底在解决什么问题？

你在求职投递时通常要做 3 件事：

- **读 JD**：岗位要什么？职责是什么？必须技能是什么？
- **对比自己**：我哪里匹配？哪里不匹配？缺口是什么？怎么补材料？
- **改简历**：把“真实项目经历”改写成更贴合目标岗位的表达（但不能编造）

这个项目把上面 3 件事变成一次接口/一次按钮点击的自动流程：

输入：

- `jd_text`：岗位 JD 文本
- `candidate_text`：候选人背景/简历文本（自由格式）
- `target_role`：目标岗位方向（用于引导分析视角）

输出（结构化 JSON）：

- `jd_analysis`：JD 解析结果
- `candidate_profile`：候选人信息结构化结果（本地规则解析）
- `match_analysis`：匹配分析结果
- `project_rewrite`：项目改写结果
- `meta`：时间戳/模型是否启用/模型名

---

## 2. 你要记住的“Agent 工程”核心套路（本项目就是这样做的）

本项目用的是非常经典、非常适合新手的套路：

- **把一个大任务拆成 3～5 个小任务模块**
- 每个模块都做一件事，输入/输出都明确
- **用 Schema（Pydantic）约束输出结构**，确保下游能稳定消费
- **用 Prompt 文件写规则/口径**（比如“不能编造事实”）
- **给每个模块准备 fallback（降级逻辑）**：没有 API Key 也能跑通流程（质量较差但不至于挂）

你后面自己构建 agent，90% 都会重复这套思路。

---

## 3. 目录结构怎么背（背下来就能口述项目骨架）

项目根目录 `job-agent-mvp/` 下核心文件如下：

- `main.py`：FastAPI 服务入口（提供 `/analyze`）
- `app.py`：Streamlit 页面入口（提供可视化输入输出）
- `services/`：**真正的业务逻辑**（Agent 的模块都在这里）
  - `orchestrator.py`：**编排器**（把多个模块按顺序串起来）
  - `llm_client.py`：LLM 统一调用封装（结构化输出 + 降级）
  - `jd_analyzer.py`：JD 解析模块
  - `candidate_profiler.py`：候选人结构化模块（本地规则）
  - `match_evaluator.py`：匹配分析模块
  - `resume_rewriter.py`：项目改写模块
- `schemas/`：每个模块的输出 Schema（Pydantic）
- `prompts/`：每个模块的 system prompt（“规则/口径/约束”）
- `utils/`：一些通用解析/格式化工具（比如把文本拆成 bullet）
- `sample_data/`：示例输入（帮助你快速跑通）

如果你只能记住一句话：  
**入口在 `main.py/app.py`，流程在 `services/orchestrator.py`，智能在 `services/* + prompts/* + schemas/`*。**

---

## 4. 从“按下按钮/调用接口”开始，数据到底怎么流（全流程）

下面按时间顺序讲清楚一次请求发生了什么。你可以直接拿这段去口述。

### 4.1 第 0 步：用户输入在哪里？

你有两种方式触发同一条链路：

- **网页方式**：`streamlit run app.py`
  - 用户在页面里填 `jd_text`、`candidate_text`，选择 `target_role`
  - 点击“开始分析”
- **接口方式**：`uvicorn main:app --reload --port 8000`
  - 客户端请求 `POST /analyze`，传同样 3 个字段

两种方式最终都会调用同一行：`orchestrator.run(...)`。

> 重要理解：**页面/接口只是“收集输入与展示输出”**。Agent 的“智能”不在入口文件里。

---

### 4.2（重要！） 第 1 步：编排器 orchestrator 做了什么？

`services/orchestrator.py` 的 `JobAgentOrchestrator.run()` 固定按顺序做 4 件事：

1. `jd_analyzer.analyze()`：解析 JD
2. `candidate_profiler.profile()`：把候选人文本变结构化
3. `match_evaluator.evaluate()`：做匹配分析
4. `resume_rewriter.rewrite()`：做项目改写

最后打包成一个 dict 返回，并附带 `meta`。

你可以把 orchestrator 理解成：

- **项目总导演**：谁先谁后、每步输入从哪来、输出给谁用
- 它本身不“聪明”，只负责“把聪明的模块串起来”

---

### 4.3 第 2 步：JD 解析模块怎么工作？

文件：`services/jd_analyzer.py`  
它做的事非常固定：

1. **读取提示词**：`prompts/jd_analysis.md`
2. 组装 `user_prompt`（把 `target_role` 和 `jd_text` 拼进去）
3. 准备一个 **fallback 结果**（本地规则抽取）
4. 调用 `LLMClient.generate_structured(...)`，并指定输出必须符合 `schemas/jd_schema.py` 里的 `JDAnalysis`

产出：`jd_analysis`（结构化 JSON）

你要理解的关键点：

- Prompt 里写了“不得编造”“信息不足要写出来”
- Schema 规定了字段：`responsibilities/required_skills/keywords/...`
- 有 Key 时：模型生成 → JSON Schema 约束 → Pydantic 校验
- 无 Key/失败时：直接返回 fallback（保底能跑通）

---

### 4.4 第 3 步：候选人结构化模块怎么工作？（这里不靠 LLM）

文件：`services/candidate_profiler.py` + `utils/parser.py`

它的目标：把自由格式的候选人文本尽量拆成：

- `skills`：技能条目
- `projects`：项目条目
- `experiences`：经历条目
- `missing_items`：缺失项列表（让后续分析知道“哪里信息不够”）
- `summary`：简短统计

解析策略（新手要这样理解）：

- 先按“标题/冒号”把文本切成段（比如 `技能:`、`项目:`）
- 段里出现“技能/项目/经历”等关键词就归类到对应列表
- 如果切不出来：就拿全文 bullet 的前 N 条做保底（所以一定不会是空）

> 这一块是 MVP 很常见的取舍：先用规则解析跑通，再慢慢升级成更强的简历结构化能力。

---

### 4.5 第 4 步：匹配分析模块怎么工作？  ---后续优化： 如何让匹配不死板

文件：`services/match_evaluator.py`

输入：

- `jd_analysis`（上一步产出）
- `candidate_profile`（候选人结构化产出）
- `target_role`

输出 Schema：

- `schemas/match_schema.py` 的 `MatchAnalysis`

思路：

- 有 Key：让 LLM 按 prompt + schema 生成“高匹配点/缺口/建议…”
- 无 Key：做一个非常朴素的 set 对比：
  - JD 的 `required_skills + keywords` 当作“岗位技能集合”
  - 候选人的 `skills` 当作“候选人技能集合”
  - 交集 → `high_match_points`
  - 差集 → `weak_match_points/gap_items`
  - 如果候选人缺失项多，就往 `risk_points` 里写“结论可靠性有限”

> 你要记住：fallback 不追求“聪明”，追求“**流程稳定 + 输出结构稳定**”。

---

### 4.6 第 5 步：项目改写模块怎么工作？

文件：`services/resume_rewriter.py`

输入：

- `candidate_text`（原始文本）
- `target_role`
- `jd_keywords`（从 `jd_analysis` 里拿到的关键词）

输出 Schema：

- `schemas/rewrite_schema.py` 的 `ProjectRewrite`

提示词 `prompts/project_rewrite.md` 强调：

- **严禁编造事实**
- 建议“动作-方法-结果”，尽量量化；没数据就提示补充

fallback 的做法：

- 把候选人 bullet 前几条取出来
- 套个模板“围绕目标岗位，在真实项目中完成：xxx”
- notes 里明确：仅优化表达，不新增事实；关键词不足就提示先完善 JD

---

## 5. LLMClient：为什么要统一封装？（理解它=理解工程化）

文件：`services/llm_client.py`

它做了三件非常工程化的事情：

1. **统一读取环境变量**
  - `OPENAI_API_KEY` 有值才启用模型
  - `OPENAI_MODEL` 默认 `gpt-4o-mini`
2. **统一“结构化输出”调用方式**
  - 每个模块都传入一个 Pydantic model
  - 它把 model 转成 JSON Schema，并强制模型按 schema 输出
3. **统一异常与降级**
  - 没 key：直接返回 fallback
  - 调用失败：直接返回 fallback

你可以把它理解成 Agent 项目里的“LLM SDK Adapter（适配层）”：

- 上层模块不关心 OpenAI 细节
- 上层只关心：给我按 schema 的结构化结果；如果不行就给 fallback

---

## 6. 你如何“口述整个项目”（给你一套背诵稿）

你可以按这个顺序说（面试/复盘都能用）：

1. 这是一个求职投递流程的任务型 Agent，输入 JD + 候选人文本 + 目标岗位方向，输出 JD 解析、候选人结构化、匹配分析、项目改写四块结构化结果。
2. 项目有两个入口：FastAPI 的 `/analyze` 和 Streamlit 页面，但它们都只负责收集输入并调用 orchestrator。
3. 核心是 `services/orchestrator.py`：按固定顺序执行 4 个模块并汇总结果。
4. 每个模块如果启用了 API Key，就通过 `LLMClient.generate_structured()` 按 Pydantic schema 强制结构化输出；否则走本地 fallback，保证 MVP 可运行。
5. Prompt 文件规定口径（比如“不能编造事实”“信息不足要写出来”），Schema 文件规定输出字段，二者一起让输出可控、可消费。

---

## 7. 如果你要自己从零搭一个同款 Agent，照这份清单做（可复刻步骤）

把这段当“配方”：

### 7.1 先定义你要输出什么（Schema 先行）

- 为每个子任务写一个 Pydantic model（例如 JDAnalysis、MatchAnalysis…）
- 字段尽量少但足够用，默认值要合理（保证稳定）

### 7.2 再写每步的 prompt（规则写在 prompt   里）

- 明确硬约束：不能编造、信息不足要写缺失项
- 明确输出风格：中文、列表、可执行
- 明确必须符合 schema

### 7.3 做一个 LLMClient 适配层

- 统一模型调用（温度、错误处理、schema 约束）
- 统一降级 fallback（没有 key 也能跑通）

### 7.4 写每个服务模块（一个模块只做一件事）

- 模块结构建议固定为：
  - 读 prompt
  - 组 user_prompt
  - 准备 fallback
  - 调 `LLMClient.generate_structured(schema_model=..., fallback_data=...)`

### 7.5 写 orchestrator（把步骤串起来）

- 把你的任务链路按顺序写死（MVP 阶段越固定越好）
- 每步输出作为下一步输入的一部分
- 最终返回一个 dict/JSON，前端/接口只负责展示

### 7.6 做两个入口（可选，但很实用）

- API 入口（FastAPI）：方便接入别的系统/脚本
- 页面入口（Streamlit）：方便你自己快速体验迭代

---

## 8. 本项目有哪些“可优化点”（你后续升级 Agent 的方向）

下面这些优化点基本覆盖了从 MVP 到可用产品的路线：

### 8.0 利用 **依赖注入/模型选择** 进行agent调用



### 8.1 让它变成“多轮 Agent”（目前是单轮）

现状：`/analyze` 一次性输入三段大文本。  
优化：

- 如果 `candidate_profile.missing_items` 不为空，让系统返回“追问问题列表”，引导用户补充材料
- 或在 Streamlit 里做多轮表单（逐步补齐技能/项目/指标）

### 8.2 提升候选人结构化质量（目前规则很轻）

现状：`utils/parser.py` 用关键词+分段，容易漏项/混项。  
优化：

- 增加更强的解析：比如先让 LLM 做“简历结构化抽取”（同样用 schema 约束）
- 兼容更多格式（PDF/Docx/Markdown），并把原文与抽取结果同时保留以便追溯

### 8.3 更严谨的“事实边界”控制

现状：依靠 prompt 约束“不编造”。  
优化：

- 在改写前做“事实清单抽取”，改写后做“事实一致性校验”（差异则标红/拒绝输出）
- 对敏感项（指标、技术栈、时间）做白名单校验：仅允许来自原文的值

### 8.4 让输出更“可投递/可复制”

现状：输出是 JSON，页面展示为 JSON。  
优化：

- 输出同时提供 Markdown 版本（简历可直接复制）
- 支持导出 Docx/PDF
- 改写结果按“STAR/三段式（动作-方法-结果）”模板排版

### 8.5 评估与可观测性（工程化必做）

现状：失败就 fallback，没日志/没指标。  
优化：

- 记录每步耗时、是否走 fallback、prompt 版本、模型版本
- 做离线评测集（sample_data 扩展成 tests），对比改动前后质量

### 8.6 让它支持“多材料检索”（README 提到的向量检索）

现状：只有一段 candidate_text。  
优化：

- 把候选人多份材料切块入库（向量检索）
- 每次针对 JD 关键词检索最相关片段再喂给改写/匹配模块（RAG）

### 8.7 更好的错误处理与用户提示

现状：异常直接 fallback，没有解释原因。  
优化：

- 返回 `meta.errors` 或 `meta.warnings`，说明是“无 key”“超时”“schema 校验失败”等
- 在页面提示用户如何修复（例如提示配置 `.env`）

---

## 9. 你现在可以做的“最小练习”（帮助你真正理解）

你不需要改代码也能练习理解：

1. 打开 `services/orchestrator.py`，把 `run()` 的 4 步顺序背下来
2. 打开 `services/jd_analyzer.py`，找“读 prompt → user_prompt → schema → fallback → generate_structured”这条模式
3. 同样方式看 `match_evaluator.py`、`resume_rewriter.py`，你会发现它们结构几乎一致
4. 打开 `schemas/*.py`，把每个模块输出字段背下来（这就是稳定 API）
5. 打开 `prompts/*.md`，把“硬性约束”背下来（这就是产品规则）

做到这 5 步，你就能口述 80% 以上。

---

## 10. 一句话总结（你应该带走的心智模型）

**Agent 应用 ≈ 固定流程编排（orchestrator） + 可控的结构化输出（schema） + 可复用的模型调用层（LLMClient） + 写清楚规则的提示词（prompts） + 随时可运行的降级逻辑（fallback）。**