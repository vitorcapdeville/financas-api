"""
Testes adicionais de API para o router de transações
Foca em endpoints não cobertos: filtros, resumo mensal, tags
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def client():
    """Cliente de teste FastAPI com banco em memória"""
    from app.infrastructure.database.models.transacao_model import TransacaoModel  # noqa
    from app.infrastructure.database.models.tag_model import TagModel  # noqa
    from app.infrastructure.database.models.regra_model import RegraModel  # noqa
    from app.infrastructure.database.models.configuracao_model import ConfiguracaoModel  # noqa
    
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    SQLModel.metadata.create_all(test_engine)
    
    def override_get_session():
        with Session(test_engine) as session:
            yield session
    
    from app.infrastructure.database.session import get_session
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    SQLModel.metadata.drop_all(test_engine)
    app.dependency_overrides.clear()


class TestTransacoesRouterAvancado:
    """Testes avançados para endpoints de transações"""
    
    def test_listar_transacoes_com_filtro_data(self, client):
        """Deve filtrar transações por data_inicio e data_fim"""
        # Criar transações em diferentes datas
        client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "Jan",
            "valor": 100.0,
            "tipo": "saida"
        })
        client.post("/transacoes", json={
            "data": "2024-02-15",
            "descricao": "Fev",
            "valor": 200.0,
            "tipo": "saida"
        })
        client.post("/transacoes", json={
            "data": "2024-03-15",
            "descricao": "Mar",
            "valor": 300.0,
            "tipo": "saida"
        })
        
        # Filtrar apenas fevereiro
        response = client.get("/transacoes", params={
            "data_inicio": "2024-02-01",
            "data_fim": "2024-02-29"
        })
        
        assert response.status_code == 200
        transacoes = response.json()
        assert len(transacoes) == 1
        assert transacoes[0]["descricao"] == "Fev"
    
    def test_listar_transacoes_com_filtro_categoria(self, client):
        """Deve filtrar transações por categoria"""
        # Criar transações com categorias diferentes
        client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "Supermercado",
            "valor": 100.0,
            "tipo": "saida",
            "categoria": "Alimentação"
        })
        client.post("/transacoes", json={
            "data": "2024-01-16",
            "descricao": "Uber",
            "valor": 50.0,
            "tipo": "saida",
            "categoria": "Transporte"
        })
        
        # Filtrar por categoria
        response = client.get("/transacoes", params={
            "categoria": "Alimentação"
        })
        
        assert response.status_code == 200
        transacoes = response.json()
        assert len(transacoes) == 1
        assert transacoes[0]["categoria"] == "Alimentação"
    
    def test_resumo_mensal_com_mes_ano(self, client):
        """Deve obter resumo mensal por mês e ano"""
        # Criar transações em janeiro
        client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "Salário",
            "valor": 5000.0,
            "tipo": "entrada"
        })
        client.post("/transacoes", json={
            "data": "2024-01-20",
            "descricao": "Aluguel",
            "valor": 1500.0,
            "tipo": "saida",
            "categoria": "Moradia"
        })
        
        # Obter resumo de janeiro/2024
        response = client.get("/transacoes/resumo/mensal", params={
            "mes": 1,
            "ano": 2024
        })
        
        assert response.status_code == 200
        resumo = response.json()
        assert resumo["mes"] == 1
        assert resumo["ano"] == 2024
        assert resumo["total_entradas"] == 5000.0
        assert resumo["total_saidas"] == 1500.0
        assert resumo["saldo"] == 3500.0
    
    def test_resumo_mensal_com_data_customizada(self, client):
        """Deve obter resumo com data_inicio e data_fim customizados"""
        # Criar transações
        client.post("/transacoes", json={
            "data": "2024-01-25",
            "descricao": "Entrada",
            "valor": 1000.0,
            "tipo": "entrada"
        })
        client.post("/transacoes", json={
            "data": "2024-02-10",
            "descricao": "Saída",
            "valor": 500.0,
            "tipo": "saida"
        })
        
        # Resumo de 25/jan a 24/fev (período customizado)
        response = client.get("/transacoes/resumo/mensal", params={
            "data_inicio": "2024-01-25",
            "data_fim": "2024-02-24"
        })
        
        assert response.status_code == 200
        resumo = response.json()
        assert resumo["total_entradas"] == 1000.0
        assert resumo["total_saidas"] == 500.0
    
    def test_adicionar_tag_em_transacao(self, client):
        """Deve adicionar tag em transação"""
        # Criar tag
        tag_response = client.post("/tags", json={
            "nome": "Importante",
            "cor": "#FF0000"
        })
        tag_id = tag_response.json()["id"]
        
        # Criar transação
        transacao_response = client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "Compra",
            "valor": 100.0,
            "tipo": "saida"
        })
        transacao_id = transacao_response.json()["id"]
        
        # Adicionar tag
        response = client.post(f"/transacoes/{transacao_id}/tags/{tag_id}")
        
        assert response.status_code == 204
        
        # Verificar que tag foi adicionada
        tags_response = client.get(f"/transacoes/{transacao_id}/tags")
        tags = tags_response.json()
        assert len(tags) == 1
        assert tags[0]["nome"] == "Importante"
    
    def test_remover_tag_de_transacao(self, client):
        """Deve remover tag de transação"""
        # Criar tag
        tag_response = client.post("/tags", json={
            "nome": "Temporária",
            "cor": "#00FF00"
        })
        tag_id = tag_response.json()["id"]
        
        # Criar transação
        transacao_response = client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "Compra",
            "valor": 100.0,
            "tipo": "saida"
        })
        transacao_id = transacao_response.json()["id"]
        
        # Adicionar tag
        client.post(f"/transacoes/{transacao_id}/tags/{tag_id}")
        
        # Remover tag
        response = client.delete(f"/transacoes/{transacao_id}/tags/{tag_id}")
        
        assert response.status_code == 204
        
        # Verificar que tag foi removida
        tags_response = client.get(f"/transacoes/{transacao_id}/tags")
        tags = tags_response.json()
        assert len(tags) == 0
    
    def test_listar_tags_de_transacao(self, client):
        """Deve listar tags de uma transação"""
        # Criar tags
        tag1 = client.post("/tags", json={"nome": "Tag1", "cor": "#FF0000"}).json()
        tag2 = client.post("/tags", json={"nome": "Tag2", "cor": "#00FF00"}).json()
        
        # Criar transação
        transacao_response = client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "Compra",
            "valor": 100.0,
            "tipo": "saida"
        })
        transacao_id = transacao_response.json()["id"]
        
        # Adicionar tags
        client.post(f"/transacoes/{transacao_id}/tags/{tag1['id']}")
        client.post(f"/transacoes/{transacao_id}/tags/{tag2['id']}")
        
        # Listar tags
        response = client.get(f"/transacoes/{transacao_id}/tags")
        
        assert response.status_code == 200
        tags = response.json()
        assert len(tags) == 2
        nomes = [t["nome"] for t in tags]
        assert "Tag1" in nomes
        assert "Tag2" in nomes
    
    def test_restaurar_valor_original(self, client):
        """Deve restaurar valor original de transação"""
        # Criar transação
        transacao_response = client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "Compra",
            "valor": 100.0,
            "tipo": "saida"
        })
        transacao_id = transacao_response.json()["id"]
        
        # Atualizar valor
        client.patch(f"/transacoes/{transacao_id}", json={
            "valor": 200.0
        })
        
        # Restaurar valor original
        response = client.post(f"/transacoes/{transacao_id}/restaurar-valor")
        
        assert response.status_code == 200
        
        # Verificar que valor foi restaurado
        transacao = client.get(f"/transacoes/{transacao_id}").json()
        assert transacao["valor"] == 100.0
    
    def test_listar_transacoes_com_multiplas_tags(self, client):
        """Deve filtrar transações por múltiplas tags"""
        # Criar tags
        tag1 = client.post("/tags", json={"nome": "Urgente", "cor": "#FF0000"}).json()
        tag2 = client.post("/tags", json={"nome": "Revisão", "cor": "#00FF00"}).json()
        
        # Criar transações
        t1 = client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "T1",
            "valor": 100.0,
            "tipo": "saida"
        }).json()
        
        t2 = client.post("/transacoes", json={
            "data": "2024-01-16",
            "descricao": "T2",
            "valor": 200.0,
            "tipo": "saida"
        }).json()
        
        # Adicionar tags
        client.post(f"/transacoes/{t1['id']}/tags/{tag1['id']}")
        client.post(f"/transacoes/{t2['id']}/tags/{tag1['id']}")
        client.post(f"/transacoes/{t2['id']}/tags/{tag2['id']}")
        
        # Filtrar por tag1
        response = client.get("/transacoes", params={
            "tag_ids": f"{tag1['id']}"
        })
        
        assert response.status_code == 200
        transacoes = response.json()
        assert len(transacoes) >= 2    
    def test_resumo_mensal_com_filtro_tags(self, client):
        """Deve filtrar resumo mensal por tags"""
        # Criar tags
        tag_importante = client.post("/tags", json={
            "nome": "Importante",
            "cor": "#FF0000"
        }).json()
        tag_normal = client.post("/tags", json={
            "nome": "Normal",
            "cor": "#00FF00"
        }).json()
        
        # Criar transações de janeiro
        t1 = client.post("/transacoes", json={
            "data": "2024-01-10",
            "descricao": "Entrada Importante",
            "valor": 1000.0,
            "tipo": "entrada"
        }).json()
        
        t2 = client.post("/transacoes", json={
            "data": "2024-01-15",
            "descricao": "Saída Importante",
            "valor": 300.0,
            "tipo": "saida",
            "categoria": "Alimentação"
        }).json()
        
        t3 = client.post("/transacoes", json={
            "data": "2024-01-20",
            "descricao": "Saída Normal",
            "valor": 500.0,
            "tipo": "saida",
            "categoria": "Transporte"
        }).json()
        
        # Adicionar tags
        client.post(f"/transacoes/{t1['id']}/tags/{tag_importante['id']}")
        client.post(f"/transacoes/{t2['id']}/tags/{tag_importante['id']}")
        client.post(f"/transacoes/{t3['id']}/tags/{tag_normal['id']}")
        
        # Resumo sem filtro - deve incluir todas
        response_all = client.get("/transacoes/resumo/mensal", params={
            "mes": 1,
            "ano": 2024
        })
        assert response_all.status_code == 200
        resumo_all = response_all.json()
        assert resumo_all["total_entradas"] == 1000.0
        assert resumo_all["total_saidas"] == 800.0  # 300 + 500
        
        # Resumo filtrado por tag "Importante" - deve incluir apenas t1 e t2
        response_filtered = client.get("/transacoes/resumo/mensal", params={
            "mes": 1,
            "ano": 2024,
            "tags": str(tag_importante['id'])
        })
        assert response_filtered.status_code == 200
        resumo_filtered = response_filtered.json()
        assert resumo_filtered["total_entradas"] == 1000.0
        assert resumo_filtered["total_saidas"] == 300.0  # Apenas t2
        assert resumo_filtered["saldo"] == 700.0
        
        # Verificar categorias filtradas
        assert "Alimentação" in resumo_filtered["saidas_por_categoria"]
        assert resumo_filtered["saidas_por_categoria"]["Alimentação"] == 300.0
        # Transporte não deve aparecer porque t3 não tem a tag "Importante"
        assert "Transporte" not in resumo_filtered["saidas_por_categoria"]