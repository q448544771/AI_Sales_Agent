from app.tools.company_tools_old import search_companies


result = search_companies.invoke(
    {
        "industry":"汽车零部件",
        "region":"中国"
    }
)


print(result)