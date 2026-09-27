"""Phase 7.6 - Full real five-agent LangGraph integration.

Supervisor:

    Verified Discovery
        -> Real Research
        -> Knowledge MCP
        -> Evidence-grounded Analysis
        -> Source-backed Sales
        -> Read-only Real CRM

No mock fallback.
No CRM create/update.
No outbound messaging.
"""

from app.graph.multi_workflow import (
    create_multi_graph,
)

from app.multi_agent.contracts import (
    AGENT_SEQUENCE,
)

from app.multi_agent.real_research_agent import (
    real_research_agent_node,
)

from app.multi_agent.knowledge_agent import (
    knowledge_agent_node,
)

from app.multi_agent.real_analysis_agent import (
    real_analysis_agent_node,
)

from app.multi_agent.real_sales_agent import (
    real_sales_agent_node,
    DRAFT_BANNER,
)

from app.multi_agent.real_crm_agent import (
    real_crm_agent_node,
    capture_crm_snapshot,
)


# ============================================================
# Graph
# ============================================================

def create_phase7_graph():

    return create_multi_graph({

        "research":
            real_research_agent_node,

        "knowledge":
            knowledge_agent_node,

        "analysis":
            real_analysis_agent_node,

        "sales":
            real_sales_agent_node,

        "crm":
            real_crm_agent_node,

    })


# ============================================================
# Initial State
# ============================================================

def initial_state():

    return {

        "goal": {

            "product_focus":
                "工业机器视觉质检解决方案",

            "target_industry":
                "汽车零部件",

            "target_region":
                "中国",

            "target_count":
                1,

            "user_requirement":

                (
                    "寻找经过企业身份验证的真实企业;"
                    "必须基于原始网页证据;"
                    "只允许literal quote作为分析依据;"
                    "生成内部审核销售草稿;"
                    "CRM仅允许只读重复匹配。"
                ),

        },


        "status":
            "planning",


        "completed_agents":
            [],


        "supervisor_turns":
            0,


        "max_supervisor_turns":
            12,

    }


# ============================================================
# Verify Result
# ============================================================

def verify_final_state(result):


    print("\n[3] Verify Supervisor Completion")


    completed = list(
        result.get(
            "completed_agents"
        ) or []
    )


    print(
        "Completed Agents:",
        completed,
    )


    assert completed == list(
        AGENT_SEQUENCE
    ), (
        "Supervisor did not complete expected sequence"
    )



    # ========================================================
    # Research
    # ========================================================

    research = result[
        "research_output"
    ]


    assert research[
        "data_mode"
    ] == "real_source_page"


    assert research[
        "mock_fallback_used"
    ] is False


    assert research[
        "verified_company_count"
    ] >= 1


    assert research[
        "verified_evidence_count"
    ] >= 1


    assert research[
        "crm_write_performed"
    ] is False


    assert research[
        "send_performed"
    ] is False


    print(
        "Verified Research Evidence:",
        research[
            "verified_evidence_count"
        ],
    )



    # ========================================================
    # Knowledge
    # ========================================================

    knowledge = result[
        "knowledge_output"
    ]


    assert knowledge[
        "source_type"
    ] == "internal_product_knowledge"


    assert knowledge[
        "document_count"
    ] >= 1


    print(
        "Knowledge Documents:",
        knowledge[
            "document_count"
        ],
    )



    # ========================================================
    # Analysis
    # ========================================================

    analysis = result[
        "analysis_output"
    ]


    assert analysis[
        "data_mode"
    ] == "real_source_page"


    if "evidence_contract_passed" in analysis:

        assert analysis[
            "evidence_contract_passed"
        ] is True



    assert analysis[
        "selected_count"
    ] >= 1


    assert analysis[
        "selected_count"
    ] == len(
        analysis[
            "assessments"
        ]
    )


    assert analysis[
        "crm_stage_changed"
    ] is False


    assert analysis[
        "crm_write_performed"
    ] is False


    assert analysis[
        "send_performed"
    ] is False


    assert result[
        "candidate_leads"
    ] == []


    print(
        "Analysis Assessments:",
        analysis[
            "selected_count"
        ],
    )



    # ========================================================
    # Sales
    # ========================================================

    sales = result[
        "sales_output"
    ]


    assert sales[
        "data_mode"
    ] == "real_source_page"


    if "evidence_contract_passed" in sales:

        assert sales[
            "evidence_contract_passed"
        ] is True



    assert sales[
        "status"
    ] == "complete"


    assert sales[
        "draft_count"
    ] >= 1


    assert sales[
        "draft_count"
    ] == len(
        sales[
            "drafts"
        ]
    )


    assert sales[
        "send_performed"
    ] is False


    assert sales[
        "crm_write_performed"
    ] is False



    print(
        "Internal Sales Drafts:",
        sales[
            "draft_count"
        ],
    )



    original_evidence = research[
        "verified_evidence"
    ]



    for draft in sales[
        "drafts"
    ]:


        assert draft[
            "draft_status"
        ] == (
            "real_internal_review_only"
        )


        assert draft[
            "requires_human_review"
        ] is True


        assert draft[
            "send_performed"
        ] is False


        assert draft[
            "crm_write_performed"
        ] is False


        assert DRAFT_BANNER in draft[
            "outreach_draft"
        ]



        assert draft[
            "entry_point"
        ] in original_evidence



    # ========================================================
    # CRM
    # ========================================================

    crm = result[
        "crm_output"
    ]


    assert crm[
        "data_mode"
    ] in (
        "real_source_page",
        "real_crm_read_only",
    )


    assert crm[
        "mode"
    ] == "read_only"


    assert crm[
        "candidate_count"
    ] == analysis[
        "selected_count"
    ]


    assert crm[
        "query_count"
    ] == 1


    assert crm[
        "read_performed"
    ] is True


    assert crm[
        "create_performed"
    ] is False


    assert crm[
        "update_performed"
    ] is False


    assert crm[
        "stage_changed"
    ] is False


    assert crm[
        "send_performed"
    ] is False


    assert crm[
        "requires_human_review"
    ] is True


    assert crm[
        "write_block_reason"
    ] == (
        "no_explicit_write_authorization"
    )


    print(
        "CRM Candidates:",
        crm[
            "candidate_count"
        ],
    )


    return crm



# ============================================================
# Main
# ============================================================

def main():


    print("=" * 68)

    print(
        "Phase 7.6 - Five Real Agents Integration"
    )

    print("=" * 68)



    print(
        "\n[1] CRM Snapshot Before Execution"
    )


    before = capture_crm_snapshot()


    print(
        "CRM Rows:",
        before[
            "row_count"
        ],
    )


    print(
        "CRM SHA256:",
        before[
            "sha256"
        ],
    )



    print(
        "\n[2] Running Five-Agent LangGraph..."
    )


    graph = create_phase7_graph()


    final_result = None

    crm = None



    try:

        # ----------------------------------------------------
        # Phase 7.6 Research Contract Precheck
        # ----------------------------------------------------
        # Verify that the real research agent returns the
        # expected state payload before entering LangGraph.
        preview_state = initial_state()

        research_preview = real_research_agent_node(
            preview_state
        )

        if not isinstance(research_preview, dict):
            raise TypeError(
                "Research agent must return dict"
            )

        if "research_output" not in research_preview:
            raise ValueError(
                "Research agent missing research_output"
            )

        if (
            "company_records"
            not in research_preview["research_output"]
        ):
            raise ValueError(
                "research_output missing company_records"
            )

        print(
            "Research Contract Precheck: PASS"
        )

        print(
            "Research Preview Records:",
            len(
                research_preview["research_output"]
                ["company_records"]
            ),
        )

        final_result = graph.invoke(

            initial_state(),

            config={
                "recursion_limit": 35,
            },

        )


        crm = verify_final_state(
            final_result
        )


    finally:


        print(
            "\n[5] CRM Snapshot After Execution"
        )


        after = capture_crm_snapshot()


        print(
            "CRM Rows:",
            after[
                "row_count"
            ],
        )


        print(
            "CRM SHA256:",
            after[
                "sha256"
            ],
        )


        assert before == after, (

            "CRM query-result snapshot changed "
            "during Phase 7.6 execution."

        )


        print(
            "CRM Query Snapshot Unchanged: PASS"
        )



    assert crm is not None


    assert crm[
        "crm_query_snapshot_sha256"
    ] == before[
        "sha256"
    ]



    print("\n" + "=" * 68)

    print(
        "Phase 7.6 Five Real Agents Integration Passed"
    )

    print("=" * 68)



    print(
        "\nVerification Summary:"
    )


    print(
        "Real Research: PASS"
    )

    print(
        "Knowledge MCP: PASS"
    )

    print(
        "Real Analysis: PASS"
    )

    print(
        "Real Sales: PASS"
    )

    print(
        "Read-only CRM: PASS"
    )

    print(
        "Supervisor Routing: PASS"
    )

    print(
        "Source URL Provenance: PASS"
    )

    print(
        "No Mock Fallback: PASS"
    )

    print(
        "No External Sending: PASS"
    )

    print(
        "No CRM Create / Update: PASS"
    )

    print(
        "CRM Query Snapshot Unchanged: PASS"
    )



if __name__ == "__main__":

    main()