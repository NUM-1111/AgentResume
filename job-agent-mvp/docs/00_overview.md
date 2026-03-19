# 项目二复盘总览

> 本文件是整个复盘文档的入口，详细模块见各子文件。

---

## 背景说明

### 这次分析是什么

本次运行是 **Project 2（求职场景 Agent MVP）** 的一次完整端到端测试。

- 输入：一份真实 JD（AI算法工程师岗位）+ 一份候选人简历
- 流程：JD 解析 → 候选人信息结构化 → 匹配度分析 → 简历改写建议
- 目的：验证整个 Workflow Agent 链路的分析质量

### 测试用的 JD 是什么岗位

**岗位名称：AI 算法工程师**

核心职责方向：
- 从零设计 AI 原生架构，包括 Agent 系统的业务流程建模与闭环设计
- 将 AI 不确定性转化为工程确定性（任务拆解、依赖编排、边界治理）
- Agent 关键模块落地：上下文/记忆管理、规划推理、工具集成、RAG/知识增强
- 建立分层验证体系与 CI 阻断机制，持续跟踪缺陷密度与线上故障率
- 通过灰度发布与渐进式 rollout 降低 MTTR

关键技术词：`AI原生架构` `Agent系统` `Prompt Engineering` `RAG` `工具调用` `任务编排` `高可用架构` `监控告警` `CI阻断` `灰度发布` `MTTR` `LangChain` `vLLM` `Ollama`

### 候选人是谁（简历摘要）

两个主要项目：

**IntelliVault（多租户智能知识库与问答平台）** 2025.12 - 至今
- 技术栈：Java 17 + Spring Boot 3 + Spring AI + PostgreSQL + MongoDB + Milvus + Docker
- 核心能力：RAG 全链路（文档处理→向量检索→流式问答）、分层存储架构、JWT 鉴权、检索隔离与向量生命周期管理

**基于大模型的求职场景智能助手（Agent MVP）** 2025.10 - 2025.12
- 技术栈：Python + LLM API + Prompt Engineering
- 核心能力：JD 解析、关键词提取、简历匹配分析、项目经历重写、多轮交互优化

核心技能：Java / Spring Boot / RESTful API / MySQL / PostgreSQL / MongoDB / Milvus / Spring AI RAG / Docker / Git / Linux / CET-6

---

## 当前阶段结论

系统已经是一个**形式稳定的 MVP**，但还不是**事实稳健的 MVP**。

整体链路已跑通：
- orchestrator 能正常串联各模块
- schema 能保证输出结构稳定
- prompt 能基本控制输出方向
- 系统能产出完整分析结果

但核心问题集中在**分析质量**，而非流程是否跑通。

---

## 四大核心问题（快速索引）

| 模块 | 问题本质 | 详细文档 |
|------|---------|---------|
| candidate_profile 抽取 | 更像"切文本"，不是真正结构化 | [02_candidate_profile.md](./02_candidate_profile.md) |
| JD 分析 | 更像"总结"，不是可驱动下游的拆解 | [01_jd_analysis.md](./01_jd_analysis.md) |
| match 分析 | 词匹配偏多，能力匹配偏少，容易过度推断 | [03_match_analysis.md](./03_match_analysis.md) |
| rewrite 模块 | 输出表达变强了，但事实边界没有守死 | [04_rewrite_module.md](./04_rewrite_module.md) |

---

## 优化优先级

1. **先优化 candidate_profile**：把中间结构化做干净，是后续所有模块的基础
2. **再收紧 rewrite**：优先守住事实边界，这是最高风险模块
3. **再升级 match**：从关键词匹配走向能力匹配
4. **最后优化 orchestrator**：加入状态判断和质量检查

---

## 一句话核心认识

> 一个 Workflow Agent 真正难的，不是把模块串起来，而是让中间表示干净、让判断不过度、让生成不越界。
