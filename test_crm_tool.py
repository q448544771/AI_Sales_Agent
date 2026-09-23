from app.tools.crm_tools import query_leads


result = query_leads.invoke(
    {
        "industry":"汽车零部件",
        "min_score":0.8
    }
)


print(result)