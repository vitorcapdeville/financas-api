from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)


def get_session():
    """Dependency para obter sessão do banco de dados"""
    with Session(engine) as session:
        yield session
