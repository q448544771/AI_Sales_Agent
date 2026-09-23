from app.database.db import SessionLocal
from app.database.models import Lead



def generate_followup_action(
    stage,
    score,
    evidence
):
    """
    根据客户生命周期生成下一步销售动作
    """

    if stage == "new":

        return (
            "收集企业基础信息，"
            "确认产品类型、生产工艺以及当前质量检测方式，"
            "寻找质量部门或智能制造负责人。"
        )


    elif stage == "qualified":

        return (
            "48小时内联系客户技术负责人，"
            "围绕自动化产线和视觉质检需求开展技术交流，"
            "准备行业案例和POC验证方案。"
        )


    elif stage == "contacted":

        return (
            "7天内进行二次跟进，"
            "确认客户当前检测痛点、预算周期以及项目推进计划。"
        )


    elif stage == "meeting":

        return (
            "准备技术方案和报价，"
            "进一步确认检测目标、产品节拍、缺陷类型以及部署环境。"
        )


    else:

        return (
            "持续跟踪客户业务变化，"
            "监控新增产线、招聘和采购信号。"
        )





def followup_node(state):

    """
    CRM Follow-up Agent节点

    读取CRM客户
    生成下一步动作
    更新数据库
    """


    db = SessionLocal()


    updated = 0


    try:

        leads = db.query(Lead).all()


        for lead in leads:


            next_action = generate_followup_action(
                lead.stage,
                lead.score,
                lead.evidence
            )


            lead.next_action = next_action


            updated += 1



        db.commit()



    finally:

        db.close()



    return {

        "followup_updated": updated,

        "status":"followup_completed"

    }