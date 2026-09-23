from langchain_core.tools import tool


@tool
def search_companies(
    industry: str,
    region: str
):
    """
    根据行业和地区搜索潜在企业。

    用于发现可能存在销售机会的候选客户。
    """

    companies = [
        {
            "name": "华东精密汽车零部件有限公司",
            "industry": "汽车零部件",
            "region": "江苏",
            "signals": [
                "新能源车零部件扩产",
                "新增自动化产线"
            ]
        },
        {
            "name": "南方汽车电子科技有限公司",
            "industry": "汽车电子",
            "region": "广东",
            "signals": [
                "智能工厂建设",
                "招聘自动化工程师"
            ]
        },
        {
            "name": "中部汽车结构件制造有限公司",
            "industry": "汽车零部件",
            "region": "湖北",
            "signals": [
                "新建生产基地",
                "质量检测升级"
            ]
        }
    ]


    filtered = [
        c for c in companies
        if industry in c["industry"]
        or c["industry"] in industry
    ]

    return filtered



@tool
def search_company_news(
    company: str
):
    """
    查询企业近期新闻和业务动态。

    用于判断企业是否存在扩产、
    新建产线、智能制造升级等购买信号。
    """

    news = {

        "华东精密汽车零部件有限公司":
        [
            "2026年投资5亿元建设新能源汽车零部件生产基地",
            "新增两条自动化生产线",
            "计划提升智能制造水平"
        ],


        "南方汽车电子科技有限公司":
        [
            "启动智能制造升级项目",
            "建设数字化生产车间"
        ],


        "中部汽车结构件制造有限公司":
        [
            "新工厂正式投产",
            "质量检测能力升级"
        ]

    }


    return news.get(
        company,
        []
    )



@tool
def search_company_jobs(
    company: str
):
    """
    查询企业招聘信息。

    用于判断企业是否正在建设
    自动化、视觉检测、质量团队。
    """

    jobs = {

        "华东精密汽车零部件有限公司":
        [
            "机器视觉工程师",
            "自动化工程师",
            "质量工程师"
        ],


        "南方汽车电子科技有限公司":
        [
            "视觉算法工程师",
            "自动化设备工程师"
        ],


        "中部汽车结构件制造有限公司":
        [
            "质量工程师",
            "生产工艺工程师"
        ]

    }


    return jobs.get(
        company,
        []
    )