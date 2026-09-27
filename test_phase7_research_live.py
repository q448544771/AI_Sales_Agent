"""
Phase 7.3 - Real Research Agent Live Integration

Pipeline:

Discovery
    ->
Company Verification
    ->
Original Source Verification
    ->
Verified Evidence

No Mock.
No CRM.
No Sending.
"""

from app.multi_agent.real_research_agent import (
    run_real_research,
)


def main():

    print("=" * 65)
    print("Phase 7.3 - Real Research Agent Integration")
    print("=" * 65)


    state = {

        "goal": {

            "target_industry":
                "汽车零部件",

            "target_region":
                "中国",

            "target_count":
                3,
        }

    }


    print("\n[1] Running Real Research Agent...")


    result = run_real_research(
        state
    )


    output = result.get(
        "research_output",
        {}
    )


    print("\n[2] Research Statistics")


    print(
        "Status:",
        output.get(
            "status"
        )
    )


    print(
        "Data Mode:",
        output.get(
            "data_mode"
        )
    )


    print(
        "Discovered Companies:",
        output.get(
            "discovered_company_count"
        )
    )


    print(
        "Identity Verified Companies:",
        output.get(
            "identity_verified_company_count",
            0
        )
    )


    print(
        "Researched Companies:",
        output.get(
            "researched_company_count"
        )
    )


    print(
        "Verified Companies:",
        output.get(
            "verified_company_count"
        )
    )


    print(
        "Evidence Count:",
        output.get(
            "verified_evidence_count"
        )
    )


    print(
        "Mock Fallback:",
        output.get(
            "mock_fallback_used"
        )
    )


    print("\n[3] Company Records")


    for company in output.get(
        "company_records",
        []
    ):

        print("\n------------------------------")

        print(
            "Company:",
            company.get(
                "company"
            )
        )


        print(
            "Identity:",
            company.get(
                "identity_status"
            )
        )


        print(
            "Evidence:",
            company.get(
                "evidence_count"
            )
        )


        verification = company.get(
            "company_verification"
        )


        if verification:

            print(
                "Company Verification:",
                verification.get(
                    "verification_status"
                )
            )


        for evidence in company.get(
            "verified_evidence",
            []
        ):

            print(
                "\nQuote:"
            )

            print(
                evidence.get(
                    "quote"
                )
            )

            print(
                "URL:",
                evidence.get(
                    "source_url"
                )
            )


    print("\n[4] Reliability Assertions")


    assert output.get(
        "mock_fallback_used"
    ) is False


    assert output.get(
        "crm_write_performed"
    ) is False


    assert output.get(
        "send_performed"
    ) is False


    print(
        "No Mock Data: PASS"
    )

    print(
        "No CRM Write: PASS"
    )

    print(
        "No Message Sending: PASS"
    )


    print("\n================================================")
    print("Phase 7.3 Real Research Integration Passed")
    print("================================================")


if __name__ == "__main__":

    main()