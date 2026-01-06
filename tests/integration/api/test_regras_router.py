"""
Testes de API para o router de regras
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def client():
    """Cliente de teste FastAPI com banco em memória"""
    # Importar modelos
    from app.infrastructure.database.models.transacao_model import TransacaoModel  # noqa
    from app.infrastructure.database.models.tag_model import TagModel  # noqa
    from app.infrastructure.database.models.regra_model import RegraModel  # noqa
    from app.infrastructure.database.models.configuracao_model import ConfiguracaoModel  # noqa
    
    # Criar engine em memória
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Criar tabelas
    SQLModel.metadata.create_all(test_engine)
    
    # Override do engine
    def override_get_session():
        with Session(test_engine) as session:
            yield session
    
    from app.infrastructure.database.session import get_session
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Limpar
    SQLModel.metadata.drop_all(test_engine)
    app.dependency_overrides.clear()


class TestRegrasRouter:
    """Testes para o router de regras"""
    
    def test_criar_regra(self, client):
        """Deve criar uma regra"""
        response = client.post("/regras", json={
            "nome": "Regra Teste",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "supermercado",
            "acao_valor": "Alimentação",
            "ativo": True,
            "prioridade": 100
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Regra Teste"
        assert data["criterio_tipo"] == "descricao_contem"
    
    def test_listar_regras(self, client):
        """Deve listar regras ordenadas"""
        # Criar regras
        client.post("/regras", json={
            "nome": "Regra 1",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste1",
            "acao_valor": "Cat1",
            "prioridade": 100
        })
        client.post("/regras", json={
            "nome": "Regra 2",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste2",
            "acao_valor": "Cat2",
            "prioridade": 50
        })
        
        response = client.get("/regras")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        # Verificar ordenação por prioridade (maior primeiro)
        prioridades = [r["prioridade"] for r in data]
        assert prioridades == sorted(prioridades, reverse=True)
    
    def test_obter_regra_por_id(self, client):
        """Deve obter uma regra por ID"""
        # Criar regra
        create_response = client.post("/regras", json={
            "nome": "Regra Obter",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste",
            "acao_valor": "Teste",
            "prioridade": 100
        })
        regra_id = create_response.json()["id"]
        
        # Obter regra
        response = client.get(f"/regras/{regra_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == regra_id
        assert data["nome"] == "Regra Obter"
    
    def test_obter_regra_inexistente_retorna_404(self, client):
        """Deve retornar 404 para regra inexistente"""
        response = client.get("/regras/999")
        
        assert response.status_code == 404
    
    def test_atualizar_regra(self, client):
        """Deve atualizar uma regra"""
        # Criar regra
        create_response = client.post("/regras", json={
            "nome": "Regra Original",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste",
            "acao_valor": "Original",
            "prioridade": 100
        })
        regra_id = create_response.json()["id"]
        
        # Atualizar regra
        response = client.patch(f"/regras/{regra_id}", json={
            "nome": "Regra Atualizada",
            "acao_valor": "Atualizada"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Regra Atualizada"
        assert data["acao_valor"] == "Atualizada"
    
    def test_deletar_regra(self, client):
        """Deve deletar uma regra"""
        # Criar regra
        create_response = client.post("/regras", json={
            "nome": "Regra Deletar",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste",
            "acao_valor": "Teste",
            "prioridade": 100
        })
        regra_id = create_response.json()["id"]
        
        # Deletar regra
        response = client.delete(f"/regras/{regra_id}")
        
        assert response.status_code == 204
        
        # Verificar que foi deletada
        get_response = client.get(f"/regras/{regra_id}")
        assert get_response.status_code == 404
