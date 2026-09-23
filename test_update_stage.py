from app.tools.crm_tools import update_lead_stage



result = update_lead_stage.invoke(

    {
        "company":
        "华东精密汽车零部件有限公司",

        "stage":
        "meeting",

        "next_action":
        "安排机器视觉质检方案技术交流"

    }

)


print(result)