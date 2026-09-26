import json


from langchain_core.tools import tool


from app.database.db import SessionLocal
from app.database.models import Lead



# ============================================================
# CRM销售阶段
# ============================================================

VALID_LEAD_STAGES = {

    "new",
    "contacted",
    "qualified",
    "meeting",
    "proposal",
    "negotiation",
    "won",
    "lost",

}



# ============================================================
# CRM合法生命周期转换
# ============================================================
#
# 原则：
#
# 1. 允许保持当前阶段
#    这样可以只刷新 next_action
#
# 2. 正常销售阶段只能逐级推进
#
# 3. lost 可以从任意进行中的阶段进入
#
# 4. won / lost 暂时视为终态
#
# ============================================================

ALLOWED_STAGE_TRANSITIONS = {

    "new": {
        "new",
        "contacted",
        "lost",
    },

    "contacted": {
        "contacted",
        "qualified",
        "lost",
    },

    "qualified": {
        "qualified",
        "meeting",
        "lost",
    },

    "meeting": {
        "meeting",
        "proposal",
        "lost",
    },

    "proposal": {
        "proposal",
        "negotiation",
        "lost",
    },

    "negotiation": {
        "negotiation",
        "won",
        "lost",
    },

    "won": {
        "won",
    },

    "lost": {
        "lost",
    },

}



# ============================================================
# 行业名称标准化
# ============================================================

def normalize_industry(
    industry: str
):

    """
    标准化行业名称。
    """


    if not industry:

        return ""


    return "".join(

        industry
        .strip()
        .lower()
        .split()

    )



# ============================================================
# 行业兼容匹配
# ============================================================

def industry_matches(
    query_industry: str,
    lead_industry: str
):

    """
    支持父子行业兼容查询。

    例如：

        汽车零部件

    可以匹配：

        汽车零部件
        新能源汽车零部件
    """


    query = normalize_industry(
        query_industry
    )


    candidate = normalize_industry(
        lead_industry
    )


    if not query:

        return True


    if not candidate:

        return False


    if query == candidate:

        return True


    if query in candidate:

        return True


    if candidate in query:

        return True


    return False



# ============================================================
# Evidence序列化
# ============================================================

def serialize_evidence(
    evidence
):

    """
    将Evidence保存成数据库Text字段需要的JSON字符串。
    """


    if evidence is None:

        evidence = []


    if isinstance(
        evidence,
        str
    ):

        # ----------------------------------------------------
        # 已经是JSON字符串时避免二次编码
        # ----------------------------------------------------

        try:

            parsed = json.loads(
                evidence
            )


            if isinstance(
                parsed,
                (list, dict)
            ):

                return json.dumps(

                    parsed,

                    ensure_ascii=False

                )


        except json.JSONDecodeError:

            pass


        evidence = [
            evidence
        ]


    return json.dumps(

        evidence,

        ensure_ascii=False

    )



# ============================================================
# Evidence反序列化
# ============================================================

def deserialize_evidence(
    evidence
):

    """
    将数据库Text中的JSON恢复成Python结构。
    """


    if evidence is None:

        return []


    if isinstance(
        evidence,
        (list, dict)
    ):

        return evidence


    if isinstance(
        evidence,
        str
    ):

        text = evidence.strip()


        if not text:

            return []


        try:

            return json.loads(
                text
            )


        except json.JSONDecodeError:

            return [
                text
            ]


    return evidence



# ============================================================
# Lead ORM -> Dict
# ============================================================

def lead_to_dict(
    lead: Lead
):

    """
    CRM统一数据结构。
    """


    return {

        "company":
            lead.company,

        "industry":
            lead.industry,

        "region":
            lead.region,

        "score":
            lead.score,

        "level":
            lead.level,

        "evidence":
            deserialize_evidence(
                lead.evidence
            ),

        "action":
            lead.action,

        "stage":
            lead.stage,

        "next_action":
            lead.next_action,

        "owner":
            lead.owner,

        "last_contact_time":
            (
                lead.last_contact_time.isoformat()

                if lead.last_contact_time

                else None
            ),

        "status":
            lead.status,

    }



# ============================================================
# 查询CRM客户
# ============================================================

@tool
def query_leads(
    industry: str = "",
    min_score: float = 0.0
):

    """
    查询CRM历史客户。

    支持父子行业兼容。

    Args:
        industry:
            行业名称。

        min_score:
            最低销售机会评分。

    Returns:
        CRM客户列表。
    """


    db = SessionLocal()


    try:

        query = db.query(
            Lead
        )


        min_score = float(
            min_score or 0.0
        )


        if min_score > 0:

            query = query.filter(

                Lead.score
                >=
                min_score

            )


        query = query.order_by(

            Lead.score.desc()

        )


        leads = query.all()



        if industry:

            leads = [

                lead

                for lead in leads

                if industry_matches(

                    industry,

                    lead.industry

                )

            ]



        return [

            lead_to_dict(
                lead
            )

            for lead in leads

        ]



    finally:

        db.close()



# ============================================================
# 创建CRM客户
# ============================================================

@tool
def create_lead(
    company: str,
    industry: str,
    region: str,
    score: float = 0.0,
    level: str = "",
    evidence: list[str] | None = None,
    action: str = "",
    next_action: str = "",
    owner: str = ""
):

    """
    创建新的CRM客户。


    新客户统一：

        stage = new
        status = new


    Reliability Rule：

    如果模型没有显式传入action，
    但已经生成了高质量next_action：

        action = next_action

    避免CRM出现：

        action = ""
        next_action = "完整销售动作"


    Args:
        company:
            企业名称。

        industry:
            企业真实行业。

        region:
            企业真实地区。

        score:
            商机评分。

        level:
            商机等级。

        evidence:
            商机证据列表。

        action:
            销售策略建议。

        next_action:
            下一步具体销售动作。

        owner:
            客户负责人。
    """


    # ========================================================
    # 参数标准化
    # ========================================================

    company = (
        company or ""
    ).strip()


    industry = (
        industry or ""
    ).strip()


    region = (
        region or ""
    ).strip()


    level = (
        level or ""
    ).strip()


    action = (
        action or ""
    ).strip()


    next_action = (
        next_action or ""
    ).strip()


    owner = (
        owner or ""
    ).strip()



    # ========================================================
    # 基础校验
    # ========================================================

    if not company:

        return {

            "success":
                False,

            "message":
                "企业名称不能为空",

        }


    if not industry:

        return {

            "success":
                False,

            "message":
                "企业行业不能为空",

            "company":
                company,

        }


    if not region:

        return {

            "success":
                False,

            "message":
                "企业地区不能为空",

            "company":
                company,

        }



    # ========================================================
    # Reliability Rule 1
    #
    # Action Fallback
    # ========================================================
    #
    # 模型常常会产生：
    #
    # next_action = "48小时内联系..."
    #
    # 但忘记填写：
    #
    # action
    #
    # 为避免CRM字段为空：
    #
    # action为空
    #     ↓
    # 使用next_action
    #
    # ========================================================

    if (
        not action
        and
        next_action
    ):

        action = next_action



    db = SessionLocal()


    try:

        # ====================================================
        # 防止重复创建
        # ====================================================

        existing = (

            db.query(Lead)

            .filter(
                Lead.company == company
            )

            .first()

        )


        if existing is not None:

            return {

                "success":
                    False,

                "already_exists":
                    True,

                "message":
                    "客户已存在",

                "lead":
                    lead_to_dict(
                        existing
                    ),

            }



        # ====================================================
        # 创建Lead
        # ====================================================

        new_lead = Lead(

            company=company,

            industry=industry,

            region=region,

            score=float(
                score or 0.0
            ),

            level=level,

            evidence=serialize_evidence(
                evidence
            ),

            action=action,

            stage="new",

            next_action=(
                next_action
                or
                None
            ),

            owner=(
                owner
                or
                None
            ),

            last_contact_time=None,

            status="new",

        )


        db.add(
            new_lead
        )


        db.commit()


        db.refresh(
            new_lead
        )



        return {

            "success":
                True,

            "created":
                True,

            "lead":
                lead_to_dict(
                    new_lead
                ),

        }



    except Exception:

        db.rollback()

        raise



    finally:

        db.close()



# ============================================================
# 更新客户销售阶段
# ============================================================

@tool
def update_lead_stage(
    company: str,
    stage: str,
    next_action: str = ""
):

    """
    更新已有CRM客户销售阶段。


    Reliability Rule：

    CRM销售阶段只能按合法生命周期推进。


    正常路径：

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


    任意进行中阶段都可以进入：

        lost


    同阶段更新是允许的：

        new → new
        qualified → qualified

    因为Agent可能只需要刷新next_action。
    """


    # ========================================================
    # 参数标准化
    # ========================================================

    company = (
        company or ""
    ).strip()


    stage = (
        stage or ""
    ).strip().lower()


    next_action = (
        next_action or ""
    ).strip()



    # ========================================================
    # 企业名称校验
    # ========================================================

    if not company:

        return {

            "success":
                False,

            "message":
                "企业名称不能为空",

        }



    # ========================================================
    # Stage名称校验
    # ========================================================

    if stage not in VALID_LEAD_STAGES:

        return {

            "success":
                False,

            "message":
                f"无效销售阶段: {stage}",

            "allowed_stages":
                sorted(
                    VALID_LEAD_STAGES
                ),

        }



    db = SessionLocal()


    try:

        # ====================================================
        # 查询客户
        # ====================================================

        lead = (

            db.query(Lead)

            .filter(
                Lead.company == company
            )

            .first()

        )



        # ====================================================
        # 客户不存在
        # ====================================================

        if lead is None:

            return {

                "success":
                    False,

                "message":
                    "客户不存在",

                "company":
                    company,

            }



        # ====================================================
        # 获取当前Stage
        # ====================================================

        previous_stage = (

            (
                lead.stage
                or
                "new"
            )
            .strip()
            .lower()

        )



        # ====================================================
        # 保护历史异常Stage
        # ====================================================

        if (
            previous_stage
            not in
            VALID_LEAD_STAGES
        ):

            return {

                "success":
                    False,

                "message":
                    "CRM当前销售阶段非法",

                "company":
                    company,

                "current_stage":
                    previous_stage,

                "requested_stage":
                    stage,

            }



        # ====================================================
        # Reliability Rule 2
        #
        # Stage Transition Guard
        # ====================================================

        allowed_next_stages = (
            ALLOWED_STAGE_TRANSITIONS[
                previous_stage
            ]
        )


        if stage not in allowed_next_stages:

            return {

                "success":
                    False,

                "transition_blocked":
                    True,

                "message":
                    (
                        "不允许跨越CRM销售生命周期阶段"
                    ),

                "company":
                    company,

                "previous_stage":
                    previous_stage,

                "requested_stage":
                    stage,

                "allowed_next_stages":
                    sorted(
                        allowed_next_stages
                    ),

                "next_action_preserved":
                    lead.next_action,

            }



        # ====================================================
        # 合法阶段更新
        # ====================================================

        lead.stage = stage



        # ====================================================
        # 更新next_action
        # ====================================================

        next_action_updated = False


        if next_action:

            lead.next_action = (
                next_action
            )

            next_action_updated = True



        # ====================================================
        # 修复历史action空值
        # ====================================================
        #
        # 之前已经存在：
        #
        # action = ""
        # next_action = "..."
        #
        # 的客户。
        #
        # 如果本次客户被更新，
        # 顺手进行自修复。
        # ====================================================

        if (
            not (
                lead.action
                or ""
            ).strip()
            and
            lead.next_action
        ):

            lead.action = (
                lead.next_action
            )



        # ====================================================
        # CRM记录状态
        # ====================================================

        lead.status = "updated"



        db.commit()


        db.refresh(
            lead
        )



        return {

            "success":
                True,

            "company":
                lead.company,

            "previous_stage":
                previous_stage,

            "stage":
                lead.stage,

            "stage_changed":
                previous_stage
                !=
                lead.stage,

            "next_action":
                lead.next_action,

            "next_action_updated":
                next_action_updated,

            "owner":
                lead.owner,

            "last_contact_time":
                (
                    lead.last_contact_time.isoformat()

                    if lead.last_contact_time

                    else None
                ),

            "status":
                lead.status,

        }



    except Exception:

        db.rollback()

        raise



    finally:

        db.close()