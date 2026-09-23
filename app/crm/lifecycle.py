LEAD_STAGES = [

    "new",

    "contacted",

    "qualified",

    "meeting",

    "proposal",

    "negotiation",

    "won",

    "lost"

]



def validate_stage(stage):

    return stage in LEAD_STAGES



def next_stage(current):


    mapping = {


        "new":
        "contacted",


        "contacted":
        "qualified",


        "qualified":
        "meeting",


        "meeting":
        "proposal",


        "proposal":
        "negotiation",


        "negotiation":
        "won"

    }


    return mapping.get(
        current
    )