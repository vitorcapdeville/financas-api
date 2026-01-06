"""
Configuração global de fixtures para testes
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool


@pytest.fixture
def mock_session():
    """Mock de sessão do banco de dados"""
    return Mock()


@pytest.fixture
def data_exemplo():
    """Data de exemplo para testes"""
    return date(2026, 1, 15)


@pytest.fixture
def datetime_exemplo():
    """Datetime de exemplo para testes"""
    return datetime(2026, 1, 15, 10, 30, 0)


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture para testes de integração com banco de dados SQLite em memória.
    Cada teste recebe uma sessão limpa e isolada.
    """
    # Importar todos os modelos para que SQLModel.metadata seja populado
    from app.infrastructure.database.models.transacao_model import TransacaoModel  # noqa: F401
    from app.infrastructure.database.models.tag_model import TagModel  # noqa: F401
    from app.infrastructure.database.models.regra_model import RegraModel  # noqa: F401
    from app.infrastructure.database.models.configuracao_model import ConfiguracaoModel  # noqa: F401

    # Criar engine em memória com pool estático para evitar problemas de concorrência
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Criar todas as tabelas
    SQLModel.metadata.create_all(engine)

    # Criar sessão
    with Session(engine) as session:
        yield session
        session.rollback()  # Reverter qualquer mudança após o teste

    # Limpar metadata
    SQLModel.metadata.drop_all(engine)
    engine.dispose()
