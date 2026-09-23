from langchain_core.tools import tool


from app.database.db import SessionLocal

from app.database.models import Lead





@tool
def query_leads(

    industry: str = "",

    min_score: float = 0.0

):

    """

    查询历史CRM销售客户。


    使用场景：

    1.
    用户希望查看已有客户


    2.
    判断某个行业是否已经研究过


    3.
    避免重复搜索已经发现的企业


    4.
    获取历史销售线索以及跟进建议



    参数:


    industry:

        行业过滤


    min_score:

        最低购买意向评分



    返回:


    历史客户列表：

    - 企业名称
    - 行业
    - 地区
    - 购买意向评分
    - 历史证据
    - 销售建议
    - 当前状态


    """



    db = SessionLocal()



    try:



        query = db.query(
            Lead
        )



        if industry:



            query = query.filter(

                Lead.industry == industry

            )




        if min_score:



            query = query.filter(

                Lead.score >= min_score

            )




        leads = query.all()



        result = []



        for lead in leads:



            result.append(

                {


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
                    lead.evidence,


                    "action":
                    lead.action,


                    "status":
                    lead.status

                }

            )



        return result




    finally:



        db.close()

@tool
def update_lead_stage(
    company:str,
    stage:str,
    next_action:str=""
):

    """
    更新客户销售阶段
    """

    db = SessionLocal()


    try:

        lead = (
            db.query(Lead)
            .filter(
                Lead.company==company
            )
            .first()
        )


        if not lead:

            return {
                "success":False,
                "message":"客户不存在"
            }



        lead.stage = stage


        if next_action:

            lead.next_action = next_action



        db.commit()


        return {

            "success":True,

            "company":company,

            "stage":stage

        }


    finally:

        db.close()