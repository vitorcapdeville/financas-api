from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)


def create_db_and_tables():
    """Cria as tabelas no banco de dados"""
    # Importar todos os modelos para que o SQLModel os reconheça
    from app.models import Transacao  # noqa: F401
    from app.models_config import Configuracao  # noqa: F401
    
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency para obter sessão do banco de dados"""
    with Session(engine) as session:
        yield session
