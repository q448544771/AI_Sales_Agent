# AI Sales Agent 项目进度记录

## Phase 2：Agent执行能力增强与Lead CRM记忆系统建设

时间：2026-09-23

状态：✅ 已完成

---

# 1. Phase 2目标

Phase 1完成了：
- Agent基础架构搭建
- LangGraph工作流设计
- Planner / Executor / Reviewer节点实现
- Tool Calling机制验证
- 基础销售线索分析流程

Phase 2目标：

1. Lead结构化输出
2. 企业销售线索持久化存储
3. Lead去重与更新
4. CRM Memory能力
5. 多客户批量管理

最终构建：

任务规划
↓
自主执行
↓
工具调用
↓
客户分析
↓
CRM记忆
↓
持续优化

的企业级AI销售Agent基础系统。

---

# 2. Phase 2整体架构

```
用户需求
    ↓
Planner Node
    ↓
Executor Node
    ↓
Tool Calling Layer
    ↓
Reviewer Node
    ↓
Memory Node
    ↓
SQLite CRM Database
```

---

# 3. 已完成模块

## 3.1 Lead结构化模型

统一Lead格式：

```json
{
 "company":"",
 "purchase_intent_score":0.0,
 "opportunity_level":"",
 "evidence":[],
 "recommended_action":""
}
```

状态：

✅ 完成


---

## 3.2 Reviewer多Lead评估能力

优化前：

企业信息 → Reviewer → 单个Lead

问题：
- 无法形成客户池
- 只能保存一个客户


优化后：

企业调查结果
↓
Reviewer
↓
多个Lead列表
↓
Memory批量保存


状态：

✅ 完成


---

## 3.3 SQLite CRM数据库

新增：

```
leads
```

字段：

|字段|说明|
|-|-|
|id|客户编号|
|company|企业名称|
|industry|行业|
|region|地区|
|score|购买意向评分|
|level|机会等级|
|evidence|购买信号|
|action|销售建议|
|status|客户状态|

状态：

✅ 完成


---

## 3.4 Memory Node

新增：

```
app/agent/memory.py
```

功能：

### Lead查询

判断数据库是否存在客户。


### Lead去重

通过：

```python
company == existing.company
```

判断重复。


### Lead更新

更新：

- score
- evidence
- action
- status


状态：

✅ 完成


---

## 3.5 LangGraph流程升级

原流程：

```
Planner
 ↓
Executor
 ↓
Review
 ↓
END
```


升级：

```
Planner
 ↓
Executor
 ↓
Review
 ↓
Memory
 ↓
Database
 ↓
END
```


状态：

✅ 完成


---

# 4. Phase 2测试结果

运行：

```bash
python test_graph.py
```

Reviewer成功发现：

```
2个潜在客户
```


## 客户1

华东精密汽车零部件有限公司

购买信号：

- 新能源零部件扩产
- 投资5亿元建设生产基地
- 新增两条自动化生产线
- 招聘机器视觉工程师


评分：

```
0.95
```


## 客户2

中部汽车结构件制造有限公司

购买信号：

- 新建生产基地
- 新工厂投产
- 质量检测能力升级


评分：

```
0.72
```


---

# 5. 数据库存储验证

## 已存在客户

华东精密汽车零部件有限公司

执行：

```
UPDATE
```

状态：

```
updated
```


## 新客户

中部汽车结构件制造有限公司

执行：

```
INSERT
```

状态：

```
new
```

---

# 6. Phase 2完成能力

Agent已经具备：

## 自主研究能力

- 制定销售研究计划
- 调用企业工具
- 分析企业需求


## 销售判断能力

分析：

- 扩产信号
- 自动化升级
- 招聘信息
- 质量升级需求


输出：

- 购买意向评分
- 销售行动建议


## CRM记忆能力

实现：

```
第一次：
发现客户
↓
保存数据库

第二次：
查询历史客户
↓
更新判断
```

---

# 7. 当前系统能力

|能力|状态|
|-|-|
|Agent规划|✅|
|自主执行|✅|
|Tool Calling|✅|
|企业搜索|✅|
|新闻分析|✅|
|招聘分析|✅|
|Lead评分|✅|
|Lead结构化|✅|
|数据库存储|✅|
|Lead去重|✅|
|Lead更新|✅|
|批量入库|✅|

---

# 8. 当前不足

## 数据源有限

当前：

```
search_companies()
```

仍为模拟数据。


后续接入：

- 企业数据库
- 搜索API
- 招聘数据
- 新闻API


## Lead数量不足

目标：

3个客户

当前：

2个客户


原因：

候选企业池不足。


## Memory能力较基础

当前：

保存 + 更新


下一步：

历史召回 + 上下文增强 + 再决策


---

# 9. Phase 3规划

## Agent长期记忆与真实企业数据接入


目标：

从：

```
销售线索收集工具
```

升级为：

```
企业销售智能助手
```


主要任务：

## Phase 3.1 CRM查询能力

新增：

```
query_leads()
```

支持：

- 查询历史客户
- 查询高价值客户
- 查询待跟进客户


## Phase 3.2 Agent Memory召回

流程：

```
用户输入
↓
查询CRM
↓
结合历史信息
↓
重新规划任务
```


## Phase 3.3 数据源扩展

替换模拟：

```
search_companies()
```

接入：

- 企业搜索接口
- 新闻搜索
- 招聘数据


## Phase 3.4 MCP协议改造

目标：

```
Agent
 ↓
MCP Server
 ↓
CRM Database/API
```

实现企业级Agent标准架构。


---

# Phase 2总结

Phase 2完成了AI Sales Agent从：

```
会思考的Agent
```

升级到：

```
会执行
+
会分析
+
会保存客户经验
```

的企业销售Agent基础版本。

下一阶段：

让Agent拥有真正的长期记忆和企业数据能力。
