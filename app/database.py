from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)


def create_db_and_tables():
    """Cria as tabelas no banco de dados"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency para obter sessão do banco de dados"""
    with Session(engine) as session:
        yield session
