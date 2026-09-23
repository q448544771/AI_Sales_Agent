from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker



DATABASE_URL = "sqlite:///sales_agent.db"



engine = create_engine(
    DATABASE_URL,
    echo=True
)



SessionLocal = sessionmaker(
    bind=engine
)



def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()
