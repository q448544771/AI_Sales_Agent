from pydantic import BaseModel, Field



class LeadAssessment(BaseModel):

    company: str


    purchase_intent_score: float = Field(
        description="购买意向评分0-1"
    )


    opportunity_level: str


    evidence: list[str]


    recommended_action: str