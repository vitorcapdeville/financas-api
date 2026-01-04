"""
Fixtures globais para testes.

Este arquivo contém fixtures compartilhadas por todos os testes:
- Banco de dados PostgreSQL de teste
- Cliente HTTP de teste
- Sessão de banco de dados
- Limpeza automática após cada teste
"""

import os
from datetime import datetime
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select, text

from app.database import get_session
from app.main import app
from app.models import TipoTransacao, Transacao
from app.models_config import Configuracao
from app.models_regra import CriterioTipo, Regra, RegraTag, TipoAcao
from app.models_tags import Tag, TransacaoTag
from alembic.config import Config
from alembic import command
from app.config import settings


@pytest.fixture(name="engine", scope="session")
def engine_fixture():
    """
    Cria engine PostgreSQL para testes e aplica migrações Alembic.

    Scope 'session' para reutilizar engine entre testes (performance).
    """
    # Criar engine
    engine = create_engine(settings.DATABASE_URL, echo=False)

    # Configurar e rodar migrações Alembic
    alembic_cfg = Config("alembic.ini")
    
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    yield engine

    # Limpar todas as tabelas ao final da sessão
    command.downgrade(alembic_cfg, "base")
    engine.dispose()


@pytest.fixture(name="session", autouse=True)
def session_fixture(engine) -> Generator[Session, None, None]:
    """
    Cria sessão de banco de dados para cada teste.

    Cada teste recebe uma sessão limpa e isolada.
    Usa transação que é revertida após o teste (rollback).
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


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
def reset_database():
    """
    Reseta completamente o banco de dados antes de cada teste.

    Usa alembic downgrade base + upgrade head para garantir
    schema limpo sem problemas de transação.
    """
    alembic_cfg = Config("alembic.ini")
    # Desfaz todas as migrações (drop all tables)
    command.downgrade(alembic_cfg, "base")
    # Reaplica todas as migrações (recreate all tables)
    command.upgrade(alembic_cfg, "head")

    yield  # Executa o teste
