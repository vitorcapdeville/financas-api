"""
Testes de API para o router de importação
"""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO

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


class TestImportacaoRouter:
    """Testes para o router de importação"""
    
    def test_importar_extrato_csv_valido(self, client):
        """Deve importar extrato bancário CSV válido"""
        # Criar CSV válido
        csv_content = """data,descricao,valor
15/01/2024,Salário,5000.00
16/01/2024,Supermercado,-150.50
17/01/2024,Restaurante,-80.00"""
        
        # Criar arquivo
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        # Importar
        response = client.post(
            "/importacao/extrato",
            files={"arquivo": ("extrato.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 3
        assert len(data["transacoes_ids"]) == 3
        assert "importadas com sucesso" in data["mensagem"].lower()
    
    def test_importar_extrato_csv_com_categoria(self, client):
        """Deve importar extrato CSV com categoria"""
        csv_content = """data,descricao,valor,categoria
15/01/2024,Salário,5000.00,Renda
16/01/2024,Supermercado,-150.50,Alimentação"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/extrato",
            files={"arquivo": ("extrato.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 2
        
        # Verificar que categorias foram salvas
        transacoes = client.get("/transacoes").json()
        assert any(t["categoria"] == "Renda" for t in transacoes)
        assert any(t["categoria"] == "Alimentação" for t in transacoes)
    
    def test_importar_extrato_csv_vazio(self, client):
        """Deve importar 0 transações de CSV vazio (comportamento tolerante)"""
        csv_content = """data,descricao,valor"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/extrato",
            files={"arquivo": ("extrato.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 0
    
    def test_importar_extrato_csv_sem_colunas_obrigatorias(self, client):
        """Deve retornar erro se faltar colunas obrigatórias"""
        # Falta coluna 'valor'
        csv_content = """data,descricao
15/01/2024,Compra"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/extrato",
            files={"arquivo": ("extrato.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 400
        assert "coluna" in response.json()["detail"].lower()
    
    def test_importar_extrato_csv_com_data_invalida(self, client):
        """Deve ignorar linhas com data inválida (comportamento tolerante)"""
        csv_content = """data,descricao,valor
99/99/9999,Compra Inválida,100.00
15/01/2024,Compra Válida,50.00"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/extrato",
            files={"arquivo": ("extrato.csv", arquivo, "text/csv")}
        )
        
        # Sistema ignora linha inválida e importa apenas a válida
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 1
    
    def test_importar_fatura_csv_valida(self, client):
        """Deve importar fatura de cartão CSV válida"""
        csv_content = """data,descricao,valor
15/01/2024,Netflix,39.90
16/01/2024,Uber,25.00
17/01/2024,iFood,45.50"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/fatura",
            files={"arquivo": ("fatura.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 3
        assert len(data["transacoes_ids"]) == 3
        
        # Verificar que todas são saídas
        transacoes = client.get("/transacoes").json()
        for t in transacoes:
            assert t["tipo"] == "saida"
    
    def test_importar_fatura_com_valores_negativos(self, client):
        """Deve converter valores negativos para positivos em fatura"""
        csv_content = """data,descricao,valor
15/01/2024,Compra,-100.00
16/01/2024,Serviço,-50.00"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/fatura",
            files={"arquivo": ("fatura.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 2
        
        # Verificar que valores foram convertidos
        transacoes = client.get("/transacoes").json()
        for t in transacoes:
            assert t["valor"] > 0
            assert t["tipo"] == "saida"
    
    def test_importar_fatura_com_data_fatura(self, client):
        """Deve importar fatura com data de fechamento"""
        csv_content = """data,descricao,valor,data_fatura
15/01/2024,Netflix,39.90,05/02/2024
16/01/2024,Spotify,19.90,05/02/2024"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/fatura",
            files={"arquivo": ("fatura.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 2
    
    def test_importar_arquivo_nao_csv(self, client):
        """Deve retornar erro para arquivo não CSV/Excel"""
        # Arquivo de texto simples
        content = "Este não é um CSV válido sem vírgulas"
        arquivo = BytesIO(content.encode('utf-8'))
        
        response = client.post(
            "/importacao/extrato",
            files={"arquivo": ("arquivo.txt", arquivo, "text/plain")}
        )
        
        assert response.status_code == 400
    
    def test_importar_extrato_com_regras_ativas(self, client):
        """Deve aplicar regras ativas durante importação"""
        # Criar regra ativa
        client.post("/regras", json={
            "nome": "Categorizar Salário",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "Salário",
            "acao_valor": "Renda",
            "ativo": True,
            "prioridade": 100
        })
        
        # Importar extrato com transação que combina com regra
        csv_content = """data,descricao,valor
15/01/2024,Salário do mês,5000.00"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/extrato",
            files={"arquivo": ("extrato.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 200
        
        # Verificar que regra foi aplicada
        transacoes = client.get("/transacoes").json()
        assert len(transacoes) == 1
        assert transacoes[0]["categoria"] == "Renda"
    
    def test_importar_extrato_formato_data_alternativo(self, client):
        """Deve aceitar formato de data YYYY-MM-DD"""
        csv_content = """data,descricao,valor
2024-01-15,Compra,100.00
2024-01-16,Venda,200.00"""
        
        arquivo = BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/extrato",
            files={"arquivo": ("extrato.csv", arquivo, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 2
