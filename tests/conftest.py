"""
Fixtures globais para testes.

Este arquivo contém fixtures compartilhadas por todos os testes:
- Banco de dados em memória (SQLite)
- Cliente HTTP de teste
- Sessão de banco de dados
- Limpeza automática após cada teste
"""

import os
from typing import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import Transacao, TipoTransacao
from app.models_config import Configuracao
from app.models_tags import Tag, TransacaoTag
from app.models_regra import Regra, RegraTag, TipoAcao, CriterioTipo


# Configurar variáveis de ambiente para testes
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture(name="engine")
def engine_fixture():
    """
    Cria engine SQLite em memória para testes.
    
    Usa StaticPool para manter a conexão aberta durante toda a sessão de teste.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine) -> Generator[Session, None, None]:
    """
    Cria sessão de banco de dados para cada teste.
    
    Cada teste recebe uma sessão limpa e isolada.
    Após o teste, faz rollback para garantir isolamento.
    """
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """
    Cria cliente HTTP de teste.
    
    Override da dependency get_session para usar sessão de teste.
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="transacao_basica")
def transacao_basica_fixture(session: Session) -> Transacao:
    """
    Cria uma transação básica para testes.
    
    Útil para testes que precisam de uma transação existente.
    """
    transacao = Transacao(
        data=datetime(2024, 1, 15).date(),
        descricao="Compra no supermercado",
        valor=150.50,
        tipo=TipoTransacao.SAIDA,
        categoria="Alimentação",
        origem="manual",
    )
    session.add(transacao)
    session.commit()
    session.refresh(transacao)
    return transacao


@pytest.fixture(name="tag_basica")
def tag_basica_fixture(session: Session) -> Tag:
    """
    Cria uma tag básica para testes.
    """
    tag = Tag(
        nome="Essencial",
        cor="#FF5733",
        descricao="Gastos essenciais",
    )
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@pytest.fixture(name="regra_basica")
def regra_basica_fixture(session: Session) -> Regra:
    """
    Cria uma regra básica para testes.
    """
    regra = Regra(
        nome="Categorizar supermercado",
        tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
        criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
        criterio_valor="supermercado",
        acao_valor="Alimentação",
        prioridade=1,
        ativo=True,
    )
    session.add(regra)
    session.commit()
    session.refresh(regra)
    return regra


@pytest.fixture(name="configuracao_basica")
def configuracao_basica_fixture(session: Session) -> Configuracao:
    """
    Cria configurações básicas para testes.
    """
    configs = [
        Configuracao(chave="diaInicioPeriodo", valor="1"),
        Configuracao(chave="criterio_data_transacao", valor="data_transacao"),
    ]
    for config in configs:
        session.add(config)
    session.commit()
    return configs[0]


@pytest.fixture(autouse=True)
def reset_database(session: Session):
    """
    Limpa o banco de dados antes de cada teste.
    
    autouse=True faz com que esta fixture seja executada automaticamente.
    """
    # Deletar dados em ordem para respeitar FKs
    session.exec(select(RegraTag)).all()
    for item in session.exec(select(RegraTag)).all():
        session.delete(item)
    
    session.exec(select(TransacaoTag)).all()
    for item in session.exec(select(TransacaoTag)).all():
        session.delete(item)
    
    for transacao in session.exec(select(Transacao)).all():
        session.delete(transacao)
    
    for tag in session.exec(select(Tag)).all():
        session.delete(tag)
    
    for regra in session.exec(select(Regra)).all():
        session.delete(regra)
    
    for config in session.exec(select(Configuracao)).all():
        session.delete(config)
    
    session.commit()
