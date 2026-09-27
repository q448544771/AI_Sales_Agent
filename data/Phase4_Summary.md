# AI Sales Agent 项目开发进度与阶段规划——Phase 4 完成版

> 更新日期：2026-09-26  
> 当前阶段：Phase 0–4 已完成；下一阶段：Phase 5 Multi-Agent（从 Phase 5.1 架构设计开始）  
> GitHub：`https://github.com/q448544771/AI_Sales_Agent`  
> Phase 4 代码提交：`8d2639e5578828ed8405c7b4b286b9711f5ad32c`  
> Phase 4 标签：`phase4-rag-complete`  
> 说明：这是开发过程记录。示例企业/招聘信息来自项目当前测试工具及 CRM 数据，不应作为已核验的真实商业情报。

## 一、项目目标与总体进度

项目目标：构建面向工业机器视觉质检解决方案的企业 AI 销售 Agent，以中国汽车零部件企业为目标，串联企业发现、购买信号分析、产品知识匹配、CRM 长期记忆、客户阶段管理及跟进建议，后续升级为 Multi-Agent 协作系统。

| 阶段 | 目标 | 当前状态 |
| --- | --- | --- |
| Phase 0 | 环境与项目结构 | ✅ 完成 |
| Phase 1 | Agent Core（Planner / Executor / Reviewer / LangGraph） | ✅ 完成 |
| Phase 2 | 企业数据与 Memory（SQLite、去重入库、CRM、Follow-up） | ✅ 完成 |
| Phase 3 | MCP 工具化（Company / CRM / Client / Adapter / 可靠性约束） | ✅ 完成 |
| **Phase 4** | **RAG 企业知识库、Knowledge MCP 和 Agentic RAG** | **✅ 完成且回归通过** |
| Phase 5 | Multi-Agent（Supervisor 和专业 Agent 协作） | ⏳ 下一阶段，5.1 架构设计 |

## 二、Phase 0–3 简要回顾

**Phase 0：环境搭建。** 使用 Windows、Conda Python 3.11 环境 `agent`；项目位于 `D:\AI_Sales_Agent`，接入 LangChain、LangGraph、DeepSeek API，并建立模块化代码结构。

**Phase 1：Agent Core。** `SalesAgentState` 管理目标、研究计划、消息、候选客户和任务状态；Planner 制定购买信号与检索方向；Executor 经模型 Tool Calling 执行任务；Reviewer 整理候选客户与建议；LangGraph 串联节点与工具循环。

**Phase 2：企业数据与 Memory。** SQLite + SQLAlchemy 保存 Lead；Memory Retrieval 在任务开始时查询历史客户；Review 结果支持已有客户更新、新客户入库；Follow-up 生成或保留跟进动作。当前 CRM 阶段模型为 `new → contacted → qualified → meeting → proposal → negotiation → won`，另有 `lost`；不能仅凭公开扩产、新闻、招聘或评分自动推进真实销售阶段。

**Phase 3：MCP 工具化。** 公司信息查询和 CRM 操作通过 MCP Server、Client、Adapter 供 Agent 调用；已有工具包括 `search_company`、`get_company_news`、`get_company_jobs`、`query_leads`、`create_lead`、`update_lead_stage`，并引入调用可靠性与 CRM Stage Transition Guard。

## 三、Phase 4 目标、边界与最终成果

### 3.1 建设目标

将企业内部产品/技术知识从零散文本变成可检索的知识库，使销售 Agent 能区分：

1. **企业事实/信号**：公司新闻、招聘和已保存的 CRM 数据；
2. **内部产品知识**：知识库真实记载的功能和适用检测场景；
3. **销售推断与待确认项**：产品适配可能性、技术交流、ROI 测算和 POC 建议。

最终不是简单地“给 Prompt 拼上一段资料”，而是形成完整的两种 RAG 接入方式：固定 Knowledge Retrieval Node 确保 Reviewer 有知识上下文；Agentic RAG 则允许 Executor 自己决定何时通过 MCP 调用知识检索工具。

### 3.2 实际实现的链路

```text
知识源（目前：vision_solution.md）
       │
       ▼
Document Loader → Text Splitter → Embedding
       │
       ▼
Chroma Persistent Vector Store
       │
       ▼
Product Retriever
       ├──────────────► 固定 Knowledge Retrieval Node
       │                      │
       │                      ▼
       │                 knowledge_context → Reviewer
       │
       └──► Knowledge Tool → Knowledge MCP Server
                                  │
                                  ▼
                           MCP Client / Adapter
                                  │
                                  ▼
                             Executor Agent
```

### 3.3 当前知识库内容与边界

当前已验证的知识来源是 `app/knowledge/data/products/vision_solution.md`，包含：工业相机、光源、图像算法和 AI 模型；汽车零部件的划痕、凹坑、毛刺、污渍等外观检测；视觉尺寸测量；漏装、错装、少件等装配检测；新能源结构件的焊缝、表面及尺寸检测；定性地说明速度、稳定性和数据追溯能力。

**不得视为已完成的内容**：真实客户可识别的成功案例、具体检出率/误报率/节拍/精度、报价、量化 ROI、回本周期、认证和已完成的 POC。原计划提出的“行业案例、报价文件”是知识库扩展方向，不代表已采集并验证入库。`vision_solution.md` 的“新能源汽车案例”章节目前属于能力介绍，不能冒充经核实的真实交付案例。

## 四、Phase 4 详细开发步骤与实现方式

### 4.1 RAG 基础设施 ✅

- 创建 `app/knowledge/` 目录，建立文档加载、切分、Embedding、向量数据库与 Retriever 的独立模块。
- `app/knowledge/loaders/document_loader.py`：读取 Markdown 产品文档；`text_splitter.py`：构建可检索的文档片段。
- `app/knowledge/embeddings/embedding_model.py`：提供 Embedding 模型。
- `app/knowledge/vectorstore/chroma_store.py`：负责 Chroma 向量库；本地持久化数据由 `.gitignore` 排除，不上传 GitHub。
- `app/knowledge/build_kb.py`：知识库构建入口；`app/knowledge/retriever/product_retriever.py`：产品知识检索。
- 通过 Loader、Chunk、Embedding、Chroma 和 Retriever 对应测试验证基础链路。

### 4.2 固定 RAG 工作流 ✅

- 新增 `app/agent/knowledge_retriever.py` 对应知识检索节点。
- 扩展 `app/agent/state.py`，加入 `knowledge_context`。
- 在 `app/graph/workflow.py` 中将知识检索并入工作流，并将结果传递至 Reviewer。
- Reviewer 根据企业信号和知识来源形成 `solution_match`，同时保留知识不足时的待确认项。
- 该链路的作用是确保 Review 阶段可以拿到内部产品知识，不完全依赖 Executor 是否自行发起知识工具调用。

### 4.3 RAG Tool / MCP 封装与 Agentic RAG ✅

- `app/tools/knowledge_tools.py`：把产品知识检索封装为可调用工具 `search_product_knowledge`。
- `app/mcp/knowledge_server.py`：对外提供 Knowledge MCP 服务。
- `app/mcp/client.py` 与 `app/mcp/adapter.py`：将 MCP 工具加载并适配到 Agent Tool Calling 接口。
- `app/agent/executor.py`：接入 Knowledge Tool；Executor 可在调研过程中判断是否需要查产品能力，而不仅使用固定 RAG 节点。
- 现有工具体系总计包括 Company MCP、CRM MCP、Knowledge MCP 对应的七项工具（3+3+1）。

### 4.3.5 Agentic Retrieval 与可靠性保护 ✅

为避免自主检索引入的重复调用、预算失控及无根据的销售话术，在 Executor / Reviewer 增加规则：

- Knowledge Tool 有独立预算：每任务最多 2 次、每轮最多 1 次（当前代码约束）。
- 企业搜索采用跨消息的 Tool Call ID 统计与饱和搜索预算，避免同一调用同时被 AIMessage 和 ToolMessage 重复计数。
- 对空搜索结果做连续次数统计，必要时停止无效地区检索，转向既有 CRM 的分析和知识匹配。
- 产品匹配只能引用检索到的知识；没有数字、案例或 ROI 数据时，不得凭空生成。
- 可以建议“收集成本后测算 ROI”“需求确认后进行打光/成像或 POC 验证”，但不能宣称已有证实的 ROI 或 POC 结果。
- 销售阶段保持与真实触达进展绑定；新闻、招聘和高分只影响商机优先级，不直接改变 CRM stage。

### 4.3.6 Full Graph Regression ✅

最后一次执行：

```powershell
python -m py_compile .\app\agent\executor.py
python test_graph.py
```

观察到：语法检查通过；Memory Retrieval 返回 8 条历史客户；固定知识检索返回 1 条产品知识；Reviewer 输出 3 家候选客户并附知识库支持的 `solution_match`；Follow-up 阶段正常完成；最终状态为 `followup_completed`；`knowledge_context` 被完整保存到 Final State。

Agentic Retrieval 方面，Executor 经 `search_product_knowledge` 调用 Knowledge MCP，获得带 `source` 的检索结果；CRM 更新动作的响应中 `stage_changed: false`，表明本轮没有因公开情报而自动推进阶段。

**搜索预算说明：**日志实际显示本轮执行了 3 次 `search_company`（四川、天津、福建均无结果），没有发生旧版本的 6/4 超额调用。模型最终自然语言报告写了“4/4”，与实际工具调用次数不一致；这是未完全解决的**报告计数表述问题**，并非底层预算执行超额。

## 五、开发中遇到的问题及解决过程

| 问题 | 现象/原因 | 已采取的解决方法 | 结果 |
| --- | --- | --- | --- |
| DeepSeek `reasoning_content` 兼容 | Thinking 模式下消息兼容性异常 | 区分 Planner/Reviewer 与 Executor 的模型调用策略，并清理不兼容推理消息内容 | 核心流程能完整运行 |
| `knowledge_context` 丢失 | 检索结果未在 Graph State/Reviewer 间可靠传递 | 扩展 `SalesAgentState`，固定节点返回知识上下文，由 Reviewer 显式使用 | Final State 可见知识内容与来源 |
| Search Budget 超限（曾出现 6/4） | 多轮 Tool Calling 预算统计不一致 | 按唯一 Tool Call ID 统计请求和回执；加入按轮限流、空结果停止规则 | 最近回归未超额 |
| Knowledge Tool 重复检索 | Agent 自主调用可能反复查同类知识 | 新增知识检索统计和每任务、每轮的调用限制 | 已接入 Executor |
| Reviewer 无依据生成 ROI/案例 | 将产品能力描述误当成真实案例或量化性能 | 增加证据边界和销售动作可靠性规则；将 ROI/POC 改为后续测算或验证 | 最新 Reviewer 建议符合证据边界 |
| 不当推进 CRM Stage | 以招聘/扩产信号代替真实触达 | 明确 Stage Guard 和 Agent 提示约束；仅依据真实跟进状态推进 | 最近更新全部 `stage_changed: false` |
| `NameError: get_knowledge_statistics` | Executor 使用知识统计函数，但代码中缺少定义 | 在实际 `executor.py` 中补回函数并进行语法与完整图回归 | 不再触发该错误 |
| 历史 CRM 旧话术回流 | 启动时 Memory 快照仍含旧 ROI/自动升级话术 | 本轮新建议与 CRM 更新遵循新规则；历史快照不实时回填 | **遗留数据清理待后续优化** |

## 六、关键测试脚本和成果文件

**主要代码**：

```text
app/agent/knowledge_retriever.py
app/agent/executor.py
app/agent/reviewer.py
app/agent/state.py
app/graph/workflow.py
app/knowledge/build_kb.py
app/knowledge/data/products/vision_solution.md
app/knowledge/embeddings/embedding_model.py
app/knowledge/loaders/document_loader.py
app/knowledge/loaders/text_splitter.py
app/knowledge/retriever/product_retriever.py
app/knowledge/vectorstore/chroma_store.py
app/tools/knowledge_tools.py
app/mcp/knowledge_server.py
app/mcp/client.py
app/mcp/adapter.py
```

**相关测试**：`test_rag_loader.py`、`test_rag_chunk.py`、`test_embedding.py`、`test_chroma.py`、`test_retriever.py`、`test_knowledge_tool.py`、`test_knowledge_node.py`、`test_knowledge_mcp_client.py`、`test_knowledge_mcp_adapter.py`、`test_agentic_rag.py`、`test_knowledge_guard.py`、`test_graph.py` 等。

上述文件体现开发覆盖范围；这份总结中确认的完整回归结果，以最终 `test_graph.py` 日志为准，不宣称所有独立测试在同一次运行中逐个复测。

## 七、遗留事项与范围声明

1. 清理历史 CRM 中旧的 `action` / `next_action` 话术，并区别“任务启动时 Memory 快照”与“数据库更新后实际记录”。
2. 修正最终报告的搜索预算自然语言计数（实际 3 次，报告写 4/4）。
3. 优化 Embedding 模型缓存、Chroma 增量更新、检索阈值、重复建库保护。
4. 研究固定 Knowledge Retrieval Node 和 Agentic Retrieval 的知识复用，减少重复检索；现阶段两条路径均已工作。
5. 后续增补经过核验的报价、可识别案例、技术指标、交付数据；当前示例产品文档不支持声称这些事实已存在。
6. 项目测试中使用的企业与新闻、招聘文本不能直接当作已经过外部来源核验的真实销售线索。

以上是后续质量与数据治理工作，不影响当前 Phase 4 的**工程实现及已执行回归**被标记为完成。

## 八、GitHub 存档与下一阶段

第四阶段提交成功推送到 GitHub `main`：`8d2639e5578828ed8405c7b4b286b9711f5ad32c`，标签 `phase4-rag-complete` 也已推送成功。之前的 `phase3-before-mcp` 标签及历史代码保留。Git 标签和 GitHub Release 是两回事；本总结只将已验证的 Git 推送与 Tag 推送视为已完成，不以此替代网页上 Publish Release 的操作。

下一阶段：**Phase 5 Multi-Agent**。原计划采用 Supervisor、Research、Analysis、Sales 和 CRM 的角色分工；Phase 5.1 先核对当前 `workflow.py`、`state.py` 与 MCP 目录，根据真实实现确定 Agent 边界和路由，重点复用已完成的 Knowledge MCP、CRM Guard 和 Agentic RAG，避免重新实现 Phase 4。

建议的后续推进顺序：5.1 架构及状态协议 → 5.2 Supervisor → 5.3 Research → 5.4 Knowledge/Analysis 的职责落地 → 5.5 销售动作与 CRM Agent → 5.6 多 Agent 图编排 → 5.7 可靠性与回归（最终子阶段编号以 Phase 5.1 设计结果确定）。

---

**阶段结论：Phase 4 的 RAG 基础设施、固定知识检索、Knowledge MCP 封装、Executor 自主检索、可靠性限制与完整工作流回归均已实现。当前正式进入 Phase 5.1 设计。**
