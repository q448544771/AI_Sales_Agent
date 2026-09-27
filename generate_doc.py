import os
import docx
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def create_interview_doc():
    doc = Document()

    # 页面边距设置
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # 主标题
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title.add_run("大模型 AI Agent 应用工程师高频面试 100 问与深度解析")
    run_title.font.name = "微软雅黑"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(31, 78, 121)

    # 副标题
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = subtitle.add_run("—— 工业级落地、LangGraph、MCP、RAG 与系统架构全景指南\n")
    run_sub.font.name = "微软雅黑"
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(112, 128, 144)

    # 100 道题目与回答的数据集
    qa_data = [
        # 一、核心概念与架构
        ("第一部分：Agent 基础概念与核心架构", [
            ("Q1: 什么是 AI Agent？它与传统的 LLM（大语言模型）对话有何本质区别？",
             "传统 LLM 是无状态、被动的文本补全系统（Text-in, Text-out），缺乏感知与修改物理/数字世界的能力。\n"
             "AI Agent 是以 LLM 作为核心认知决策引擎（大脑），结合规划（Planning）、记忆（Memory）、工具使用（Tools）和环境感知反馈构成的自主闭环系统。Agent 能自主拆解复杂目标、感知环境变化、调用外部 API，并依据反馈自我迭代直至完成目标。"),
            ("Q2: 经典 Agent 的核心四大支柱是什么？",
             "1. Brain（认知核心/LLM）：负责意图理解、逻辑推理、决策与任务调度。\n"
             "2. Planning（规划能力）：包含子目标拆解、反思（Reflection）、自错纠错与路径回溯。\n"
             "3. Memory（记忆机制）：短期工作记忆（Context Window）与长期持久化记忆（向量检索/实体图谱/数据库）。\n"
             "4. Tools/Action（行动与工具）：连接外部数字世界的接口（代码解释器、搜索引擎、数据库、RESTful API、MCP）。"),
            ("Q3: 什么是 ReAct 架构？其基本流转逻辑是什么？",
             "ReAct 即 Reasoning（思考）+ Acting（行动）。\n"
             "其核心流程为：Thought -> Action -> Observation 循环：\n"
             "- Thought：模型根据目标和历史观察，生成内心独白，分析“下一步该做什么”；\n"
             "- Action：若需外部输入，输出具体工具名称及传参；\n"
             "- Observation：环境执行该工具后将返回值喂回给模型；\n"
             "- 循环往复，直至模型认为信息充分，输出 Final Answer。"),
            ("Q4: 什么是 Plan-and-Solve（计划后执行）策略？它与 ReAct 相比优缺点是什么？",
             "机制：先由 Planner 一次性把复杂目标拆解成静态的多步步骤列表；再由 Executor 按顺序调用工具执行。\n"
             "优点：针对复杂宏观任务全局视野好，单步推理 Token 消耗低，主干流程稳定。\n"
             "缺点：缺乏动态自适应能力。若前置步骤报错，静态计划无法自适应修改，必须引入 Replanner 动态重构计划。"),
            ("Q5: 请对比 OpenAI Assistants API、LangChain、LangGraph 和 AutoGen。",
             "- OpenAI Assistants API：全托管黑盒方案，包含线程、代码沙箱和内置检索，开发极快但定制性差、平台深度绑定。\n"
             "- LangChain：经典链式封装，生态庞大，但在处理循环（Loop）、复杂条件分支与状态回滚时抽象较死板。\n"
             "- LangGraph：将控制流抽象为有向状态图（StateGraph），把节点（Nodes）、条件边（Edges）和全局状态（State）解耦，原生支持循环、人机协同（Human-in-the-loop）、断点续跑和复杂多 Agent，是工业级生产首选。\n"
             "- AutoGen：微软主导的多 Agent 对话协作框架，偏重 Agent 间的群聊与博弈，适合开放式生成与演练，在严格受控的企业业务中可控性偏弱。"),
            ("Q6: 为什么生产环境中不能单纯依赖无约束的 LLM 自主决策？",
             "无约束的 Agent 容易陷入死循环、幻觉臆造参数、不可预测的高额 Token 账单以及意外执行破坏性操作（如误删生产数据）。工业级系统必须通过状态机、强类型 Schema 契约、熔断阈值和人工确认节点加以边界限制。"),
            ("Q7: 什么是 Human-in-the-Loop（人机协同）？在什么阶段必须引入？",
             "指在 Agent 自动化流转的特定节点设置断点，暂停系统等待人工确认、修改参数或补充信息后再继续执行。\n"
             "必须引入阶段：高风险操作（金融转账、向 CRM 录入合同、批量对外发送商务邮件、执行不可逆的数据库变更）。"),
            ("Q8: 什么是 Agent 的“确定性（Deterministic）”与“非确定性（Probabilistic）”平衡？",
             "业务规则、数据鉴权、核心逻辑分支由确定性代码（Python / LangGraph 条件边）固定；而模糊意图提取、跨模态理解、长文本归纳和个性化润色交由 LLM 处理，实现兼具可靠性与智能性的系统。"),
            ("Q9: 什么是 Reflexion（反思机制）？",
             "Reflexion 在动作反馈后引入评判者（Evaluator）或自我反思步骤。如果任务执行失败，系统不直接退出，而是由 Agent 基于错误日志反思原因，将反思内容加入上下文后重新尝试生成新的 Action。"),
            ("Q10: 什么是 Tree of Thoughts（思维树，ToT）？它在 Agent 规划中怎么用？",
             "将线性的思维链（CoT）扩展为树状结构，Agent 在每一步可以探索多种解决思路，结合启发式评估（评判各分支可行性），配合广度优先（BFS）或深度优先（DFS）搜索，支持路径回溯（Backtracking）与剪枝。"),
            ("Q11: 什么是 Function Calling（工具调用）？底层的通信协议是什么格式？",
             "模型在训练阶段强化学习了特定格式输出能力。开发者在请求时传入 Tools 的 JSON Schema 定义；模型判定需要调工具时，不再输出自然语言，而是返回严格包含 tool_name 和 arguments 的 JSON 结构体；客户端解析并执行真实代码后，再把结果以 tool 角色返回给模型。"),
            ("Q12: 智能体应用中“状态（State）”的定义原则是什么？",
             "1. 精简性：只保留对后续推理、UI 渲染或日志追踪必须的关键字段；\n"
             "2. 不可变与可追加（Append-only）：对消息队列通常使用追加合并模式（Reducers），便于回溯历史；\n"
             "3. 类型安全：使用 TypedDict 或 Pydantic BaseModel 强类型约束，防止因 Key 缺失导致下游节点崩溃。"),
        ]),
        # 二、提示词工程与结构化输出
        ("第二部分：提示词工程与结构化输出", [
            ("Q13: 如何保证大模型输出绝对合规的 JSON，避免因格式损坏导致代码异常？",
             "1. 启用底层厂商提供的 JSON Mode / Structured Outputs；\n"
             "2. 使用 Pydantic 定义输出数据类，结合 LangChain 的 PydanticOutputParser；\n"
             "3. 在 System Prompt 中提供输出 Schema 定义及 1~2 个真实的 Few-shot 样例；\n"
             "4. 引入重试纠错层（如 OutputFixingParser），捕获解析异常时将错误信息喂给模型二次校正。"),
            ("Q14: 什么是 System Prompt 中的“角色扮演（Persona）”与“负向约束（Negative Constraints）”？",
             "Persona 设定 Agent 的行业专家定位、语调、职责边界，使其激活该领域垂直语义分布；\n"
             "负向约束明确禁止 Agent 做的事（例如“严禁臆造数据出处”、“严禁在未确认证据前打分”）。负向约束应具体、可量化，避免抽象词汇。"),
            ("Q15: Few-Shot（少样本学习）在构建垂直领域 Agent 时的关键细节是什么？",
             "样例必须真实反映边际情况（Edge Cases）；样例中的思考过程需严谨展示中间工具调用的传参风格；若上下文窗口紧张，应利用 Embedding 向量检索动态召回与当前 Query 最相似的 2~3 个 Few-shot 样例注入 Prompt。"),
            ("Q16: 当 System Prompt 过长（如超过 3000 字），模型出现“指令丢失”怎么办？",
             "1. 分层提示词：拆散长 Prompt，分配给不同专职子 Agent；\n"
             "2. 利用首尾效应：大模型对 Prompt 开头和结尾注意力权重最高，将最核心的禁令和格式约束放在末尾；\n"
             "3. 结构化排版：使用 Markdown 标题、XML 标签建立清晰的信息层级。"),
            ("Q17: 什么是 Chain-of-Thought（思维链，CoT）？它对 Agent 决策的利弊分别是什么？",
             "利：引导模型逐步推导，显著提升逻辑运算、复杂依赖判断和参数填写的准确率。\n"
             "弊：增加首字延迟（TTFT）与端到端响应时间；消耗更多的 Output Tokens；若缺乏结构化提取，容易污染最终返回给用户的文本。"),
            ("Q18: 为什么现代 Agent 架构中主张将“思考过程”与“最终输出”严格解耦？",
             "工业级系统通常需要将思考日志存入审计追踪系统，而用户前端 UI 只需洁净结果；同时分离思考与输出可以避免内部 Prompt 泄露与商业机密外溢，并方便利用 Pydantic 针对纯输出结果进行单一校验。"),
            ("Q19: 如何防范 Prompt Injection（提示词注入攻击）？",
             "1. 输入隔离：将用户输入包裹在特定 XML 标签中（如 ...），声明该内容仅为参考，不得覆盖系统规则；\n"
             "2. 双模型前置检测：设立轻量守门模型（Guardrail Model）进行毒性与越狱识别；\n"
             "3. 工具鉴权隔离：敏感操作严格由后台鉴权拦截，不轻信 Agent 的调用意图。"),
            ("Q20: 什么是 Self-Consistency（自洽性采样）？适合用在 Agent 的哪类环节？",
             "以较高 Temperature 多次采样模型的推理路径，通过多数投票（Majority Vote）或聚类选出出现频次最高的一致性结果。\n"
             "适用场景：离线线索评级、金融风控审核、敏感数据清洗等注重极高准确率但容忍较高延迟的非实时场景。"),
            ("Q21: 什么是 Markdown Prompting 中的 XML 隔离规范？",
             "使用 XML 标签清晰划分上下文（如 、、、）。模型在预训练和微调中高度适应了 XML 结构的边界识别，能大幅降低因用户指令与系统指令混淆带来的歧义。"),
            ("Q22: 如何动态组装 Prompt（Dynamic Prompt Engineering）？",
             "不把所有规则写死在单一大文本中，而是依据运行时状态（如当前用户等级、已绑定的数据源类型、上一轮执行报错信息）从 Prompt 库中拼接子模块，按需插入模板。"),
            ("Q23: 什么是 Prompt Caching（提示词缓存）？它如何降低 Agent 成本？",
             "当请求的前缀（Prefix）完全一致且达到一定长度时，服务器重用已计算好的 KV Cache，读取成本仅为常规输入价格的 10%~50%，且显著降低首字延迟。\n"
             "工程设计要求：必须将静态不变的 System Prompt、工具定义、Few-shot 放置在请求最前端，动态用户输入置于尾部。"),
            ("Q24: 如果模型总是漏填某一个 Tool 参数，Prompt 层面该如何精准纠正？",
             "在 Tool 的 JSON Schema description 属性中详细阐述该字段的含义和推导方法；并在 Schema 的 required 列表中显式包含该字段；同时在 Prompt 中提供反面与正面样例对比。"),
        ]),
        # 三、规划、推理与控制流
        ("第三部分：任务规划、推理与控制流", [
            ("Q25: LangGraph 中的 Node（节点）与 Edge（边）各代表什么含义？",
             "Node（节点）：通常是一个纯 Python 函数，负责接收当前全局 State，执行特定业务（调模型、调工具），并返回字典增量更新 State。\n"
             "Edge（边）：定义状态从一个节点流向下一个节点的路由路径，包含固定单向边和基于状态动态判定的条件边（Conditional Edge）。"),
            ("Q26: 什么是 Conditional Edges（条件边）？写一个简单的路由逻辑。",
             "条件边根据当前节点执行结果中的字段，动态计算下一个目的节点。\n"
             "示例：\n"
             "def route(state):\n"
             "    if state.get('error_count', 0) > 3: return 'human_fallback'\n"
             "    if state.get('has_tool_call'): return 'executor'\n"
             "    return 'reviewer'"),
            ("Q27: 如何处理 Agent 运行过程中的“无限死循环”？",
             "1. 硬性步数截断：State 中维护 step_count，设置最大步数（如 10 步）超时强制熔断；\n"
             "2. 重复动作检测：维护最近动作哈希队列，若连续调用同一工具传参相同则拦截；\n"
             "3. 模型参数抑制：提高重复惩罚（Frequency Penalty）。"),
            ("Q28: 什么是 Hierarchical Planning（分层规划）？",
             "设立 Supervisor Agent 负责宏观战略制定、进度考核与资源分配；各 Worker Agent 专注于垂直领域的深度执行（搜索、计算、报告渲染），Worker 完成后向 Supervisor 汇总成果。"),
            ("Q29: 为什么在生产工作流中，更推崇“DAG 状态机”而不是完全自主的“ReAct”？",
             "ReAct 完全依赖大模型不可预知的单步采样，难以向业务方保证 SLA 和逻辑确定性；DAG 状态机限定了合法的业务流转状态，将主干确定性流程固化，仅在局部复杂决策点借助 LLM 智能。"),
            ("Q30: 什么是 Memory-augmented Planning（记忆增强规划）？",
             "Agent 在制定计划前，先利用当前任务特征向量，在以往“成功解决相似问题的执行历史库”中检索相似案例，直接复用既往成功 Plan 骨架，减少重复试错。"),
            ("Q31: 如果 Executor 执行某工具抛出 500 网络超时，Agent 控制流应如何应对？",
             "1. 工具内部先进行 3 次指数退避重试；\n"
             "2. 若重试失败，将清洗后的错误摘要写入 State 的 Observation；\n"
             "3. 控制流路由回 Planner，让模型感知依赖不可用，进而调整策略调用备用工具或告知用户。"),
            ("Q32: 什么是 State Reducer（状态还原器）？在 LangGraph 中有什么用？",
             "用于定义新旧 State 字段如何合并的规则函数。例如默认字典合并是直接覆盖，但聊天记录 messages: Annotated[list, add_messages] 的 Reducer 能保证新消息追加到列表尾部而不清空旧消息。"),
            ("Q33: 如何实现任务中断（Interrupt）与断点续跑（Checkpointing）？",
             "利用 LangGraph 的 Checkpointer（如 SqliteSaver）将每一步执行后的 State 快照序列化保存。\n"
             "需要人工介入时触发 interrupt()；人工审核完成后，传入对应的 thread_id 即可加载原快照无损恢复执行。"),
            ("Q34: 什么是 Subgraph（子图）架构？它解决了什么工程难题？",
             "将复杂模块拆解为独立的自闭环小图（如独立知识库检索子图），在主图中以普通节点形式挂载。\n"
             "解决的问题：解耦巨型系统的复杂度，实现团队分工协作与局部状态隔离，便于独立进行单元测试。"),
            ("Q35: 什么是 Least-to-Most Prompting？它与 CoT 有何区别？",
             "CoT 是单步直接输出整个推导链；Least-to-Most 是由浅入深推进：先将大问题分解为若干相互依赖的子问题列表，串行执行，前一个子问题的答案作为后一个子问题的输入。"),
            ("Q36: 规划模型与轻量执行模型混合搭配的成本优化策略是什么？",
             "使用高推理能力模型（如 Claude 3.5 Sonnet / DeepSeek-R1 / GPT-4o）作为 Planner 和 Reviewer 制定宏观策略；局部参数填充、简单工具执行由高速廉价模型（如 GPT-4o-mini / GLM-4-Air）负责，可节省 70% 以上 API 成本。"),
        ]),
        # 四、记忆机制与上下文工程
        ("第四部分：记忆机制与上下文工程", [
            ("Q37: Agent 体系中短期记忆与长期记忆的物理实现分别是什么？",
             "短期记忆：当前会话进程中的上下文窗口，保存在内存、Redis 缓存或临时会话表中。\n"
             "长期记忆：持久化保存在向量数据库（Chroma/Milvus）、图数据库（Neo4j）或关系型数据库中，沉淀跨会话、跨天的用户信息、业务偏好和操作记录。"),
            ("Q38: 当多轮对话历史超出上下文窗口时，有哪些主流剪裁策略？",
             "1. 滑动窗口（Sliding Window）：保留最近 N 轮对话，丢弃最早历史；\n"
             "2. 会话总结归纳（Summarization）：当消息达到阈值，触发轻量 LLM 归纳旧消息为简短 Summary 替换旧历史；\n"
             "3. 分层记忆保留：保留最初 1~2 轮（用户意图原点）+ 提取的实体事实字典 + 最近 3 轮完整对话。"),
            ("Q39: 什么是 Semantic Memory（语义记忆）与 Episodic Memory（情景记忆）？",
             "语义记忆：事实性、概念性知识（如“客户公司主营高精度铝压铸，使用的是三菱 PLC”）；\n"
             "情景记忆：按时间顺序记录特定历史经历（如“上周二我们向该客户推介过轮毂表面质检方案，客户反馈预算超标”），带有明确时间戳和因果关系。"),
            ("Q40: 为什么直接把历史消息一次性全部向量化检索往往效果不佳？",
             "对话片段（“好的”、“没问题”、“刚才说的那个”）高度依赖上下文代词，语义极度稀疏，单句 Embedding 丢失前因后果。应先通过大模型提取结构化事实断言（Declarative Facts），再对断言进行向量化入库。"),
            ("Q41: 如何从非结构化对话中自动提取用户画像与长期偏好？",
             "后台采用异步流水线或单独的 Memory Updater 节点，输入最新一轮交互，使用预定义的 Pydantic Schema（行业、痛点、预算、已拒绝项）提取结构化 JSON，与数据库已有画像进行对比合并（Upsert/Deduplication）。"),
            ("Q42: 什么是 Lost in the Middle（中间迷失）现象？在设计 Agent 上下文时如何规避？",
             "大模型对处于上下文最前端和最尾端的信息注意力最强，对超长文档中央区域的信息提取能力显著退化。\n"
             "规避策略：将关键任务指令、负向约束置于最尾部；在检索 RAG 片段后，将相关度得分最高的证据放在首尾两端，而非堆放在正中央。"),
            ("Q43: 记忆机制中的 Memory Decay（遗忘机制）如何用数学或工程实现？",
             "结合时间衰减因子与访问频率计算保留权重：Score = Similarity * exp(-λ * Δt) + α * AccessCount。\n"
             "冷门、久远的记忆权重自然下降，防止无意义历史长期占据上下文。"),
            ("Q44: 什么是 Entity Memory（实体记忆）？其适用场景是什么？",
             "专门以现实中的实体（公司、联系人、产品型号）为 Key 构建的字典或图谱。\n"
             "适用场景：CRM 销售管理、复杂客服系统。无论用户跨越多少轮对话，只要提到“某客户公司”，即可精确提取对应公司名下的固定属性。"),
            ("Q45: 如何保障写入长期记忆的数据隐私与安全？",
             "1. 前置脱敏：在持久化向量或数据库前，使用正则或识别模型将手机号、身份证号、银行卡等 PII 敏感信息进行掩码处理；\n"
             "2. 租户隔离：在向量检索与数据库查询时，强制将 tenant_id 作为硬过滤条件（Metadata Filter），防止跨租户信息越权。"),
            ("Q46: LangChain 的 add_messages 机制底层是如何处理不同消息角色的？",
             "识别 AIMessage、HumanMessage、SystemMessage、ToolMessage；每条消息带有唯一 id，接收到相同 id 则覆写（Update），不同 id 则追加；针对带有 tool_calls 的 AIMessage，严格追踪其对应的 tool_call_id 是否被随后的 ToolMessage 闭环回复。"),
            ("Q47: 什么是 Context Compression（上下文压缩）？",
             "召回多篇文档或历史记录后，不把几万字全喂给大模型，而是先利用微型模型或规则滤除停用词与无关段落，仅抽取与当前提问强相关的关键词句重新拼接，以高信噪比注入上下文。"),
            ("Q48: 长期记忆存储中，向量数据库和关系型数据库如何协同？",
             "关系型数据库存储主数据实体与状态（确凿无误、需要 ACID 事务支持的属性，如用户金额、工单状态）；向量数据库存储语义索引与经验沉淀（非结构化的对话片段、工单复盘记录），通过关联外键 entity_id 实现混合检索。"),
        ]),
        # 五、工具调用与 MCP 生态
        ("第五部分：工具调用与 MCP（Model Context Protocol）生态", [
            ("Q49: 什么是 MCP（Model Context Protocol）？它解决了什么痛点？",
             "MCP 是由 Anthropic 主导提出的开放标准协议，旨在标准化大语言模型与外部数据源及工具之间的通信。\n"
             "痛点：以往各框架（LangChain, LlamaIndex, AutoGen）有各自私有 Tool 封装语法，导致重复造轮子。MCP 统一了客户端与服务端标准，如同智能体领域的“USB 接口”。"),
            ("Q50: MCP 的架构由哪三层主要角色组成？",
             "1. MCP Host：发起调用的主程序（如 Claude Desktop、自定义 Python Agent）；\n"
             "2. MCP Client：运行在 Host 内部的协议客户端，负责与具体的 Server 建立通信并交换 JSON-RPC 请求；\n"
             "3. MCP Server：独立的轻量级进程，提供标准化的上下文资源（Resources）、提示模板（Prompts）以及可执行工具（Tools）。"),
            ("Q51: MCP 支持的三大核心原语（Primitives）是什么？",
             "1. Resources（资源）：只读的数据源（类似文件读取，提供静态上下文，支持动态订阅更新）；\n"
             "2. Prompts（提示词模版）：由服务端预先配置好的交互提示词工程模板；\n"
             "3. Tools（工具）：具有副作用（Side-effects）的可执行函数，支持客户端通过模型决策发起调用并获取结果。"),
            ("Q52: MCP Client 与 MCP Server 之间通常采用什么底层传输方式？",
             "1. Stdio（标准输入输出）：适用于本地进程间通信（IPC）。Server 作为子进程拉起，通过 stdin/stdout 传输 JSON-RPC 消息，速度快、安全隔离；\n"
             "2. SSE（Server-Sent Events / HTTP）：适用于跨网络分布式场景，Server 部署在远程服务器上，通过 HTTP POST 提交调用，通过 SSE 接收长连接事件。"),
            ("Q53: 在将 MCP 工具桥接到自主 Agent 时，Adapter（适配器）需要完成哪些转换？",
             "异步列出 MCP Server 的 tools 列表；读取每个工具的 JSON-RPC 参数描述，解析其 JSON Schema 映射成 LangChain 的 StructuredTool 或动态构造 Pydantic 参数校验模型；实现异步执行与错误重定向。"),
            ("Q54: 工具调用时遇到网络抖动或超时，如何在代码层面设计健壮的防御？",
             "1. Timeout 限制：每个工具函数硬编码超时上限（如 10 秒），防止子进程或远端 HTTP 请求挂死；\n"
             "2. 熔断器机制（Circuit Breaker）：连续多次失败触发熔断降级；\n"
             "3. 异常安全拦截：工具函数内部严禁裸抛异常，统一包装为 {'status': 'error', 'message': '...'} 返回字典供模型反思。"),
            ("Q55: 什么是“自描述工具（Self-describing Tools）”？",
             "工具的名称（Name）、简介（Description）以及入参（Parameters）被赋予详尽的业务语义。大模型完全不依赖外部硬编码规则，仅通过读取工具的 docstring 和 schema 就能精准推断出该工具的适用边界、限制条件和期望传参格式。"),
            ("Q56: 工具定义过多（如超过 30 个）导致大模型选择失准、Token 浪费怎么办？",
             "1. 动态工具检索：将 30 个工具的说明向量化，每轮先根据 Query 向量检索出最相关的 Top-5 工具挂载进 Prompt；\n"
             "2. 二级路由分发：设计顶层 Master Router 仅负责将任务指派给子部门，各子组拥有局部的 5~6 个专用工具。"),
            ("Q57: 为什么工具执行应当遵循“幂等性（Idempotency）”设计？",
             "Agent 具有自我修正与重试特性。如果网络中断或模型因为格式问题进行了二次尝试，非幂等操作（如扣减积分）会导致重复操作灾难。必须引入业务唯一幂等键（Idempotency Key）确保多次调用结果一致。"),
            ("Q58: 怎样在 Agent 中安全地运行大模型生成的 Python 代码？",
             "严禁在宿主机直接 exec() 或 eval()。采用容器化隔离（Docker 临时无网络容器）、WebAssembly 沙箱或专用云端代码沙箱 API（如 E2B），设定严格的 CPU/内存配额和超时限制。"),
            ("Q59: 什么是 Tool Augmentation 与 Tool Synthesis？",
             "Tool Augmentation：增强工具返回值的信息密度（自动补充数据更新时间、数据来源置信度等元数据）；\n"
             "Tool Synthesis：当发现无现成工具时，Agent 自动编写一段代码完成新功能，并注册为新工具供后续重复使用。"),
            ("Q60: 如何测试一个 Agent 工具调用的单元测试覆盖率？",
             "不调用真模型，直接对模型输出的 Tool Call Payload 进行 Mock；测试底层参数 Pydantic 解析是否健壮；测试边界输入条件；测试异常链路（Mock 远端抛出 404/500/Timeout 时工具是否返回规范错误字典）。"),
        ]),
        # 六、多智能体协同架构
        ("第六部分：多智能体（Multi-Agent）协同架构", [
            ("Q61: 单智能体与多智能体系统（MAS）的权衡点是什么？",
             "单 Agent：架构简洁、延迟低、易调试；但在跨角色复杂业务中单模型注意力分散、提示词臃肿；\n"
             "多 Agent：角色职责单一解耦、上下文干净；缺点是系统复杂度高，通信 Token 消耗大，存在互相推诿或串通妥协风险。"),
            ("Q62: 多智能体协同的常见组织拓扑结构有哪些？",
             "1. 层级主管制（Supervisor）：总管负责拆解分派任务并收束结果；\n"
             "2. 流水线链式（Sequential Pipeline）：上一节点输出是下一节点输入；\n"
             "3. 竞技辩论模式（Debate）：多个 Agent 正反方辩驳，法官裁决；\n"
             "4. 共享黑板模式（Blackboard）：所有 Agent 围绕公共状态池读写各自负责的信息片段。"),
            ("Q63: 什么是“多智能体辩论（Multi-Agent Debate）”？它如何抑制模型幻觉？",
             "让多个独立的 Agent 针对同一问题给出推导，将对方的推理作为下一轮输入要求其寻找漏洞并自辩。竞争与交叉质疑能让模型互相纠错，显著降低单模型的盲区与幻觉。"),
            ("Q64: 如何避免多智能体之间陷入“无限无意义讨论”？",
             "引入显式收敛协议：1. 限制最大交互轮数（如最多 3 轮）；2. 引入拥有终审裁定权的独立判官（Judge）；3. 规定结束信号（达成共识或特定 TERMINATE 标记）。"),
            ("Q65: 多智能体通信的有效机制是基于自然语言还是结构化协议？",
             "实验探索可用自然语言；生产工程中强推结构化协议（JSON/Pydantic）。每个 Agent 返回必须包含固定键（verdict, critique, revised_data 等），以便下游程序可靠解析和控制流条件跳转。"),
            ("Q66: 什么是 Dynamic Agent Allocation（动态智能体分配）？",
             "运行时不预先启动所有专家智能体。主控 Agent 根据任务复杂度，从注册表中按需实例化特定专家（如仅在涉及合规纠纷时才动态初始化 LegalAgent 接入网络）。"),
            ("Q67: 多 Agent 之间如何共享环境状态？",
             "采用中央集中式 State（如 LangGraph StateGraph）。每个 Agent 节点作为 Pure Function 接收只读 State 副本，计算完后仅返回增量变更的 Delta Payload，由框架的全局 Reducer 统一合并，避免并发冲突。"),
            ("Q68: 什么是 Multi-Agent 中的 Role-Playing Alignment（角色对齐）？",
             "为每个智能体注入严格正交的职责边界，明确其“不能做什么”。例如 SecurityAgent 专注于挖漏洞，绝不能越权执行业务；WriterAgent 专注于文字润色，不能擅自修改核心业务数据。"),
            ("Q69: 面对海量并发请求，多智能体系统在工程上如何防止 API 速率受限（429）？",
             "1. 建立底层全局异步任务队列（Celery / RabbitMQ）；\n"
             "2. 在统一 LLM Client 层实现令牌桶（Token Bucket）算法进行流量整形；\n"
             "3. 配置自动化故障转移与多提供商 Fallback（如 OpenAI 限流时平滑路由到 Azure OpenAI 备用渠道）。"),
            ("Q70: 为什么多 Agent 系统比单 Agent 系统需要更加严格的可观测性？",
             "多 Agent 链路长、网状交织，单点故障极难定位。若没有分布式链路追踪，无法定位错误究竟是由上游传递了脏数据、中游解析失败，还是下游产生了幻觉。"),
            ("Q71: 什么是 Agent 的“群智涌现”？在工业落地中应注意什么？",
             "大量轻量智能体通过局部互动在宏观上表现出解决复杂协同问题的能力。\n"
             "工业注意事项：企业追求高确定性指标，“涌现”意味着不可测和不可控。除仿真演练外，企业常规业务尽量少用自由交互群集。"),
            ("Q72: 如何设计一个带有 Reviewer（审核反思）节点的多 Agent 质量把关循环？",
             "设计两节点环路：Worker -> Reviewer -> (通过 -> END / 未通过 -> Worker)。\n"
             "Reviewer 严格依照质检清单逐项打分，未通过时附带结构化修改建议列表 feedback，Worker 针对性重写，且设置最大循环次数作为兜底。"),
        ]),
        # 七、RAG 与向量知识库整合
        ("第七部分：RAG 与向量知识库深度整合", [
            ("Q73: 传统的 Naive RAG 面临的三大痛点是什么？Agentic RAG 是如何解决的？",
             "Naive RAG 痛点：1. 检索质量不可控（召回垃圾噪声诱发幻觉）；2. 低估复杂意图（单次匹配无法解多跳问题）；3. 缺乏纠错机制（检索不到硬编答案）。\n"
             "Agentic RAG 解法：智能体主动决策，具备查询重写（Query Rewriting）、自适应路由（Routing）、检索结果重排与评估（Re-ranking/Grading）及未召回时的二次发散检索能力。"),
            ("Q74: 什么是 Self-RAG（自我反思检索增强）？其内部关键的四个反思标记是什么？",
             "模型在生成过程中自主插入特殊反思 Token 评估行为：\n"
             "1. [Retrieve]：判断当前句子是否需要检索；\n"
             "2. [IsREL]：检索到的片段是否与问题相关；\n"
             "3. [IsSUP]：生成的内容是否完全由检索文档事实支撑；\n"
             "4. [IsUSE]：生成内容对回答初始问题是否真正有用。"),
            ("Q75: 什么是 Corrective RAG（CRAG，纠错式 RAG）？",
             "在检索与生成之间加入评估检索结果（Document Evaluator）模型：\n"
             "- Correct（相关）：直接送入生成层；\n"
             "- Incorrect（不相关）：丢弃结果，触发 Web Search 扩充外网信源；\n"
             "- Ambiguous（模糊）：融合知识库与网络搜索结果提纯后再送入模型。"),
            ("Q76: 为什么长文本切分（Chunking）时不能机械地按固定字符数粗暴切断？",
             "固定字数容易把连贯的句子、表格行或代码块斩断，导致前后切片语义破损。\n"
             "更优策略：使用 RecursiveCharacterTextSplitter 优先在段落 \n\n 或标点处断开；针对技术文档使用 MarkdownHeaderTextSplitter 按标题层级切分；或使用语义相似度切分（Semantic Chunking）。"),
            ("Q77: 什么是 Chunk Overlap（分块重叠）？它的作用是什么？",
             "相邻两个 Chunk 之间保留一定比例（如 10%~20%，约 50~100 字符）的重合区域。\n"
             "作用：确保切分边缘处的实体词和上下文逻辑不被生硬割裂，保证检索任一相邻切片时都能获取边缘上下文。"),
            ("Q78: 稠密向量检索（Dense）与稀疏关键词检索（BM25）有何本质差异？如何实现混合检索？",
             "Dense（向量）：捕捉深层语义近义词关联，但在专有名词、料号、缩写上容易模糊匹配；\n"
             "BM25（稀疏）：基于词频统计，对精确字面匹配极度敏锐，但无法理解近义词。\n"
             "混合检索：同时执行两路召回，通过 RRF（倒数排名融合算法）或加权归一化分数将两份排行榜进行无量纲重合打分。"),
            ("Q79: 什么是 Re-ranker（交叉重排模型）？为什么向量数据库初筛后必须加重排？",
             "双塔向量模型（Bi-Encoder）为了检索性能将 Query 与 Doc 独立编码，牺牲了深层交叉注意力；\n"
             "Cross-Encoder（如 BGE-Reranker）将 Query + Document 拼接为长文本全量计算 Token 间交叉注意力。\n"
             "工程收益：先用向量库秒级召回 Top-20 粗筛，再用 Cross-Encoder 精准挑出最相关的 Top-3，大幅提升最终信噪比。"),
            ("Q80: 什么是 Parent Document Retriever（父子文档检索器）？它解决什么矛盾？",
             "核心矛盾：切片太小向量表征精准但上下文缺失；切片太大检索召回准确率低。\n"
             "机制：将文档切成极小的小切片（Child Chunk）计算向量建立索引，命中后系统通过外键关联调取完整的父切片（Parent Chunk）输入大模型。"),
            ("Q81: 什么是 Metadata Filtering（元数据过滤）？在企业级知识库中如何应用？",
             "切片入库时附带结构化标签（如 {'department': 'finance', 'year': 2026}）。\n"
             "检索时先通过 SQL 布尔表达式快速剔除不满足条件的数据，再在过滤后的小数据池中进行高维向量计算，既保证权限隔离又缩短检索耗时。"),
            ("Q82: 什么是 Hypothetical Document Embeddings（HyDE，假设性文档嵌入）？",
             "用户问句往往很短且与文档句式差异大；\n"
             "HyDE 让 LLM 先针对提问生成一篇“假设性答案”，再拿这篇假设性文章去向量库检索。因为文章与文章之间的文体特征远比问句与段落接近，召回精度往往大幅提升。"),
            ("Q83: 什么是 Graph RAG（基于知识图谱的检索增强）？它优于传统向量 RAG 的地方在哪？",
             "利用 LLM 从文本提取实体与关系构建知识图谱网络。\n"
             "优势：传统向量检索对全局宏观问题（如归纳某方案演进路线）无能为力；Graph RAG 能够通过图拓扑做多跳遍历（Multi-hop）和社区发现，实现全局宏观理解。"),
            ("Q84: 如何防止 RAG 检索到的过时文档（Outdated Knowledge）污染回答？",
             "1. 切片打上版本号与最后有效时间戳元数据；\n"
             "2. 知识库更新时通过唯一文档 ID 增量淘汰失效切片；\n"
             "3. Prompt 中约束大模型在事实冲突时以最新时间戳版本为准。"),
        ]),
        # 八、评估、可观测性与生产测试
        ("第八部分：评估、可观测性与生产测试", [
            ("Q85: 评估一个生产级 Agent，通常包含哪些关键维度？",
             "1. 任务完成率（Task Success Rate）：目标是否端到端达成；\n"
             "2. 工具调用准确率（Tool Call Precision & Recall）：是否选对工具，入参是否合法；\n"
             "3. 事实准确性（Grounding / Faithfulness）：回答是否忠于材料，有无幻觉；\n"
             "4. 工程性能（Latency & Cost）：单次任务消耗的 Total Tokens 与端到端响应耗时；\n"
             "5. 轨迹效率（Trajectory Efficiency）：是否走了多余的重复步骤。"),
            ("Q86: 什么是 RAGAS 评估框架？它的核心四项指标是什么？",
             "RAGAS 是针对 RAG 与智能体生成的自动化无参考评估标准：\n"
             "1. Faithfulness（真实性）：生成答案中的声明能否在检索上下文找到依据；\n"
             "2. Answer Relevance（答案相关性）：生成结果是否正面回答了问题；\n"
             "3. Context Precision（上下文精确度）：包含答案的切片是否排在靠前位置；\n"
             "4. Context Recall（上下文召回率）：回答所需事实是否被全量召回。"),
            ("Q87: 什么是 LLM-as-a-Judge（以大模型作为裁判）？如何保证裁判的客观性？",
             "使用更高阶模型（如 GPT-4o / Claude 3.5 Sonnet）根据预设细则（Rubric）对待测 Agent 输出打分。\n"
             "客观性保障：提供分级细致的评分标准锚点；提供 Few-shot 样例校准；交换输入顺序（Position Swap）消除位置偏见；强制裁判在打分前先输出推导理由。"),
            ("Q88: 什么是分布式追踪（Tracing）？主流工具有哪些？",
             "将单次用户请求引发的整个调用链路（Prompt -> Tool -> Subgraph -> Reviewer）通过唯一 Trace ID 和 Span ID 串联，记录每一步耗时、输入输出、Token 消耗与堆栈。\n"
             "主流工具：LangSmith、Langfuse、Arize Phoenix、OpenTelemetry。"),
            ("Q89: 面对 Agent 的非确定性，如何构建高覆盖率的自动化 CI/CD 回归测试集？",
             "构建包含 100~500 个典型案例与历史 Bad Case 的黄金基准测试集（Golden Dataset）；在 GitHub Actions / CI 流水线中跑批；固定 Temperature=0；结合单元测试断言与综合语义通过率阈值（如得分 > 92% 准予发版）。"),
            ("Q90: 什么是 Red Teaming（红队攻防演练）？在 Agent 落地前如何开展？",
             "模拟恶意攻击者向 Agent 发起对抗性提示词攻击（提示词注入越狱、诱导泄露敏感系统 Prompt、诱导执行破坏性 SQL/系统命令、利用参数漏洞导致死循环等），根据攻防暴露出的漏洞修补安全边界。"),
            ("Q91: 生产环境中当用户反馈“回答很差（Bad Feedback）”时，闭环排查流水线应该怎么走？",
             "1. 通过 Trace ID 定位完整追踪链路；\n"
             "2. 检查 Query 是否歧义，Router 是否分流错误；\n"
             "3. 查看知识检索召回片段是否包含正确事实（若无，排查切片与召回）；\n"
             "4. 查看最终输入上下文是否包含事实（若有但答错，排查 Prompt 约束与模型能力）；\n"
             "5. 将该样本打标入库，纳入黄金评测集用于回归验证。"),
            ("Q92: 生产监控中应设置哪些告警指标（Alerting Rules）？",
             "业务级：连续 Tool Call 失败率 > 5%、Reviewer 拒绝率异常攀升、单会话平均轮次暴增（死循环特征）；\n"
             "系统级：API 429 限流频率、端到端响应耗时 P99 > 30s、每分钟 Token 突增、外部依赖健康检查失败。"),
        ]),
        # 九、工程落地与避坑深水区
        ("第九部分：企业级工程实践、避坑与架构深水区", [
            ("Q93: 在高并发生产环境下，Agent 的实时交互前端应该如何设计？",
             "必须采用全链路流式响应（Streaming via SSE / WebSocket）。不能等 Agent 运行数分钟才一次性返回，而应将中间的 Thinking...、Calling Tool: X...、Tool Finished 及最终文本以事件流实时推向前端，降低用户等待焦虑。"),
            ("Q94: 为什么很多基于开源框架搭建的 Agent 在生产环境下经常“挂死（Hanging）”？",
             "外部 HTTP 依赖、Subprocess 调用或数据库操作未设置严格的 Socket 超时时间；线程池耗尽；大模型连接池未释放；异步 async/await 混用同步阻塞代码（Sync I/O in Async Loop）导致主事件循环被锁死。"),
            ("Q95: 什么是“状态漂移（State Drift）”？如何防范？",
             "在长程对话或复杂多轮任务中，由于中间数据追加和错误累积，全局 State 中的关键原始参数被意外覆盖或偏离最初设定。\n"
             "防范：区分不可变初始约束（Immutable Constraints）与运行期工作区数据（Scratchpad），对核心初始目标在 Schema 层设置只读保护。"),
            ("Q96: 本地开发（Windows）与 Linux 生产容器部署常见差异有哪些？",
             "1. 文件路径：Windows 反斜杠容易转义报错，代码中必须统一使用 pathlib.Path；\n"
             "2. 编码问题：Windows 终端默认 GBK 容易引发 UTF-8 编码崩溃，需显式配置 PYTHONUTF8=1；\n"
             "3. 导入路径：统一采用 python -m package.module 执行，避免 sys.path 缺失根包；\n"
             "4. 异步事件循环：Windows 默认 ProactorEventLoop 在子进程通信上与 Linux Epoll 有差异。"),
            ("Q97: 当必须使用小型开源模型（如 7B/8B）在本地搭建 Agent 时，常见难点与克服方案是什么？",
             "难点：长指令遵循差、Function Calling 参数格式常写崩、复杂逻辑易迷失。\n"
             "方案：任务拆解为极简的单一职责原子节点，单个节点挂载工具不超过 2 个；采用针对 Tool Calling 微调过的权重；使用严格的语法限制采样库（如 Outlines）强制生成合法 JSON。"),
            ("Q98: 工业生产中，如何处理多租户环境下的数据库鉴权与 SQL 注入风险（Text-to-SQL）？",
             "严禁模型直接生成原生 SQL 并裸跑。模型仅输出结构化查询参数，由 ORM 组装参数化查询；若必须生成 SQL，使用只读账号连接，开启事务自动回滚，外层 AST 语法树解析强制拦截危险关键字，并在底层行级安全策略（RLS）强制绑定 tenant_id。"),
            ("Q99: 什么是“证据链追踪（Evidence-based Provenance）”？它为什么是商业智能 Agent 的生命线？",
             "企业销售情报若存在编造将带来灾难性商业损失。\n"
             "证据链追踪要求系统任何推论与商机打分必须能反向追溯到物理世界的原始数据源（具体落地页 URL、确切段落原文）。若缺乏原始字面证据，系统宁可标记 insufficient_evidence 也绝不输出编造结论。"),
            ("Q100: 面试官追问：“如果今天让你从零主导搭建一个企业级复杂业务的 AI Agent，你的前三步分别是什么？”",
             "第一步：明确业务边界与确定性流程（SOP 梳理）。梳理标准作业程序，厘清哪些是确定性状态机规则，哪些才需要 LLM 认知决策；\n"
             "第二步：设计严密的输入输出契约（Contracts & Schemas）与原子化工具。利用 Pydantic 规范全局 State 与协议，打造自描述、幂等、防超时的工具层与 MCP 接口；\n"
             "第三步：构建 LangGraph 状态图与评估闭环（Evals First）。先搭建 50+ 黄金测试集与链路追踪，以数据驱动量化评测指导后续 Prompt 调优与落地迭代。"),
        ])
    ]

    total_count = 0

    for part_title, qa_list in qa_data:
        # 一级模块标题
        h1 = doc.add_heading(level=1)
        run_h1 = h1.add_run(part_title)
        run_h1.font.name = "微软雅黑"
        run_h1.font.size = Pt(15)
        run_h1.font.bold = True
        run_h1.font.color.rgb = RGBColor(31, 78, 121)

        for q, a in qa_list:
            total_count += 1
            # 问题标题
            p_q = doc.add_paragraph()
            p_q.paragraph_format.space_before = Pt(8)
            p_q.paragraph_format.space_after = Pt(2)
            run_q = p_q.add_run(q)
            run_q.font.name = "微软雅黑"
            run_q.font.size = Pt(11)
            run_q.font.bold = True
            run_q.font.color.rgb = RGBColor(0, 51, 102)

            # 答案段落
            p_a = doc.add_paragraph()
            p_a.paragraph_format.space_before = Pt(2)
            p_a.paragraph_format.space_after = Pt(8)
            p_a.paragraph_format.line_spacing = 1.25
            run_a = p_a.add_run(a)
            run_a.font.name = "宋体"
            run_a.font.size = Pt(10.5)

    output_path = "AI_Agent_100_Interview_Questions.docx"
    doc.save(output_path)
    print(f"成功生成 Word 文档：{os.path.abspath(output_path)}，共包含 {total_count} 道面试精选问答！")

if __name__ == "__main__":
    create_interview_doc()