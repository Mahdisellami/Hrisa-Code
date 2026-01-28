from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

def init_db():
    engine = create_engine('sqlite:///tasks.db')
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)