数据都读完了，现在做完整的对比分析。

---

## 两次输出对比分析

### 一、JD 分析模块

| 维度 | 第一次（Resume0to1） | 第二次（Resume1to2） |
|------|------|------|
| `required_skills` 结构 | 原文整句，9条大段话 | 结构化 SkillItem，20条独立技能点，每条含 priority / verifiable / evidence_hint |
| `keywords` | 混合平铺列表，30个词无分类 | 按 tech / capability / tool / domain 四桶分组，共约80个词，粒度更细 |
| `candidate_focus` | 10条纯文字建议，无优先级 | 10条，每条含 priority（high/medium/low）和 reason，按优先级排列 |
| `jd_risk_flags` | 无此字段 | 新增8条高门槛风险标注 |

**结论：✅ 完全满足**。JD 分析从"总结"变成了"可驱动下游的拆解"，required_skills 可以直接被 match 模块逐条评估，keyword_groups 分桶后下游可以区分权重。

---

### 二、candidate_profile 模块

| 维度 | 第一次 | 第二次 |
|------|------|------|
| `skills` | 38项，混入大量原文整句、章节标题、被换行截断的半句话 | 18项独立技能点（Java、Spring Boot、RAG、Docker 等），无完整句子 |
| `projects` | 8条，实为原文逐行切割，projects 和 experiences 内容几乎完全重复 | 2个结构化对象，每个含 name / period / role / tech_stack / highlights |
| `missing_items` | 空数组 `[]` | 3条有意义的缺失项：工作/实习经历、GitHub链接、量化数据 |
| `summary` | "技能38项，项目8条，经历8条"（行数统计，不可信） | "技能18项，结构化项目2个，无工作/实习经历，缺失项3处"（语义单元，准确） |
| `basic_info` | 无此字段 | 新增，提取到 education: 本科、english_level: CET-6 |
| `work_experiences` | 无此字段（experiences 与 projects 重复） | 独立字段，正确识别为空（候选人无实习/全职经历） |

**结论：✅ 完全满足**。这是改动最大的模块，从"切文本"变成了真正的结构化。projects 现在是可以直接传给 rewrite 的事实白名单。

---

### 三、match 分析模块

| 维度 | 第一次 | 第二次 |
|------|------|------|
| `high_match_points` 结构 | 6条纯字符串，无证据等级 | 7条结构化 MatchPoint，每条含 evidence / evidence_level / jd_requirement |
| 证据等级分布 | 无 | strong×4，medium×3，无 weak/inferred 的过度推断 |
| 过度推断问题 | 存在："具备数据契约与边界治理意识"（单一功能点推综合能力）；"具备任务拆解与分层设计能力"（数据库设计≠Agent规划） | 已修正：分层存储架构被正确标注为 strong 的"系统级权衡设计"，不再混淆为 Agent 能力 |
| `needs_verification` | 无此字段 | 新增5条，明确标注哪些匹配点需要面试验证 |
| `gap_items` | 6条，但混入了加分项缺口（CV/NLP模型训练） | 11条，区分更细，加分项缺口单独列出 |
| `rewrite_focus` | 6条，包含候选人没有的能力（"细化Agent模块落地：补充上下文管理、规划推理、工具集成"） | 5条，全部基于有证据支撑的方向，不再要求候选人"补充"没有的能力 |

**结论：✅ 基本满足**，但有一个残留问题值得注意：第二次的 `high_match_points` 里"具备分层存储架构设计能力"被标注为 `strong` 且 jd_requirement 是"系统级权衡设计"——这个映射仍然有点牵强（存储分层 ≠ 系统级权衡），不过相比第一次已经好很多，且有了 needs_verification 兜底。

---

### 四、rewrite 模块

| 维度 | 第一次 | 第二次 |
|------|------|------|
| 虚构量化数字 | 4处："约30%"、"约20%"、"约15%"、"约25%" | **0处**，`added_facts: []` 自查通过 |
| 脑补功能 | 2处："支持工具调用（如AI编程工具集成）"、"支持后续监控告警与自动恢复机制集成" | **0处** |
| 能力拔高 | "构建企业级AI原生架构"（替换了候选人原文）、"形成智能体式处理闭环" | 保留原文表述，仅做结构优化 |
| `added_facts` 字段 | 无此字段 | 新增，本次输出为空列表（自查通过） |
| `notes` | 4条，但仍在建议"补充CI阻断、灰度发布"等候选人没有的内容 | 2条，聚焦在候选人可以真实补充的内容（量化指标、阶段划分标准） |
| 改写策略 | 第一条就是"量化成果表达"（导致了虚构数字） | 第一条改为"严格基于原文事实，不添加任何未提及的数字、功能或技术" |

**结论：✅ 完全满足**，这是改动最显著的模块。事实边界守住了，`added_facts` 自查机制也正常工作。

---

## 总体评估

| 原始问题 | 是否解决 |
|------|------|
| candidate_profile 更像"切文本" | ✅ 解决，projects 结构化，skills 独立技能点，missing_items 有意义 |
| JD 分析更像"总结"，不可驱动下游 | ✅ 解决，required_skills 结构化，keywords 分桶，candidate_focus 有优先级 |
| match 词匹配偏多，容易过度推断 | ✅ 基本解决，证据等级机制生效，needs_verification 兜底，rewrite_focus 不再越界 |
| rewrite 事实边界没有守死 | ✅ 解决，虚构数字和脑补功能全部消失，added_facts 自查为空 |

**一个还值得关注的点**：candidate_profile 里 projects 的 highlights 仍然存在被换行截断的问题（如"完成知识" 和 "库管理..."是同一句话被切断了）。这是 parser 的正则切割逻辑还没完全处理好简历中的软换行，是下一步可以继续优化的方向。