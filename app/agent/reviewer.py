import json


from app.llm.model import get_reasoning_llm


from app.models.review_schema import LeadAssessment





def review_node(state):


    """
    Reviewer Node

    对Executor收集的企业信息进行评估

    输出:
        candidate_leads

    支持多个企业批量进入Memory


    """



    llm = get_reasoning_llm()



    messages = state.get(
        "messages",
        []
    )



    prompt = f"""

你是一名B2B销售分析专家。


根据下面Agent调查过程中的全部信息，

筛选可能需要工业机器视觉质检方案的企业。


请完成:

1. 找出所有有购买潜力的企业

2. 根据扩产、自动化升级、
   机器视觉招聘、质量升级等信号
   评估购买意向

3. 输出Top 3潜在客户


调查记录:

{messages}



请严格输出JSON数组格式：

[

    {{
        "company":"",
        "purchase_intent_score":0.0,
        "opportunity_level":"",
        "evidence":[],
        "recommended_action":""

    }}

]



要求:

- purchase_intent_score范围0-1
- evidence必须列出具体购买信号
- recommended_action给出销售下一步动作
- 不要输出任何解释文字


"""



    response = llm.invoke(
        prompt
    )



    content = response.content.strip()



    # ==========================
    # JSON解析
    # ==========================

    try:


        data = json.loads(
            content
        )


    except Exception as e:


        print(
            "Reviewer JSON解析失败:"
        )

        print(content)


        raise e



    # ==========================
    # Pydantic批量校验
    # ==========================


    leads = []


    for item in data:


        result = LeadAssessment(
            **item
        )


        leads.append(
            result.model_dump()
        )



    print(
        f"Reviewer发现 {len(leads)} 个潜在客户"
    )



    return {


        "candidate_leads": leads,


        "status": "reviewed"

    }