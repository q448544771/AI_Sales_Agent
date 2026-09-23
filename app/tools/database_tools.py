import json


from app.database.db import SessionLocal

from app.database.models import Lead



def save_lead(
    company: str,
    industry: str,
    region: str,
    score: float,
    level: str,
    evidence: list,
    action: str
):

    """
    保存销售线索
    """


    db = SessionLocal()


    lead = Lead(

        company=company,

        industry=industry,

        region=region,

        score=score,

        level=level,

        evidence=json.dumps(
            evidence,
            ensure_ascii=False
        ),

        action=action,

        status="new"

    )


    db.add(lead)


    db.commit()


    db.close()


    return {

        "status":"success",

        "company":company

    }



def query_lead(
    company:str
):

    """
    查询历史客户
    """


    db = SessionLocal()


    result = db.query(
        Lead
    ).filter(
        Lead.company==company
    ).first()


    db.close()


    if result:

        return {

            "exists":True,

            "company":result.company,

            "score":result.score,

            "status":result.status

        }


    return {

        "exists":False,

        "company":company

    }


def get_lead(company):

    """
    根据公司名称查询客户
    """

    db = SessionLocal()

    try:

        lead = (
            db.query(Lead)
            .filter(
                Lead.company == company
            )
            .first()
        )


        if lead:

            return {
                "exists": True,
                "id": lead.id,
                "company": lead.company,
                "score": lead.score,
                "status": lead.status
            }


        return {
            "exists": False
        }


    finally:

        db.close()


def update_lead(
    company,
    score,
    level,
    evidence,
    action
):


    db = SessionLocal()


    try:


        lead = (
            db.query(Lead)
            .filter(
                Lead.company == company
            )
            .first()
        )


        if not lead:

            return {
                "status":"not_found"
            }



        lead.score = score

        lead.level = level

        lead.evidence = json.dumps(
            evidence,
            ensure_ascii=False
        )


        lead.action = action


        lead.status="updated"



        db.commit()



        return {

            "status":"updated",

            "company":company

        }


    finally:

        db.close()