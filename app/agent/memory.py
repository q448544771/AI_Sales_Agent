import json


from app.database.db import SessionLocal
from app.database.models import Lead



# ============================================================
# Follow-up Node目前针对new客户的默认兜底动作
# ============================================================

DEFAULT_NEW_NEXT_ACTION = (
    "收集企业基础信息，确认产品类型、生产工艺以及当前质量检测方式，"
    "寻找质量部门、自动化部门或智能制造负责人。"
)



# ============================================================
# CRM允许的商机等级
# ============================================================
#
# 注意：
#
# CRM level表达的是：
#
#     高 / 中 / 低
#
# Reviewer中的：
#
#     Top 1
#     Top 2
#     Top 3
#
# 属于“本轮候选排名”，
# 不能写入CRM level字段。
#
# ============================================================

VALID_CRM_LEVELS = {
    "高",
    "中",
    "低",
}



# ============================================================
# 根据Score推导CRM等级
# ============================================================

def level_from_score(
    score
):

    """
    当Reviewer没有提供合法CRM等级时，
    根据purchase_intent_score生成：

        >= 0.80 -> 高
        >= 0.60 -> 中
        <  0.60 -> 低
    """


    try:

        score_value = float(
            score or 0.0
        )

    except (
        TypeError,
        ValueError
    ):

        score_value = 0.0


    if score_value >= 0.8:

        return "高"


    if score_value >= 0.6:

        return "中"


    return "低"



# ============================================================
# 解析Reviewer Level
# ============================================================

def resolve_crm_level(
    reviewer_level,
    score,
    existing_level=""
):

    """
    将Reviewer输出转换成真正的CRM level。


    优先级：

    1. Reviewer明确输出：
       高 / 中 / 低

       -> 直接使用


    2. Reviewer输出：
       Top 1 / Top 2 / Top 3

       -> 不写入CRM level


       如果数据库已有合法：

       高 / 中 / 低

       -> 保留原等级


    3. 如果数据库现有level本身也已经被
       Top 1 / Top 2 / Top 3污染：

       -> 根据score重新推导高/中/低


    这样可以同时：

    - 防止以后继续污染
    - 自动修复已经污染的候选客户
    """


    reviewer_level = (

        reviewer_level
        or
        ""

    ).strip()


    existing_level = (

        existing_level
        or
        ""

    ).strip()



    # ========================================================
    # Reviewer本身就是合法CRM等级
    # ========================================================

    if reviewer_level in VALID_CRM_LEVELS:

        return reviewer_level



    # ========================================================
    # 保留已有合法CRM等级
    # ========================================================

    if existing_level in VALID_CRM_LEVELS:

        return existing_level



    # ========================================================
    # Reviewer可能是Top 1 / Top 2 / Top 3，
    # 或历史数据库level已经被排名污染。
    #
    # 使用score恢复CRM等级。
    # ========================================================

    return level_from_score(
        score
    )



# ============================================================
# 解析连续JSON对象
# ============================================================

def parse_json_objects(content):

    """
    解析 MCP ToolMessage 中的企业搜索结果。

    MCP search_company 当前可能返回：

    {
        ...
    }
    {
        ...
    }
    {
        ...
    }

    也就是多个JSON对象连续出现，
    而不是一个标准JSON数组。

    这里把它们全部解析出来。
    """


    # --------------------------------------------------------
    # 已经是dict
    # --------------------------------------------------------

    if isinstance(content, dict):

        return [
            content
        ]


    # --------------------------------------------------------
    # 已经是list
    # --------------------------------------------------------

    if isinstance(content, list):

        result = []


        for item in content:

            if isinstance(item, dict):

                if (
                    "text" in item
                    and
                    isinstance(
                        item["text"],
                        str
                    )
                ):

                    result.extend(

                        parse_json_objects(
                            item["text"]
                        )

                    )

                else:

                    result.append(
                        item
                    )


        return result


    # --------------------------------------------------------
    # 不是字符串
    # --------------------------------------------------------

    if not isinstance(
        content,
        str
    ):

        return []


    text = content.strip()


    if not text:

        return []


    decoder = json.JSONDecoder()

    index = 0

    objects = []


    while index < len(text):


        # ----------------------------------------------------
        # 跳过空白字符
        # ----------------------------------------------------

        while (
            index < len(text)
            and
            text[index].isspace()
        ):

            index += 1


        if index >= len(text):

            break


        # ----------------------------------------------------
        # 尝试解析一个JSON对象
        # ----------------------------------------------------

        try:

            obj, end_index = (
                decoder.raw_decode(
                    text,
                    index
                )
            )

        except json.JSONDecodeError:

            break


        # ----------------------------------------------------
        # 保存解析结果
        # ----------------------------------------------------

        if isinstance(obj, dict):

            objects.append(
                obj
            )


        elif isinstance(obj, list):

            for item in obj:

                if isinstance(
                    item,
                    dict
                ):

                    objects.append(
                        item
                    )


        index = end_index


    return objects



# ============================================================
# 从Agent历史消息提取企业真实元数据
# ============================================================

def extract_company_metadata(
    state
):

    """
    从 search_company 的 ToolMessage 中提取：

    company/name
    industry
    region
    """


    metadata = {}


    messages = state.get(
        "messages",
        []
    )


    for message in messages:


        message_name = getattr(
            message,
            "name",
            None
        )


        if message_name != "search_company":

            continue


        content = getattr(
            message,
            "content",
            None
        )


        companies = (
            parse_json_objects(
                content
            )
        )


        for company_data in companies:


            company_name = (

                company_data.get(
                    "name"
                )

                or

                company_data.get(
                    "company"
                )

            )


            if not company_name:

                continue


            metadata[
                company_name
            ] = {

                "industry":
                    company_data.get(
                        "industry"
                    ),

                "region":
                    company_data.get(
                        "region"
                    ),

            }


    return metadata



# ============================================================
# 从Executor Tool Call恢复CRM更新意图
# ============================================================

def extract_pending_crm_updates(
    state
):

    """
    提取Executor生成过的：

    update_lead_stage(...)

    后面的调用覆盖前面的调用，
    以最新一次Executor决策为准。
    """


    updates = {}


    messages = state.get(
        "messages",
        []
    )


    for message in messages:


        tool_calls = getattr(
            message,
            "tool_calls",
            None
        )


        if not tool_calls:

            continue


        for tool_call in tool_calls:


            if (
                tool_call.get(
                    "name"
                )
                !=
                "update_lead_stage"
            ):

                continue


            args = tool_call.get(
                "args",
                {}
            )


            company = args.get(
                "company"
            )


            if not company:

                continue


            updates[
                company
            ] = {

                "stage":
                    args.get(
                        "stage"
                    ),

                "next_action":
                    args.get(
                        "next_action"
                    ),

            }


    return updates



# ============================================================
# Evidence标准化
# ============================================================

def serialize_evidence(
    evidence
):

    """
    将evidence统一存储为JSON字符串。

    避免字符串再次json.dumps导致双重编码。
    """


    if isinstance(
        evidence,
        str
    ):

        return evidence


    return json.dumps(

        evidence or [],

        ensure_ascii=False

    )



# ============================================================
# 清理新客户推荐动作
# ============================================================

def clean_recommended_action(
    action
):

    """
    清除Reviewer中已经无意义的
    “先录入CRM”前缀。
    """


    if not action:

        return ""


    prefixes = [

        "先由人工/后台将该企业录入CRM并设为new阶段；",

        "先由人工/后台将该企业录入CRM并设为 new 阶段；",

        "先将该企业录入CRM并设为new阶段；",

        "先将该企业录入CRM并设为 new 阶段；",

    ]


    cleaned = action.strip()


    for prefix in prefixes:

        if cleaned.startswith(
            prefix
        ):

            cleaned = cleaned[
                len(prefix):
            ].strip()

            break


    return cleaned



# ============================================================
# Memory Node
# ============================================================

def memory_node(state):

    """
    将Reviewer候选结果持久化到CRM。


    Reviewer中的：

        opportunity_level

    可能表示两种不同含义：

        高 / 中 / 低
            -> CRM商机等级

        Top 1 / Top 2 / Top 3
            -> 本轮候选排名


    本节点保证：

        Lead.level

    永远只保存：

        高 / 中 / 低


    Top排名继续保留在：

        state["candidate_leads"]

    中用于最终报告展示。
    """


    # ========================================================
    # 获取候选Lead
    # ========================================================

    leads = state.get(
        "candidate_leads",
        []
    )


    if not leads:

        return {

            "memory_saved":
                0,

            "status":
                "no leads"

        }



    # ========================================================
    # 提取辅助信息
    # ========================================================

    company_metadata = (
        extract_company_metadata(
            state
        )
    )


    pending_crm_updates = (
        extract_pending_crm_updates(
            state
        )
    )



    # ========================================================
    # Sales Goal
    # ========================================================

    goal = state.get(
        "goal"
    )


    goal_industry = (

        getattr(
            goal,
            "target_industry",
            ""
        )

        if goal

        else ""

    )


    goal_region = (

        getattr(
            goal,
            "target_region",
            ""
        )

        if goal

        else ""

    )



    # ========================================================
    # Database Session
    # ========================================================

    db = SessionLocal()


    saved_count = 0



    try:


        # ====================================================
        # 遍历Reviewer候选客户
        # ====================================================

        for lead_data in leads:


            company = lead_data.get(
                "company"
            )


            if not company:

                continue



            # =================================================
            # 查询已有客户
            # =================================================

            existing = (

                db.query(Lead)

                .filter(
                    Lead.company == company
                )

                .first()

            )



            # =================================================
            # Reviewer基础数据
            # =================================================

            evidence = serialize_evidence(

                lead_data.get(
                    "evidence",
                    []
                )

            )


            score = lead_data.get(

                "purchase_intent_score",

                0

            )


            # =================================================
            # Reviewer的opportunity_level
            # =================================================
            #
            # 注意：
            #
            # 这里不再直接写：
            #
            # existing.level = opportunity_level
            #
            # 因为它可能是：
            #
            # Top 1 / Top 2 / Top 3
            #
            # =================================================

            reviewer_level = (

                lead_data.get(
                    "opportunity_level",
                    ""
                )

                or

                ""

            ).strip()



            # =================================================
            # 生成真正的CRM level
            # ============================================================

            crm_level = resolve_crm_level(

                reviewer_level=(
                    reviewer_level
                ),

                score=score,

                existing_level=(

                    existing.level

                    if existing

                    else ""

                )

            )



            # =================================================
            # 调试信息
            # ========================================================

            if (
                reviewer_level
                and
                reviewer_level
                not in
                VALID_CRM_LEVELS
            ):

                print(

                    f"Reviewer排名不写入CRM level: "
                    f"{company} | "
                    f"{reviewer_level} -> "
                    f"{crm_level}"

                )



            action = clean_recommended_action(

                lead_data.get(
                    "recommended_action",
                    ""
                )

            )



            # =================================================
            # Company MCP真实行业 / 地区
            # =================================================

            company_meta = (

                company_metadata.get(
                    company,
                    {}
                )

            )


            explicit_industry = (

                lead_data.get(
                    "industry"
                )

                or

                company_meta.get(
                    "industry"
                )

            )


            explicit_region = (

                lead_data.get(
                    "region"
                )

                or

                company_meta.get(
                    "region"
                )

            )



            # =================================================
            # Executor之前生成的CRM操作
            # =================================================

            pending_update = (

                pending_crm_updates.get(
                    company,
                    {}
                )

            )


            executor_next_action = (

                pending_update.get(
                    "next_action"
                )

                or

                ""

            ).strip()



            # =================================================
            # Reviewer显式next_action
            # =================================================

            reviewer_next_action = (

                lead_data.get(
                    "next_action"
                )

                or

                ""

            ).strip()



            # =================================================
            # 最终next_action
            # =================================================

            resolved_next_action = (

                executor_next_action

                or

                reviewer_next_action

                or

                action

                or

                None

            )



            # =================================================
            # 已存在 -> 更新
            # =================================================

            if existing:


                print(
                    f"更新已有客户: {company}"
                )


                # ---------------------------------------------
                # Reviewer评估信息
                # ---------------------------------------------

                existing.score = score


                # ---------------------------------------------
                # CRM level只保存：
                #
                # 高 / 中 / 低
                # ---------------------------------------------

                existing.level = (
                    crm_level
                )


                existing.evidence = evidence

                existing.action = action

                existing.status = "updated"



                # ---------------------------------------------
                # 真实industry
                # ---------------------------------------------

                if explicit_industry:

                    existing.industry = (
                        explicit_industry
                    )



                # ---------------------------------------------
                # 真实region
                # ---------------------------------------------

                if explicit_region:

                    existing.region = (
                        explicit_region
                    )



                # ---------------------------------------------
                # next_action
                # ---------------------------------------------

                if not existing.next_action:

                    existing.next_action = (
                        resolved_next_action
                    )


                elif (

                    existing.stage == "new"

                    and

                    existing.next_action
                    ==
                    DEFAULT_NEW_NEXT_ACTION

                    and

                    resolved_next_action

                ):

                    print(
                        f"升级新客户跟进动作: {company}"
                    )

                    existing.next_action = (
                        resolved_next_action
                    )



            # =================================================
            # 不存在 -> 新增
            # =================================================

            else:


                print(
                    f"新增客户: {company}"
                )



                industry = (

                    explicit_industry

                    or

                    goal_industry

                )


                region = (

                    explicit_region

                    or

                    goal_region

                )



                # ---------------------------------------------
                # 新客户始终从new开始
                # ---------------------------------------------

                stage = "new"



                new_lead = Lead(

                    company=company,

                    industry=industry,

                    region=region,

                    score=score,


                    # -----------------------------------------
                    # 注意：
                    #
                    # 这里同样使用crm_level，
                    # 而不是Reviewer Top排名。
                    # -----------------------------------------

                    level=crm_level,

                    evidence=evidence,

                    action=action,

                    stage=stage,

                    next_action=(
                        resolved_next_action
                    ),

                    owner=None,

                    last_contact_time=None,

                    status="new",

                )


                db.add(
                    new_lead
                )



            saved_count += 1



        # ====================================================
        # Commit
        # ====================================================

        db.commit()



    except Exception:


        db.rollback()

        raise



    finally:


        db.close()



    # ========================================================
    # LangGraph State返回
    # ========================================================

    return {

        "memory_saved":
            saved_count,

        "status":
            "success"

    }