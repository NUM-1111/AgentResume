# candidate_profile 抽取模块复盘

> 本文档聚焦候选人信息结构化模块的实际输出质量、存在问题与优化方向。

---

## 本次实际输出（真实结果）

系统对候选人简历的结构化输出如下：

```json
{
  "raw_text": "项目经历\nIntelliVault（多租户智能知识库与问答平台）...",
  "skills": [
    "项目经历",
    "IntelliVault（多租户智能知识库与问答平台） 2025.12 - 至今",
    "核心开发者 Java 17, Spring Boot 3, Spring AI, PostgreSQL, MongoDB, Milvus, Docker",
    "基于 Java 17 + Spring Boot 3 + Spring AI 开发企业级多租户智能知识库与问答平台，完成知识",
    "库管理、文档上传与处理、检索问答、会话管理、用户设置等核心模块设计与实现。",
    "...（后续均为原文整句）"
  ],
  "projects": [
    "项目经历",
    "IntelliVault（多租户智能知识库与问答平台） 2025.12 - 至今",
    "核心开发者 Java 17, Spring Boot 3, Spring AI, PostgreSQL, MongoDB, Milvus, Docker",
    "基于 Java 17 + Spring Boot 3 + Spring AI 开发企业级多租户智能知识库与问答平台，完成知识",
    "...（后续均为原文整句）"
  ],
  "experiences": [
    "（与 projects 内容几乎完全重复）"
  ],
  "missing_items": [],
  "summary": "候选人材料中提取到技能 38 项，项目条目 8 条，经历条目 8 条。"
}
```

---

## 问题分析

### 直接问题

**1. skills / projects / experiences 三个字段内容高度重叠**

- `projects` 和 `experiences` 几乎是同一份内容的复制
- `skills` 里混入了大量项目描述原句，而不是独立的技能点
- 三个字段没有做到职责分离

**2. 标题和正文没有分干净**

- `"项目经历"` 这种章节标题被当成一条 skill 条目
- `"核心开发者 Java 17, Spring Boot 3..."` 这种角色+技术栈行被当成一条 skill
- 正文描述句被逐行切割，导致一句话被拆成两条（如"完成知识" / "库管理、文档上传..."）

**3. missing_items 识别不准**

- 输出为空数组 `[]`
- 但候选人明显缺少：工作经历（无实习/全职）、学历信息、GitHub 链接、量化数据等
- 说明 missing_items 的判断逻辑没有真正工作

**4. summary 数字不可信**

- "技能 38 项，项目条目 8 条，经历条目 8 条" 是对切割后的行数统计，不是真实的语义单元数量
- 候选人实际只有 2 个项目，但系统报告 8 条

---

## 本质问题

> 当前 candidate_profile 更像"切文本"，不是"真正结构化"

系统做的事：把简历文本按换行符切割，然后塞进不同字段。
系统应该做的事：识别语义单元（项目名、时间、角色、技术栈、每条成就），按结构化 schema 填充。

---

## 优化方向

### 短期（prompt 层面）

1. 明确要求 `skills` 只输出独立技能点，格式为：
   ```
   ["Java", "Spring Boot", "RAG", "Prompt Engineering", "Docker", ...]
   ```
   不允许出现完整句子

2. 明确要求 `projects` 按项目级别结构化，每个项目是一个对象：
   ```json
   {
     "name": "IntelliVault",
     "period": "2025.12 - 至今",
     "role": "核心开发者",
     "tech_stack": ["Java 17", "Spring Boot 3", "Spring AI", "PostgreSQL", "MongoDB", "Milvus", "Docker"],
     "highlights": [
       "设计分层存储架构，分别承载文档元数据、会话记录与向量检索",
       "实现 RAG 全链路：文档处理→向量检索→SSE 流式问答",
       "实现检索隔离与向量生命周期管理，降低串库与脏数据风险"
     ]
   }
   ```

3. 删除 `experiences` 字段（与 `projects` 重复，无独立价值），或明确区分为"工作经历"（实习/全职）

4. 明确 `missing_items` 的检查清单，在 prompt 中列出必须检查的项：
   - 是否有工作/实习经历
   - 是否有学历信息
   - 是否有量化数据
   - 是否有 GitHub/作品集链接

### 中期（schema 层面）

将 candidate_profile schema 从扁平结构升级为嵌套结构：

```json
{
  "basic_info": { "name": "...", "education": "...", "english_level": "CET-6" },
  "skills": ["Java", "Spring Boot", "RAG", ...],
  "projects": [
    {
      "name": "...",
      "period": "...",
      "role": "...",
      "tech_stack": [...],
      "highlights": [...]
    }
  ],
  "work_experiences": [],
  "missing_items": ["工作/实习经历", "学历信息", "量化数据", "GitHub链接"],
  "confidence": "medium"
}
```

### 核心认识

> candidate_profile 是整个 pipeline 的"中间表示"，它的质量直接决定 match 和 rewrite 的上限。
> 中间表示不干净，下游再聪明也救不回来。
