from app.database.db import SessionLocal
from app.database.models import Lead



db = SessionLocal()


leads = db.query(Lead).all()


for lead in leads:

    print(
        lead.company
    )

    print(
        lead.stage
    )

    print(
        lead.next_action
    )



db.close()