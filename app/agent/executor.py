from app.llm.model import get_tool_llm



from app.mcp.adapter import (

    load_all_langchain_tools_sync,

)





from langchain_core.messages import (

    ToolMessage,

    SystemMessage,

)







# ============================================================

# 加载全部 MCP Tools

# ============================================================

#

# Company MCP:

#

# search_company

# get_company_news

# get_company_jobs

#

# CRM MCP:

#

# query_leads

# create_lead

# update_lead_stage

#

# Knowledge MCP:

#

# search_product_knowledge

#

# ============================================================



tools = (

    load_all_langchain_tools_sync()

)







# ============================================================

# Tool Map

# ============================================================



tool_map = {



    tool.name:

        tool



    for tool in tools



}







# ============================================================

# Tool名称

# ============================================================



SEARCH_COMPANY_TOOL_NAME = (

    "search_company"

)





KNOWLEDGE_TOOL_NAME = (

    "search_product_knowledge"

)







# ============================================================

# Search Reliability 配置

# ============================================================



# 普通情况下允许的最大企业搜索次数

DEFAULT_SEARCH_BUDGET = 10





# 如果CRM已经存在足够高质量候选，

# 只进行少量补充搜索。

SATURATED_SEARCH_BUDGET = 4





# 单次LLM响应最多允许生成多少个

# search_company Tool Call。

MAX_SEARCH_CALLS_PER_ROUND = 4





# 连续多少次搜索为空后，

# 提前停止继续搜索。

MAX_CONSECUTIVE_EMPTY_SEARCHES = 4





# 用于判断CRM候选池是否已经充足。

HIGH_VALUE_SCORE_THRESHOLD = 0.8







# ============================================================

# Knowledge Reliability 配置

# ============================================================



# 单个任务最多允许调用几次知识库。

#

# 防止：

#

# - 对相似问题反复检索

# - Knowledge Tool无限循环

# - 同一个产品文档被反复返回

#

MAX_KNOWLEDGE_CALLS_PER_TASK = 2





# 单次LLM响应最多允许调用一次知识库。

#

# 这样Agent应该：

#

# 先查一次

#   ↓

# 阅读结果

#   ↓

# 再决定是否真的需要第二次查询

#

# 而不是一次并行发起多个相似查询。

#

MAX_KNOWLEDGE_CALLS_PER_ROUND = 1







# ============================================================

# Knowledge Reliability Rules

# ============================================================



KNOWLEDGE_RELIABILITY_RULES = """



============================================================

Knowledge Reliability Rules

============================================================



产品知识库是企业内部事实来源。



使用 search_product_knowledge 时必须严格遵守以下规则。





一、区分三类信息



你必须始终区分：



1. 企业事实



来源于：



- 企业新闻

- 企业招聘

- CRM

- 企业搜索结果





2. 内部产品知识



来源于：



search_product_knowledge





3. 销售推断



由企业事实和产品知识推导出的：



- 潜在需求

- 销售机会

- 推荐方案

- 下一步动作





销售推断不能写成已经确认的事实。







二、禁止扩写知识库不存在的产品能力



只有知识库明确返回的内容，



才能描述为：



“我司产品能力”

“已有方案”

“已有案例”

“已有技术指标”。





如果知识库没有明确说明：



- 检出率

- 准确率

- 误报率

- 检测节拍

- 具体缺陷类型

- 技术参数

- 产品价格

- 报价

- ROI

- 回本周期

- 客户案例

- POC结果

- 认证信息

- 行业认证

- 已落地项目



禁止自行编造。





此时应该明确说：



“当前内部知识库未提供该信息。”



或者：



“该项需要进一步确认。”





可以把这些内容作为：



- 后续调研项

- POC验证项

- ROI测算项

- 客户沟通确认项



但不能描述为已有事实。







三、禁止把行业常识包装成内部产品知识



即使你知道某些行业通用知识，



如果内部知识库没有明确提供，



也不能说：



“我们的系统已经支持……”



“我们的案例已经验证……”



“我们的产品达到……”





可以使用行业常识进行一般性分析，



但必须明确属于：



“分析”

“推断”

“建议进一步确认”



而不是内部产品事实。







四、企业需求必须有企业证据



产品知识不能证明客户存在需求。





例如：



知识库支持焊缝检测



并不能证明：



某企业一定正在采购焊缝检测系统。





客户需求必须结合：



- 新产线

- 扩产

- 自动化改造

- 质量升级

- 招聘信息

- CRM历史

- 其他企业情报



进行判断。







五、不要做过度确定的推断



例如：



企业没有招聘机器视觉工程师



不能直接得出：



“企业内部没有机器视觉能力”。





更合理的表达是：



“当前公开招聘信息中未发现机器视觉岗位，

可能存在外部方案合作机会，

但仍需要首次沟通确认内部技术能力。”





企业新增机器人焊接工位



也不能直接得出：



“一定会采购视觉检测设备”。





应该表达为：



“机器人焊接工位增加了焊接质量检测的潜在需求，

建议进一步确认当前检测方式和采购计划。”







六、避免重复知识检索



如果已经检索到了能够回答当前问题的产品知识，



应该优先复用已有结果。





不要为了：



- 换一种说法

- 查询同一个产品能力

- 查询高度相似的检测场景



重复调用 search_product_knowledge。





如果知识库第一次已经没有提供：



- 报价

- ROI

- 案例

- 指标



不要通过重复换关键词，



试图让知识库“找出”不存在的信息。







七、低相关结果处理



向量知识库即使没有真正匹配的内容，



也可能返回最接近的文档。





因此：



如果返回文档并没有明确回答当前问题，



必须认为：



“当前知识库没有提供相关信息。”





不能因为Retriever返回了文档，



就认为文档一定支持当前结论。







八、最终输出原则



推荐按照以下逻辑：





【企业证据】



企业实际出现了什么信号。





【内部产品匹配】



知识库明确支持哪些能力。





【销售推断】



基于前两者，可以推测什么机会。





【待确认信息】



哪些信息必须通过：



- 首次电话

- 邮件

- 技术交流

- POC

- 客户现场



进一步验证。



============================================================



"""





# ============================================================

# Sales Action Reliability Rules

# ============================================================



SALES_ACTION_RELIABILITY_RULES = """



============================================================

Sales Action Reliability Rules

============================================================



销售动作、CRM next_action 和最终建议

必须遵守以下规则。





一、ROI不能冒充已有数据



如果内部知识库没有明确提供：



- ROI

- 投资回报数据

- 回本周期

- 客户收益数据



禁止写：



“提供ROI”



“向客户展示ROI”



“提供现成ROI数据”





应该写成：



“收集客户产线、人力、返工等数据后进行ROI测算”



或者：



“准备ROI测算框架，并在需求确认后计算”。





ROI可以作为未来销售动作，



但不能描述为企业内部已经拥有的数据。







二、不能虚构客户案例



只有内部知识库明确包含：



- 客户名称

- 项目背景

- 具体方案

- 项目结果



等可识别案例信息时，



才能表述为：



“已有客户案例”。





如果知识库只是存在：



“新能源汽车案例”



这样的章节标题，



但内容实际上只是：



“可以进行焊缝检测、表面缺陷检测、尺寸检测”



则它只能证明产品能力，



不能证明存在具体落地客户案例。





禁止写：



“推送汽车电子成功案例”



“提供新能源零部件成熟案例”



“已有某行业落地案例”



除非知识库明确支持。





更合理的动作是：



“准备与客户场景匹配的产品方案材料”



或者：



“如内部后续确认存在相关案例，再作为销售材料使用”。







三、POC只能作为未来验证动作



允许建议：



- POC

- 样件测试

- 打光验证

- 成像验证



因为这些属于未来销售动作。





但是不能把它们描述成：



“已有POC成功结果”



“已经验证达到某指标”



除非内部知识库有明确证据。







四、招聘信号绝不能直接推进CRM Stage



企业出现：



- 机器视觉工程师

- 视觉算法工程师

- 自动化工程师

- 质量工程师

- 视觉检测工程师



等招聘信息，



只能够影响：



- 商机优先级

- purchase_intent_score

- 销售关注度

- next_action

- 跟进频率





招聘信号不能单独导致：



new -> qualified



contacted -> qualified



或任何其他stage推进。





禁止出现：



“一旦出现机器视觉岗位立即升级qualified”。





应该写：



“一旦出现机器视觉相关岗位，

上调商机优先级并加强触达，

但CRM stage仍需依据真实销售进展决定。”







五、Stage只反映真实销售过程



Stage推进必须有真实销售事件支持。



例如：



new -> contacted



需要存在真实首次触达。





contacted -> qualified



需要经过实际沟通，

确认存在合理需求、预算、项目或采购机会。





qualified -> meeting



需要真实会议或技术交流被确认。





不得因为：



- 新闻

- 招聘

- 扩产

- 自动化改造

- 模型推断

- 高评分



直接推进stage。







六、last_contact_time为空时



如果：



last_contact_time = None



说明当前没有可确认的真实触达记录。





此时：



- 可以刷新next_action

- 可以提高商机优先级

- 可以补充情报

- 可以形成产品方案匹配





但不得仅依据公开情报继续向前推进stage。





如果历史CRM中已经存在较高stage，



不要自动降级，



但也不要因为新的公开信号继续升级。







七、next_action建议格式



优先使用：



“联系谁”



+



“确认什么”



+



“准备什么”



+



“下一阶段满足什么真实条件才推进”





例如：



“48小时内联系质量/自动化负责人，

确认当前检测方式、具体缺陷类型、产线节拍和采购计划；

准备外观缺陷与尺寸检测方案材料；

收集人力与返工数据后进行ROI测算；

真实沟通确认需求后再决定是否推进CRM stage。”





============================================================



"""





# ============================================================

# Search Result 是否为空

# ============================================================



def is_empty_search_result(

    content

):



    """

    判断 search_company ToolMessage

    是否属于空搜索结果。



    当前可能出现：



        ""



        []



        {}



        null



    都视为没有找到企业。

    """





    if content is None:



        return True





    if isinstance(

        content,

        str

    ):



        text = content.strip()





        if text in {

            "",

            "[]",

            "{}",

            "null",

            "None",

        }:



            return True





        return False





    if isinstance(

        content,

        (list, dict)

    ):



        return len(content) == 0





    return False







# ============================================================

# 统计 Search 使用情况

# ============================================================



def get_search_statistics(

    messages

):



    """

    统计当前任务中的search_company使用情况。



    与旧版本不同：



    不再只依赖ToolMessage统计。



    同时读取：



    1. AIMessage.tool_calls

    2. ToolMessage.tool_call_id



    并根据Tool Call ID去重。



    这样即使LangGraph某一轮状态合并时

    ToolMessage统计存在时序差异，



    只要上一轮AI已经生成了search_company调用，

    下一轮就能够正确占用Search Budget。

    """





    # 已经计划或执行过的search_company调用ID

    search_call_ids = set()





    # 极端情况下Tool Call没有ID，

    # 使用独立计数兜底。

    anonymous_search_calls = 0





    # 已执行的search_company结果，

    # 用于判断连续空搜索。

    search_results = []





    for message in messages:





        # ====================================================

        # 1. 从AIMessage.tool_calls统计

        # ====================================================

        #

        # 不要求message一定是AIMessage，

        # 只要对象具有tool_calls即可。

        #

        # 这样不需要重新引入AIMessage类型。

        # ====================================================



        tool_calls = (



            getattr(

                message,

                "tool_calls",

                None

            )



            or



            []



        )





        for tool_call in tool_calls:





            if not isinstance(

                tool_call,

                dict

            ):



                continue





            if (

                tool_call.get("name")

                !=

                SEARCH_COMPANY_TOOL_NAME

            ):



                continue





            tool_call_id = (

                tool_call.get("id")

            )





            if tool_call_id:



                search_call_ids.add(

                    tool_call_id

                )



            else:



                anonymous_search_calls += 1





        # ====================================================

        # 2. 从ToolMessage统计实际执行结果

        # ====================================================



        if (



            isinstance(

                message,

                ToolMessage

            )



            and



            getattr(

                message,

                "name",

                None

            )

            ==

            SEARCH_COMPANY_TOOL_NAME



        ):



            search_results.append(

                message

            )





            tool_call_id = getattr(



                message,



                "tool_call_id",



                None



            )





            if tool_call_id:



                # 与AIMessage中的同一个ID自动去重

                search_call_ids.add(

                    tool_call_id

                )



            else:



                anonymous_search_calls += 1





    # ========================================================

    # Search总使用量

    # ========================================================



    total_searches = (



        len(

            search_call_ids

        )



        +



        anonymous_search_calls



    )





    # ========================================================

    # 连续空搜索次数

    # ========================================================

    #

    # 连续空结果只看真正执行完成的ToolMessage。

    # ========================================================



    consecutive_empty = 0





    for message in reversed(

        search_results

    ):



        if is_empty_search_result(

            message.content

        ):



            consecutive_empty += 1



        else:



            break





    return {



        "total_searches":

            total_searches,



        "consecutive_empty":

            consecutive_empty,



    }








# ============================================================
# Knowledge使用统计
# ============================================================

def get_knowledge_statistics(
    messages
):

    """
    统计当前任务中
    search_product_knowledge
    的使用次数。

    同Search Budget一样，
    同时读取：

    1. AIMessage.tool_calls
    2. ToolMessage.tool_call_id

    并根据Tool Call ID去重。

    这样可以避免LangGraph跨轮状态更新时，
    仅依赖ToolMessage造成Knowledge Budget
    统计滞后的问题。
    """

    # 已经计划或执行过的Knowledge Tool Call ID
    knowledge_call_ids = set()

    # 极端情况下Tool Call没有ID，
    # 使用独立计数兜底。
    anonymous_knowledge_calls = 0

    for message in messages:

        # ====================================================
        # 1. 从AIMessage.tool_calls统计
        # ====================================================

        tool_calls = (
            getattr(
                message,
                "tool_calls",
                None
            )
            or
            []
        )

        for tool_call in tool_calls:

            if not isinstance(
                tool_call,
                dict
            ):
                continue

            if (
                tool_call.get("name")
                !=
                KNOWLEDGE_TOOL_NAME
            ):
                continue

            tool_call_id = (
                tool_call.get("id")
            )

            if tool_call_id:
                knowledge_call_ids.add(
                    tool_call_id
                )
            else:
                anonymous_knowledge_calls += 1

        # ====================================================
        # 2. 从ToolMessage统计实际执行调用
        # ====================================================

        if (
            isinstance(
                message,
                ToolMessage
            )
            and
            getattr(
                message,
                "name",
                None
            )
            ==
            KNOWLEDGE_TOOL_NAME
        ):

            tool_call_id = getattr(
                message,
                "tool_call_id",
                None
            )

            if tool_call_id:
                # 与AIMessage中的相同调用自动去重
                knowledge_call_ids.add(
                    tool_call_id
                )
            else:
                anonymous_knowledge_calls += 1

    total_calls = (
        len(
            knowledge_call_ids
        )
        +
        anonymous_knowledge_calls
    )

    return {
        "total_calls":
            total_calls
    }


# ============================================================

# 判断CRM客户池是否已经足够

# ============================================================



def crm_pool_is_sufficient(

    memory_context,

    target_count

):



    """

    判断当前CRM是否已经拥有足够数量的

    高质量潜在客户。

    """





    high_value_count = 0





    for lead in memory_context:



        if not isinstance(

            lead,

            dict

        ):



            continue





        try:



            score = float(



                lead.get(

                    "score",

                    0.0

                )



                or



                0.0



            )



        except (

            TypeError,

            ValueError

        ):



            score = 0.0





        if (

            score

            >=

            HIGH_VALUE_SCORE_THRESHOLD

        ):



            high_value_count += 1





    return (

        high_value_count

        >=

        target_count

    )







# ============================================================

# 计算本轮Search Budget

# ============================================================



def get_search_budget(

    memory_context,

    goal

):



    """

    根据当前CRM候选池动态决定企业搜索预算。

    """





    target_count = getattr(



        goal,



        "target_count",



        3



    )





    try:



        target_count = int(

            target_count

            or

            3

        )



    except (

        TypeError,

        ValueError

    ):



        target_count = 3





    if crm_pool_is_sufficient(



        memory_context,



        target_count



    ):



        return (

            SATURATED_SEARCH_BUDGET

        )





    return (

        DEFAULT_SEARCH_BUDGET

    )







# ============================================================

# 原地更新AIMessage Tool Calls

# ============================================================



def update_tool_calls_in_place(

    response,

    tool_calls

):



    """

    在不重新构造AIMessage的情况下，

    修改当前LLM响应中的Tool Calls。





    重要：



    DeepSeek Thinking Mode在多轮Tool Calling中，

    需要上一轮Assistant Message中的reasoning_content

    能够被完整回传。





    如果重新创建一个新的AIMessage：



        AIMessage(...)



    可能丢失DeepSeek Provider附带的

    reasoning_content等扩展信息，



    从而在下一轮请求时报错：



        The `reasoning_content` in the thinking mode

        must be passed back to the API.





    因此这里：



        不创建新的AIMessage



    而是：



        直接修改原始response.tool_calls





    这样可以最大程度保留原始模型响应中的：



    - reasoning_content

    - response_metadata

    - provider扩展字段

    - usage_metadata

    - message id

    - 其他Provider-specific信息

    """





    response.tool_calls = list(

        tool_calls

    )





    # ========================================================

    # 清理可能存在的旧tool_calls副本

    # ========================================================

    #

    # 某些Provider / LangChain版本可能同时在：

    #

    # response.tool_calls

    #

    # 和：

    #

    # response.additional_kwargs["tool_calls"]

    #

    # 中保存调用信息。

    #

    # 如果存在旧副本，需要删除。

    #

    # 注意：

    #

    # 这里只删除tool_calls。

    #

    # 绝对不能删除：

    #

    # reasoning_content

    #

    # 或其他Thinking Mode字段。

    # ========================================================



    additional_kwargs = getattr(



        response,



        "additional_kwargs",



        None



    )





    if isinstance(

        additional_kwargs,

        dict

    ):



        additional_kwargs.pop(

            "tool_calls",

            None

        )





    return response







# ============================================================

# 限制单次AIMessage中的Search Tool Calls

# ============================================================



def limit_search_tool_calls(

    response,

    allowed_search_calls

):



    """

    对LLM单次返回的Search Tool Calls增加硬限制。



    非search_company工具完全保留。

    """





    tool_calls = list(



        getattr(

            response,

            "tool_calls",

            []

        )



        or



        []



    )





    if not tool_calls:



        return response





    filtered_tool_calls = []



    accepted_search_calls = 0



    removed_search_calls = 0





    for tool_call in tool_calls:





        tool_name = (

            tool_call.get(

                "name"

            )

        )





        # ====================================================

        # 非search_company工具

        # ====================================================



        if (

            tool_name

            !=

            SEARCH_COMPANY_TOOL_NAME

        ):



            filtered_tool_calls.append(

                tool_call

            )



            continue





        # ====================================================

        # search_company

        # ====================================================



        if (

            accepted_search_calls

            <

            allowed_search_calls

        ):



            filtered_tool_calls.append(

                tool_call

            )



            accepted_search_calls += 1





        else:



            removed_search_calls += 1





    # ========================================================

    # 没有发生裁剪

    # ========================================================



    if removed_search_calls == 0:



        return response





    print(



        "\n[Search Budget] "



        f"本轮截断 "

        f"{removed_search_calls} "



        "个超出预算的 "

        "search_company 调用"



    )





    # ========================================================

    # 直接修改原始Response

    #

    # 不再重新构建AIMessage

    # ========================================================



    return update_tool_calls_in_place(



        response,



        filtered_tool_calls



    )







# ============================================================

# 限制Knowledge Tool Calls

# ============================================================



def limit_knowledge_tool_calls(

    response,

    allowed_knowledge_calls

):



    """

    对LLM单次返回的Knowledge Tool Call

    增加程序层硬限制。



    当前：



    单轮最多：



        MAX_KNOWLEDGE_CALLS_PER_ROUND



    单任务最多：



        MAX_KNOWLEDGE_CALLS_PER_TASK



    非Knowledge Tool完全保留。

    """





    tool_calls = list(



        getattr(

            response,

            "tool_calls",

            []

        )



        or



        []



    )





    if not tool_calls:



        return response





    filtered_tool_calls = []



    accepted_calls = 0



    removed_calls = 0





    for tool_call in tool_calls:





        tool_name = (

            tool_call.get(

                "name"

            )

        )





        # ====================================================

        # 非Knowledge Tool

        # ====================================================



        if (

            tool_name

            !=

            KNOWLEDGE_TOOL_NAME

        ):



            filtered_tool_calls.append(

                tool_call

            )



            continue





        # ====================================================

        # Knowledge Tool

        # ====================================================



        if (

            accepted_calls

            <

            allowed_knowledge_calls

        ):



            filtered_tool_calls.append(

                tool_call

            )



            accepted_calls += 1





        else:



            removed_calls += 1





    # ========================================================

    # 没有发生裁剪

    # ========================================================



    if removed_calls == 0:



        return response





    print(



        "\n[Knowledge Budget] "



        f"本轮截断 "

        f"{removed_calls} "



        "个重复或超出预算的 "

        "search_product_knowledge 调用"



    )





    # ========================================================

    # 直接修改原始Response

    #

    # 不再重新构建AIMessage

    # ========================================================



    return update_tool_calls_in_place(



        response,



        filtered_tool_calls



    )







# ============================================================

# 创建Executor

# ============================================================



def create_executor(

    available_tools=None

):



    """

    创建LLM Executor。

    """





    llm = get_tool_llm()





    if available_tools is None:



        available_tools = tools





    executor = llm.bind_tools(

        available_tools

    )





    return executor







# ============================================================

# 独立Agent执行循环

# ============================================================



def execute_agent(

    messages

):



    """

    独立Tool Calling调试循环。



    正式LangGraph流程使用：



        executor_node



    此调试循环同样启用：



        Knowledge Reliability Guard

        Knowledge Budget

    """





    runtime_messages = [



        SystemMessage(

            content=(

                KNOWLEDGE_RELIABILITY_RULES

            )

        ),



        *messages,



    ]





    while True:





        # ====================================================

        # 当前Knowledge调用统计

        # ====================================================



        knowledge_stats = (

            get_knowledge_statistics(

                runtime_messages

            )

        )





        used_knowledge_calls = (

            knowledge_stats[

                "total_calls"

            ]

        )





        remaining_knowledge_calls = max(



            0,



            MAX_KNOWLEDGE_CALLS_PER_TASK

            -

            used_knowledge_calls



        )





        knowledge_disabled = (



            remaining_knowledge_calls

            <=

            0



        )





        # ====================================================

        # 动态Tool集合

        # ====================================================



        if knowledge_disabled:



            available_tools = [



                tool



                for tool in tools



                if (

                    tool.name

                    !=

                    KNOWLEDGE_TOOL_NAME

                )



            ]



        else:



            available_tools = tools





        executor = create_executor(

            available_tools

        )





        # ====================================================

        # 调用LLM

        # ====================================================



        response = executor.invoke(

            runtime_messages

        )





        # ====================================================

        # Knowledge 单轮硬限制

        # ====================================================



        if not knowledge_disabled:



            allowed_knowledge_calls = min(



                MAX_KNOWLEDGE_CALLS_PER_ROUND,



                remaining_knowledge_calls



            )





            response = (

                limit_knowledge_tool_calls(



                    response,



                    allowed_knowledge_calls



                )

            )





        print(

            "\n===== AI Response ====="

        )





        print(

            response

        )





        # ====================================================

        # 没有Tool Call

        # ====================================================



        if not response.tool_calls:



            return response





        # ====================================================

        # 保存原始Assistant Message

        #

        # 注意：

        #

        # 此处保存的是DeepSeek原始Response对象。

        #

        # response中的reasoning_content等信息

        # 必须被保留下来，

        # 供下一轮Thinking Mode请求回传。

        # ====================================================



        runtime_messages.append(

            response

        )





        # ====================================================

        # 执行Tool Calls

        # ====================================================



        for tool_call in response.tool_calls:





            tool_name = (

                tool_call["name"]

            )





            tool_args = (

                tool_call["args"]

            )





            print(

                f"\n执行工具: {tool_name}"

            )





            print(

                f"工具参数: {tool_args}"

            )





            if tool_name not in tool_map:



                raise ValueError(



                    f"未注册的工具: "

                    f"{tool_name}。"



                    f"当前可用工具: "

                    f"{list(tool_map.keys())}"



                )





            tool = tool_map[

                tool_name

            ]





            result = tool.invoke(

                tool_args

            )





            print(

                "工具返回:",

                result

            )





            runtime_messages.append(



                ToolMessage(



                    content=str(

                        result

                    ),



                    tool_call_id=(

                        tool_call["id"]

                    ),



                    name=tool_name,



                )



            )







# ============================================================

# LangGraph Executor Node

# ============================================================



def executor_node(

    state

):



    """

    LangGraph Executor Node。





    当前拥有：



    Company MCP

    -----------

    search_company

    get_company_news

    get_company_jobs





    CRM MCP

    -------

    query_leads

    create_lead

    update_lead_stage





    Knowledge MCP

    -------------

    search_product_knowledge





    同时实现：



    Search Budget



    Knowledge Budget



    Knowledge Reliability Guard



    Stage语义约束



    CRM生命周期维护

    """





    # ========================================================

    # Memory Context

    # ========================================================



    memory_context = state.get(

        "memory_context",

        []

    )





    # ========================================================

    # Goal

    # ========================================================



    goal = state.get(

        "goal"

    )





    # ========================================================

    # 当前Messages

    # ========================================================



    state_messages = state.get(

        "messages",

        []

    )





    # ========================================================

    # Search Budget

    # ========================================================



    search_budget = (

        get_search_budget(



            memory_context,



            goal



        )

    )





    search_stats = (

        get_search_statistics(

            state_messages

        )

    )





    used_searches = (

        search_stats[

            "total_searches"

        ]

    )





    consecutive_empty = (

        search_stats[

            "consecutive_empty"

        ]

    )





    remaining_searches = max(



        0,



        search_budget

        -

        used_searches



    )





    search_budget_exhausted = (



        used_searches

        >=

        search_budget



    )





    empty_search_limit_reached = (



        consecutive_empty

        >=

        MAX_CONSECUTIVE_EMPTY_SEARCHES



    )





    search_disabled = (



        search_budget_exhausted



        or



        empty_search_limit_reached



    )





    # ========================================================

    # Knowledge Budget

    # ========================================================



    knowledge_stats = (

        get_knowledge_statistics(

            state_messages

        )

    )





    used_knowledge_calls = (

        knowledge_stats[

            "total_calls"

        ]

    )





    remaining_knowledge_calls = max(



        0,



        MAX_KNOWLEDGE_CALLS_PER_TASK

        -

        used_knowledge_calls



    )





    knowledge_disabled = (



        remaining_knowledge_calls

        <=

        0



    )





    # ========================================================

    # 动态Tool集合

    # ========================================================

    #

    # Search Budget耗尽：

    #

    #     移除search_company

    #

    # Knowledge Budget耗尽：

    #

    #     移除search_product_knowledge

    #

    # 其他工具保持不变。

    # ========================================================



    available_tools = []





    for tool in tools:





        if (



            search_disabled



            and



            tool.name

            ==

            SEARCH_COMPANY_TOOL_NAME



        ):



            continue





        if (



            knowledge_disabled



            and



            tool.name

            ==

            KNOWLEDGE_TOOL_NAME



        ):



            continue





        available_tools.append(

            tool

        )





    executor = create_executor(

        available_tools

    )





    # ========================================================

    # Search状态

    # ========================================================



    if search_disabled:





        if empty_search_limit_reached:



            search_status = (



                "企业搜索已停止："

                f"最近连续 "

                f"{consecutive_empty} "

                "次 search_company "

                "均未返回企业。"



            )



        else:



            search_status = (



                "企业搜索预算已用完："

                f"{used_searches}/"

                f"{search_budget}。"



            )



    else:



        search_status = (



            "企业搜索仍可使用。"

            f"当前已使用 "

            f"{used_searches}/"

            f"{search_budget} 次，"



            f"剩余 "

            f"{remaining_searches} 次。"



            f"单轮最多调用 "

            f"{MAX_SEARCH_CALLS_PER_ROUND} 次。"



        )





    # ========================================================

    # Knowledge状态

    # ========================================================



    if knowledge_disabled:



        knowledge_status = (



            "本任务产品知识检索预算已用完："

            f"{used_knowledge_calls}/"

            f"{MAX_KNOWLEDGE_CALLS_PER_TASK}。"



            "请复用已经获得的产品知识，"

            "不要继续重复查询。"



        )



    else:



        knowledge_status = (



            "产品知识库可以按需调用。"



            f"当前已使用 "

            f"{used_knowledge_calls}/"

            f"{MAX_KNOWLEDGE_CALLS_PER_TASK} 次，"



            f"剩余 "

            f"{remaining_knowledge_calls} 次。"



            f"每轮最多调用 "

            f"{MAX_KNOWLEDGE_CALLS_PER_ROUND} 次。"



        )





    # ========================================================

    # System Prompt

    # ========================================================



    memory_prompt = f"""



你是一名企业销售智能 Agent。





你的目标不是只生成一次性的客户名单，



而是持续发现潜在客户、分析销售机会，



并维护 CRM 中的企业销售生命周期。







============================================================

一、当前 CRM 历史客户

============================================================





{memory_context}







============================================================

二、企业搜索预算

============================================================





{search_status}





搜索规则：





1.



search_company 只用于发现新的潜在企业。





2.



不要为了穷举全国所有地区而重复搜索。





3.



如果当前CRM已经存在足够数量的高质量客户，



只进行少量补充发现即可。





4.



如果某些地区连续没有结果，



停止继续尝试类似地区。





5.



禁止重复搜索已经搜索过的



“行业 + 地区”组合。





6.



单次思考最多调用：



{MAX_SEARCH_CALLS_PER_ROUND}



次 search_company。





7.



搜索预算用完后，



继续使用已有客户完成：



- 新闻调查

- 招聘调查

- 产品方案匹配

- 商机判断

- CRM维护





不要执着于寻找新的第N家企业。







============================================================

三、企业情报工具

============================================================





1. search_company



根据行业和地区搜索潜在企业。





2. get_company_news



查询企业近期：



- 投资项目

- 新工厂

- 新生产线

- 扩产

- 自动化升级

- 智能制造

- 质量检测升级





3. get_company_jobs



查询企业近期招聘岗位。





重点关注：



- 机器视觉工程师

- 视觉算法工程师

- 自动化工程师

- 质量工程师

- 质量检测工程师

- 工艺工程师







============================================================

四、企业内部产品知识工具

============================================================





search_product_knowledge



用于查询企业内部产品知识库。





当前Knowledge状态：



{knowledge_status}





可以查询：



- 产品能力

- 产品功能

- 检测场景

- 行业解决方案

- 技术方案

- 产品优势

- 企业内部已有案例资料





当你已经发现企业存在某个具体生产或质量场景，



并需要判断：



“我们的产品是否能够解决这个问题”



或者：



“应该向这个企业推荐什么具体方案”



时，



可以调用：



search_product_knowledge





查询应该尽量具体。





例如：



“新能源汽车结构件 焊缝视觉检测方案”



而不是：



“机器视觉是什么”。





如果已经获得可以回答问题的知识，



不要重复查询。





{KNOWLEDGE_RELIABILITY_RULES}



{SALES_ACTION_RELIABILITY_RULES}



============================================================

五、CRM工具

============================================================





1. query_leads



查询CRM已有客户。





2. create_lead



仅用于创建CRM中不存在的新客户。





创建前必须：



- 确认CRM中不存在

- 完成基本企业情报调查

- 存在合理销售机会





新客户统一：



stage = new





3. update_lead_stage



仅用于更新已经存在的CRM客户。







============================================================

六、CRM阶段规则

============================================================





销售生命周期：





new

 ↓

contacted

 ↓

qualified

 ↓

meeting

 ↓

proposal

 ↓

negotiation

 ↓

won





任意进行中的阶段可以进入：



lost





禁止跳级。





例如：



new → qualified



是不允许的。





如果客户仍然：



last_contact_time = None



通常说明尚没有真实销售触达。





此时即使存在：



- 机器视觉招聘

- 新生产线

- 自动化升级

- 明确检测需求



也应该优先：



提高商机优先级



更新next_action





而不是虚构已完成的销售触达。





如果stage保持不变，



仍然可以使用update_lead_stage



刷新next_action。







============================================================

七、新客户处理流程

============================================================





search_company



        ↓



确认CRM不存在



        ↓



get_company_news

+

get_company_jobs



        ↓



识别具体生产/质检场景



        ↓



必要时调用

search_product_knowledge



        ↓



判断：



企业需求

+

内部产品能力



是否存在合理匹配



        ↓



create_lead





不要使用update_lead_stage



来探测新客户是否存在。







============================================================

八、已有客户处理流程

============================================================





查询已有CRM信息



        ↓



检查新闻



        ↓



检查招聘



        ↓



判断需求变化



        ↓



必要时调用

search_product_knowledge



        ↓



形成针对性的方案切入点



        ↓



更新next_action



        ↓



只有真实销售进程变化时



才推进stage







============================================================

九、停止条件

============================================================





以下任意情况出现时，



应该停止继续发现新企业：





- search_company预算已经用完



- 连续搜索无结果



- 已有客户已经足以满足任务目标



- 新搜索结果全部是CRM已有企业





停止搜索不代表结束任务。





停止发现后，



应继续完成：



- 客户情报分析

- 产品方案匹配

- 商机排序

- CRM维护

- 下一步动作设计







============================================================

十、最终目标

============================================================





形成：



企业发现

    ↓

需求信号识别

    ↓

产品方案匹配

    ↓

CRM入库

    ↓

真实销售触达

    ↓

需求确认

    ↓

销售阶段推进

    ↓

成交或归档





的完整销售生命周期。



"""





    # ========================================================

    # Messages

    # ========================================================



    messages = [



        SystemMessage(

            content=memory_prompt

        )



    ] + state_messages





    # ========================================================

    # 调用LLM

    # ========================================================



    response = executor.invoke(

        messages

    )





    # ========================================================

    # Search Tool Call硬限制

    # ========================================================



    if not search_disabled:



        allowed_search_calls = min(



            MAX_SEARCH_CALLS_PER_ROUND,



            remaining_searches



        )





        response = (

            limit_search_tool_calls(



                response,



                allowed_search_calls



            )

        )





    # ========================================================

    # Knowledge Tool Call硬限制

    # ========================================================



    if not knowledge_disabled:



        allowed_knowledge_calls = min(



            MAX_KNOWLEDGE_CALLS_PER_ROUND,



            remaining_knowledge_calls



        )





        response = (

            limit_knowledge_tool_calls(



                response,



                allowed_knowledge_calls



            )

        )





    return {



        "messages": [

            response

        ],



        "status":

            "executing",



    }