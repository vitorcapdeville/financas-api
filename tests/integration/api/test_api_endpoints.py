"""
Testes de integração para API de Tags

Objetivo: Testar endpoints da API usando TestClient do FastAPI
Nota: Usa banco de dados em memória (SQLite)
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


@pytest.mark.integration
class TestTagsAPI:
    """Testes de integração para endpoints de tags"""
    
    def test_listar_tags_retorna_200(self, client):
        """
        ARRANGE: Cliente HTTP configurado
        ACT: Fazer GET /tags
        ASSERT: Verificar status 200 e estrutura da resposta
        """
        # Act
        response = client.get("/tags")
        
        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_criar_tag_valida_retorna_201(self, client):
        """Testa criação de tag válida"""
        # Arrange
        tag_data = {"nome": "Tag Teste Integração"}
        
        # Act
        response = client.post("/tags", json=tag_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Tag Teste Integração"
        assert "id" in data
        
        # Cleanup
        tag_id = data["id"]
        client.delete(f"/tags/{tag_id}")
    
    def test_criar_tag_nome_vazio_retorna_422(self, client):
        """Testa que criar tag com nome vazio retorna erro de validação"""
        # Arrange
        tag_data = {"nome": ""}
        
        # Act
        response = client.post("/tags", json=tag_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_obter_tag_inexistente_retorna_404(self, client):
        """Testa que buscar tag inexistente retorna 404"""
        # Act
        response = client.get("/tags/99999")
        
        # Assert
        assert response.status_code == 404


@pytest.mark.integration
class TestTransacoesAPI:
    """Testes de integração para endpoints de transações"""
    
    def test_listar_transacoes_retorna_200(self, client):
        """Testa listagem de transações"""
        # Act
        response = client.get("/transacoes/")
        
        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_criar_transacao_valida_retorna_201(self, client):
        """Testa criação de transação válida"""
        # Arrange
        transacao_data = {
            "data": "2026-01-15",
            "descricao": "Teste integração",
            "valor": 100.50,
            "tipo": "saida",
            "origem": "manual"
        }
        
        # Act
        response = client.post("/transacoes/", json=transacao_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["descricao"] == "Teste integração"
        assert data["valor"] == 100.50
        
        # Cleanup
        if "id" in data:
            client.delete(f"/transacoes/{data['id']}")
    
    def test_obter_resumo_mensal_retorna_200(self, client):
        """Testa endpoint de resumo mensal"""
        # Act
        response = client.get("/transacoes/resumo/mensal?mes=1&ano=2026")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_entradas" in data
        assert "total_saidas" in data
        assert "saldo" in data
        assert "entradas_por_categoria" in data
        assert "saidas_por_categoria" in data


@pytest.mark.integration
class TestConfiguracoesAPI:
    """Testes de integração para endpoints de configurações"""
    
    def test_listar_configuracoes_retorna_200(self, client):
        """Testa listagem de configurações"""
        # Arrange - Criar configurações padrão
        client.post("/configuracoes/", json={"chave": "diaInicioPeriodo", "valor": "1"})
        client.post("/configuracoes/", json={"chave": "criterio_data_transacao", "valor": "data_transacao"})
        
        # Act
        response = client.get("/configuracoes/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "diaInicioPeriodo" in data
        assert "criterio_data_transacao" in data
    
    def test_obter_configuracao_existente_retorna_200(self, client):
        """Testa obter configuração específica"""
        # Arrange - Criar configuração
        client.post("/configuracoes/", json={"chave": "diaInicioPeriodo", "valor": "1"})
        
        # Act
        response = client.get("/configuracoes/diaInicioPeriodo")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "diaInicioPeriodo"
        assert "valor" in data
    
    def test_obter_configuracao_inexistente_retorna_404(self, client):
        """Testa que buscar configuração inexistente retorna 404"""
        # Act
        response = client.get("/configuracoes/chave_inexistente")
        
        # Assert
        assert response.status_code == 404
