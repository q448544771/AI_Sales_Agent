import json

from app.database.db import SessionLocal
from app.database.models import Lead



def memory_node(state):

    """
    Memory Node

    将Reviewer产生的多个Lead保存到CRM数据库

    已存在:
        更新客户信息

    不存在:
        新增客户

    """

    leads = state.get(
        "candidate_leads",
        []
    )


    if not leads:

        return {

            "memory_saved":0,

            "status":"no leads"

        }



    db = SessionLocal()


    saved_count = 0


    try:


        for lead_data in leads:


            company = lead_data.get(
                "company"
            )


            if not company:

                continue



            # =====================
            # 查询已有客户
            # =====================

            existing = (

                db.query(Lead)

                .filter(
                    Lead.company == company
                )

                .first()

            )



            evidence = json.dumps(

                lead_data.get(
                    "evidence",
                    []
                ),

                ensure_ascii=False

            )



            score = lead_data.get(

                "purchase_intent_score",

                0

            )



            level = lead_data.get(

                "opportunity_level",

                ""

            )



            action = lead_data.get(

                "recommended_action",

                ""

            )



            # =====================
            # 已存在 -> 更新
            # =====================

            if existing:


                print(
                    f"更新已有客户: {company}"
                )


                existing.score = score

                existing.level = level

                existing.evidence = evidence

                existing.action = action

                existing.status = "updated"



            # =====================
            # 不存在 -> 新增
            # =====================

            else:


                print(
                    f"新增客户: {company}"
                )


                new_lead = Lead(

                    company=company,

                    industry=
                    state["goal"].target_industry,


                    region=
                    state["goal"].target_region,


                    score=score,

                    level=level,

                    evidence=evidence,

                    action=action,

                    status="new"

                )


                db.add(
                    new_lead
                )



            saved_count += 1



        db.commit()



    except Exception as e:


        db.rollback()

        raise e



    finally:


        db.close()



    return {

        "memory_saved":saved_count,

        "status":"success"

    }