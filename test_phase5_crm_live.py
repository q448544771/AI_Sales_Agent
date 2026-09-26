"""
Phase 5.7.2 - Real CRM MCP Read-only Integration

Actual execution:
    CRM Agent
        -> LangChain MCP Adapter
        -> CRM MCP Client
        -> CRM MCP Server
        -> query_leads
        -> Existing CRM Database

No create_lead.
No update_lead_stage.
No message sending.

The input companies are Mock examples for integration testing.
"""

from app.multi_agent.crm_agent import run_crm


# ============================================================
# 1. Mock companies used only as lookup examples
# ============================================================

COMPANY_A = "华东精密汽车零部件有限公司"
COMPANY_B = "华南新能源汽车零部件有限公司"


def make_lead(company, evidence, score):

    return {
        "company": company,
        "purchase_intent_score": score,
        "opportunity_level": "高",
        "evidence": [evidence],
        "solution_match": [],
        "recommended_action": (
            "人工核实企业信息后，联系质量与自动化负责人，"
            "确认检测对象和实际采购计划。"
        ),
    }


def make_draft(company, evidence):

    return {
        "company": company,
        "entry_point": evidence,
        "evidence_refs": [evidence],
        "next_action": (
            "人工核实企业真实性和需求后，"
            "联系相关负责人确认检测对象、"
            "生产节拍及后续项目安排。"
        ),
        "draft_status": "mock_internal_only",
        "requires_human_review": True,
        "send_performed": False,
        "crm_write_performed": False,
    }


# ============================================================
# 2. Create a valid upstream state
# ============================================================

def create_test_state():

    evidence_a = "新增两条自动化生产线"
    evidence_b = "新增自动化装配与检测工位"

    leads = [
        make_lead(COMPANY_A, evidence_a, 0.80),
        make_lead(COMPANY_B, evidence_b, 0.75),
    ]

    drafts = [
        make_draft(COMPANY_A, evidence_a),
        make_draft(COMPANY_B, evidence_b),
    ]

    return {
        "goal": {
            "target_count": 2,
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "product_focus": "工业机器视觉质检解决方案",
        },

        "research_output": {
            "status": "complete",
            "data_mode": "mock_company_mcp",
        },

        "analysis_output": {
            "status": "complete",
            "selected_count": len(leads),
            "crm_stage_changed": False,
        },

        "candidate_leads": leads,

        "sales_output": {
            "status": "complete",
            "data_mode": "mock_company_mcp",
            "draft_count": len(drafts),
            "drafts": drafts,
            "requires_human_review": True,
            "send_performed": False,
            "crm_write_performed": False,
        },
    }


# ============================================================
# 3. Execute real CRM MCP read-only query
# ============================================================

def main():

    print("=" * 65)
    print("Phase 5.7.2 - CRM MCP Read-only Integration")
    print("=" * 65)

    state = create_test_state()

    print("\n[1] Connecting to real CRM MCP...")

    # No fake tool injected:
    # run_crm loads the real query_leads tool.
    result = run_crm(state)

    output = result["crm_output"]

    # ========================================================
    # 4. CRM statistics
    # ========================================================

    print("\n[2] CRM Statistics")

    print("Status:", output["status"])
    print("Mode:", output["mode"])
    print("Data Mode:", output["data_mode"])

    print("Query Count:", output["query_count"])
    print("Candidate Count:", output["candidate_count"])

    print("Existing Count:", output["existing_count"])
    print("Missing Count:", output["missing_count"])
    print("Duplicate Count:", output["duplicate_count"])

    print("Read Performed:", output["read_performed"])
    print("Create Performed:", output["create_performed"])
    print("Update Performed:", output["update_performed"])
    print("Stage Changed:", output["stage_changed"])

    print("Write Block Reason:", output["write_block_reason"])

    # ========================================================
    # 5. Show only the two requested candidate records
    # ========================================================

    print("\n[3] CRM Matching Results")

    for record in output["review_records"]:

        print("\n" + "-" * 55)

        print("Company:", record["company"])

        print("Lookup Status:", record["lookup_status"])

        print("Existing Stage:", record["existing_stage"])

        print(
            "Last Contact Time:",
            record["last_contact_time"],
        )

        print("Suggested Review:", record["suggested_review"])

        print("Action Taken:", record["action_taken"])

        print(
            "CRM Write Performed:",
            record["crm_write_performed"],
        )

        if record["lookup_status"] == "duplicate_records":

            print(
                "Duplicate Record Count:",
                record["duplicate_record_count"],
            )

    # ========================================================
    # 6. Reliability assertions
    # ========================================================

    print("\n[4] Reliability Assertions")

    expected_companies = {
        COMPANY_A,
        COMPANY_B,
    }

    returned_companies = {
        record["company"]
        for record in output["review_records"]
    }

    assert output["status"] in {
        "review_only",
        "manual_dedup_required",
    }

    assert output["mode"] == "read_only"

    assert output["data_mode"] == "mock_company_mcp"

    assert output["query_count"] == 1

    assert output["candidate_count"] == 2

    assert len(output["review_records"]) == 2

    assert returned_companies == expected_companies

    assert (
        output["existing_count"]
        + output["missing_count"]
        + output["duplicate_count"]
        == 2
    )

    assert output["read_performed"] is True

    assert output["create_performed"] is False

    assert output["update_performed"] is False

    assert output["stage_changed"] is False

    assert output["requires_human_review"] is True

    assert output["write_block_reason"] == "mock_company_data"

    assert all(
        record["action_taken"] == "none"
        and record["crm_write_performed"] is False
        for record in output["review_records"]
    )

    print("\nCRM MCP Connection: PASS")
    print("Read-only Query: PASS")
    print("Candidate Matching: PASS")
    print("Duplicate Detection Logic: PASS")
    print("Mock Data Write Restriction: PASS")
    print("No Create/Update Invocation: PASS")

    print("\n" + "=" * 65)
    print("Phase 5.7.2 Integration Test Passed")
    print("=" * 65)


if __name__ == "__main__":
    main()