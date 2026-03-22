##  第一次优化分析过程

### 1 优化前：流程已通，与「可执行需求」仍有距离

《需求分析（具体化版本）》把抽象目标落为四类可验证需求：**正确性（JD/候选人中间表示）**、**可信度（match 证据、rewrite 边界）**、**决策辅助（可回答「为何适合 / 何处不配 / 面试风险」）**、**效率（固定管线、结构化可复用、工程化校验与降级）**。

第一次优化前，系统已是**形式稳定的 MVP**（能跑通 `JD → Profile → Match → Rewrite`），但对照上述标准，核心缺口集中在需求分析第 3 节差距表所概括的四点：

| 模块 | 当时状态 | 相对具体化需求的缺失 |
| --- | --- | --- |
| `candidate_profile` | 更像切文本 | 缺少稳定、可复用的事实层（独立技能点、结构化项目、去重） |
| `jd_analysis` | 更像总结 JD | 缺少可逐条驱动 match 的执行标准（SkillItem、关键词分桶） |
| `match` | 词匹配、易过度推断 | 缺少证据分级与待验证清单 |
| `rewrite` | 表达变强但易越界 | 缺少硬性事实边界与新增内容自审（`added_facts`） |

因此问题不在「流程不通」，而在：**中间表示不干净、判断缺证据、生成缺边界**——与「基于事实的求职决策与表达系统」这一总目标尚有距离。

---

### 2 优化目标：按需求维度缩短差距，而非单点修 prompt

第一次优化围绕《需求分析》中的映射关系展开，把用户侧诉求落到模块级目标：

| 需求维度 | 优化前典型问题 | 第一次优化指向 |
| --- | --- | --- |
| 正确理解候选人 | profile 像切文本、字段重叠 | 独立 `skills`、结构化 `projects`、区分工作经历、可检查的 `missing_items` |
| 正确理解 JD | `required_skills` 大段原文、keywords 混杂 | SkillItem（priority / verifiable / evidence_hint）、keywords 四分桶、`candidate_focus` 带优先级与 `jd_risk_flags` |
| 可信匹配 | 弱证据推强结论 | `evidence_level`、`needs_verification`、结构化 MatchPoint、禁止单点功能推导综合能力 |
| 安全改写 | 虚构数字/功能、JD 词替换事实 | 禁止类规则、`added_facts`、以事实白名单约束输入 |
| 效率与可复用（工程侧） | 各步输出形态不一 | 各步结构化 JSON、schema 升级，便于下游直接消费而少重复解析原文 |

---

### 3 分模块：对照具体化标准，实际做了什么、达到了什么

#### 3.1 `candidate_profile`：从「切文本」到可下游复用的事实层

**对照需求：** `skills` 仅为独立技能点；`projects` 为 `{ name, period, role, tech_stack, highlights }`；经历与项目语义区分、不重复；`summary` / `missing_items` 能反映真实缺失而非形式统计。

**实际优化动作：** 约束 `skills` 去整句；将 `projects` 结构化为对象；消除与 `experiences` 的无价值重复，明确 `work_experiences`；强化 `missing_items`；引入 `basic_info` 等嵌套 schema。

**可观察结果（样例跑通时）：** `skills` 从混入整句的约 38 项收敛为约 18 项独立技能点；`projects` 从逐行切割文本转为结构化项目对象；`missing_items` 变为可执行检查项；`projects` 可作为 rewrite 的事实输入来源。

**小结：** 候选人侧从「杂乱原文碎片」推进为「可供 match / rewrite 稳定使用的事实中间表示」。

---

#### 3.2 `jd_analysis`：从「总结 JD」到「JD → 可执行标准」

**对照需求：** `required_skills` 拆为独立 SkillItem；keywords 明确分为 tech / capability / tool / domain；每项可单独被 match 判断，避免整段 JD 原文堆在 `required_skills` 里。

**实际优化动作：** keywords 四分桶；`required_skills` 结构化为带 priority、verifiable、evidence_hint 的条目；`candidate_focus` 增加优先级与 reason；补充 `jd_risk_flags`。

**可观察结果（样例）：** `required_skills` 从多条大段原文变为多条独立 SkillItem；keywords 由混合列表变为分桶结构；JD 输出可直接驱动 match 逐条评估。

**小结：** 从「读懂 JD」推进为「把 JD 变成可执行、可逐条核对的岗位要求标准」。

---

#### 3.3 `match`：从「词命中」到「证据驱动的判断」

**对照需求：** 每条匹配含 `point / evidence / evidence_level / jd_requirement`；`evidence_level` 覆盖 strong / medium / weak / inferred；禁止由单一功能推导综合能力；必须有 `needs_verification`；整体输出需支撑 high / weak、gap、risk、needs_verification 等决策视图。

**实际优化动作：** 引入证据等级与 `needs_verification`；`high_match_points` 升级为结构化 MatchPoint；明确禁止「单点 → 综合能力」式推断。

**可观察结果（样例）：** `high_match_points` 由纯字符串变为带证据与等级的结构化列表；出现明确的 `needs_verification` 条目；`rewrite_focus` 不再诱导候选人「补」不存在的能力。

**小结：** 匹配从「关键词碰撞」推进为「带证据等级与待验证清单的判断」，与用户要的「可置信结论」更一致。

---

#### 3.4 `rewrite`：从「更强表达」到「受约束、可承认的表达」

**对照需求：** 禁止虚构数字与百分比、禁止原文未出现的功能与技术；禁止用 JD 词汇替换候选人事实、禁止能力逐级拔高；通过 `added_facts` 显式记录新增内容（理想为空）；rewrite 输入原则上仅依赖强证据与项目事实（与决策辅助需求衔接）。

**实际优化动作：** 写入上述禁止类规则；输入侧以事实白名单约束；引入 `added_facts` 自审。

**可观察结果（样例）：** 虚构量化、脑补功能、明显拔高在样例中收敛；`added_facts` 存在且可为空列表。

**小结：** 改写从「会生成更强话术」推进为「在事实边界内、用户敢用的表述」。

---

### 4 第一次优化整体结论

对照《需求分析》中的关键结论，第一次优化的本质不是「模型更会写」，而是：

- 建立 **中间表示**（候选人事实层 + 岗位标准层）；
- 引入 **证据机制**（缓解过度推断）；
- 强化 **事实边界**（抑制幻觉与越界改写）。

用产品语言概括：项目从 **「流程跑通的生成型 Agent MVP」**，推进到 **「具备结构化事实与约束、开始向可控推理型 Workflow Agent 靠拢的 MVP」**——与需求文档中「从生成型 Agent → 可控推理型 Workflow Agent」的方向一致，但尚未在全部维度上达标（见下文「仍存在的 需求差距」）。

---

### 5 仍存在的 需求差距

以下条目按《需求分析》中的可执行标准与第 5 节「下一步方向」归纳，表示**第一次优化之后仍与理想状态有距离**的部分（含工程与算法两侧）。

**正确性**

- **解析鲁棒性：** 简历解析在软换行等边界场景仍可能错切句子，影响事实层质量；与「skills / projects 可直接用于匹配与改写、无需再解析」的目标仍有摩擦。
- **JD / Profile 纯度：** 需在更多真实 JD 与简历上验证「无整段 JD 混入 `required_skills`」「skills 无整句」是否稳定成立，避免个案达标、长尾失效。

**可信度与决策辅助**

- **match：** 「能力建模」仍偏 skill / 证据字面层，与需求分析提到的「不是简单 skill 对 skill」相比，综合能力与软技能的刻画仍粗；`weak_match_points`、`gap_items`、`risk_points` 等决策视图在体验上是否始终完整、可解释，仍需持续对齐产品预期。
- **rewrite 与 match 的衔接：** 需求规定 rewrite 原则上只使用 high_match（strong / medium）与 `candidate_profile.projects`，并排除 weak / inferred；需在实现与评测上持续校验是否**严格执行**，避免策略文档与运行时行为漂移。
- **验证闭环：** `needs_verification` 目前更多是「列出待核实项」，与用户侧「如何补证、补完如何回灌」的闭环仍缺产品/流程设计。

**效率与工程**

- **管线固化：** 需求中的「每步 JSON、可单独复用、避免重复解析原文」在架构上已靠拢，但是否全链路满足 **Pydantic 校验、无 LLM 降级、JSONL 日志** 等工程清单，需以代码与部署为准逐项核对。
- **中间表示复用：** `JDAnalysis → Match`、`Profile → Rewrite` 的复用程度仍依赖具体实现；若某步仍回退到原始长文本，则与「效率需求」中的理想状态仍有差距。

**能力与体验（需求分析第 5 节延伸）**

- **rewrite：** 在「不越界」前提下如何增强可读性、STAR 化与针对性，仍属未充分展开的「第二次优化」空间。
- **JD：** 行业 / 岗位知识增强（非纯文本拆解）尚未系统化，与「JD → 可执行标准」的长期目标相比仍偏文本规则与模型提示。

---

*说明：本节「差距」用于对照《需求分析（具体化版本）》自检；具体以仓库内实现与评测为准，随二次优化可逐条勾选关闭。*
