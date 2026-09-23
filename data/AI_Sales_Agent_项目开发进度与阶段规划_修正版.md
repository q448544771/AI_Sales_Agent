# AI Sales Agent 项目开发进度与阶段规划（修正版）

## 项目目标

构建企业 AI 销售智能体，实现： - 自动发现潜在客户 - 企业购买信号分析 -
CRM 长期记忆 - Lead 生命周期管理 - 自动生成销售跟进动作 - 后续扩展 RAG
与 Multi-Agent

核心技术： - LangGraph - LangChain - DeepSeek API - MCP - RAG -
Multi-Agent

------------------------------------------------------------------------

# Phase 0：环境搭建 ✅

完成： - Python 环境 - LangChain - LangGraph - DeepSeek API -
项目结构设计

------------------------------------------------------------------------

# Phase 1：Agent Core ✅

目标： 完成基础 Agent 框架。

## State 状态管理 ✅

实现 SalesAgentState：

-   goal
-   research_plan
-   messages
-   candidate_leads
-   evidence
-   status

## Planning Agent ✅

功能： 将用户销售目标转换为研究计划。

输出： - 搜索方向 - 购买信号 - 研究维度 - 搜索关键词

## Executor Agent ✅

实现：

用户目标 → LLM推理 → Tool Calling → 工具执行 → 结果反馈

## Tool Calling ✅

已实现：

-   search_companies
-   search_company_news
-   search_company_jobs

## LangGraph Workflow ✅

流程：

START → Planner → Executor → Tools → Executor → Review → END

## Review Agent ✅

输出：

-   company
-   purchase_intent_score
-   opportunity_level
-   evidence
-   recommended_action

------------------------------------------------------------------------

# Phase 2：企业数据与 Memory ✅（增强完成）

目标： 让 Agent 从一次性搜索升级为长期销售知识系统。

## Lead Database ✅

技术：

SQLite + SQLAlchemy

字段：

-   company
-   industry
-   region
-   score
-   level
-   evidence
-   action
-   stage
-   next_action
-   owner
-   status

## Agent Memory ✅

实现：

memory_retrieval_node

流程：

Agent启动 → 查询CRM → 获取历史客户 → Executor结合历史信息决策

## Lead评分系统 ✅

实现：

-   purchase_intent_score
-   opportunity_level

## Lead去重更新 ✅

能力：

已有企业： - 更新记录

新企业： - 新增记录

## Lead批量入库 ✅

流程：

Review → candidate_leads → Memory Node → Database

## Lead Lifecycle Management ✅

状态：

new → contacted → qualified → meeting → proposal → closed

## Follow-up Agent ✅

自动生成：

-   联系动作
-   技术方案准备
-   后续跟进计划

------------------------------------------------------------------------

# Phase 3：MCP 工具化 ⏳ 下一阶段

目标：

将当前 Python Tool 升级为 MCP 标准工具。

计划：

## Company MCP Server

封装：

-   企业搜索
-   新闻查询
-   招聘查询

## CRM MCP Server

封装：

-   查询客户
-   更新状态
-   新增客户
-   查询跟进记录

## MCP Client 接入

实现：

Agent动态发现并调用工具。

------------------------------------------------------------------------

# Phase 4：RAG 企业知识库 ⏳

目标：

让 Agent 具备企业内部知识。

数据：

-   产品资料
-   技术方案
-   行业案例
-   报价文件

流程：

Document → Embedding → Vector Database → Retriever → Agent

------------------------------------------------------------------------

# Phase 5：Multi-Agent ⏳

目标：

从单 Agent 升级多 Agent。

架构：

Supervisor Agent

├── Research Agent

├── Analysis Agent

├── Sales Agent

└── CRM Agent

------------------------------------------------------------------------

# 当前项目状态

完成：

Phase 0 ✅

Phase 1 ✅

Phase 2 ✅（增强完成）

下一阶段：

Phase 3：MCP 工具化

最终目标：

企业搜索 → 智能分析 → CRM记忆 → 销售跟进 → RAG知识增强 → Multi-Agent协作

形成完整企业级 AI Sales Agent 系统。
