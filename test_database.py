from app.tools.database_tools import (
    save_lead,
    query_lead
)



result = save_lead(

    company="华东精密汽车零部件有限公司",

    industry="汽车零部件",

    region="江苏",

    score=0.93,

    level="高",

    evidence=[
        "新增自动化生产线",
        "招聘机器视觉工程师"
    ],

    action="联系质量部门"

)


print(result)



print(
    query_lead(
        "华东精密汽车零部件有限公司"
    )
)
