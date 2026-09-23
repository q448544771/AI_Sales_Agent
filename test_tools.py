from app.tools.company_tools import search_companies


result = search_companies.invoke(
    {
        "industry":"汽车零部件",
        "region":"中国"
    }
)


print(result)