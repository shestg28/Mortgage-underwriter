from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_database_url
from app.models.base import Base

DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
