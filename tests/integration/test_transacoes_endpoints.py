"""
Testes de integração para endpoints de transações.

Testa:
- POST /transacoes (criar)
- GET /transacoes (listar com filtros)
- GET /transacoes/{id} (obter)
- PATCH /transacoes/{id} (atualizar)
- DELETE /transacoes/{id} (deletar)
- GET /transacoes/categorias (listar categorias)
- GET /transacoes/resumo/mensal (resumo)
- POST /transacoes/{id}/restaurar-valor
- POST /transacoes/{id}/tags/{tag_id} (adicionar tag)
- DELETE /transacoes/{id}/tags/{tag_id} (remover tag)
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import TipoTransacao
from tests.factories import TransacaoFactory, TagFactory, ConfiguracaoFactory


class TestCriarTransacao:
    """Testes para POST /transacoes."""
    
    def test_criar_transacao_completa(self, client: TestClient):
        """Testa criação de transação com todos os campos."""
        payload = {
            "data": "2024-01-15",
            "descricao": "Compra no supermercado",
            "valor": 150.50,
            "tipo": "saida",
            "categoria": "Alimentação",
            "observacoes": "Compras da semana",
            "data_fatura": "2024-02-15",
        }
        
        response = client.post("/transacoes", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["descricao"] == "Compra no supermercado"
        assert data["valor"] == 150.50
        assert data["tipo"] == "saida"
        assert data["categoria"] == "Alimentação"
        assert data["data_fatura"] == "2024-02-15"
        assert "id" in data
        assert "criado_em" in data
    
    def test_criar_transacao_campos_minimos(self, client: TestClient):
        """Testa criação com apenas campos obrigatórios."""
        payload = {
            "data": "2024-01-15",
            "descricao": "Transação mínima",
            "valor": 50.00,
            "tipo": "entrada",
        }
        
        response = client.post("/transacoes", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["descricao"] == "Transação mínima"
        assert data["origem"] == "manual"  # Default
        assert data["categoria"] is None
    
    @pytest.mark.edge_case
    def test_criar_transacao_valor_zero(self, client: TestClient):
        """EDGE CASE: Valor zero é permitido."""
        payload = {
            "data": "2024-01-15",
            "descricao": "Valor zero",
            "valor": 0.0,
            "tipo": "saida",
        }
        
        response = client.post("/transacoes", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valor"] == 0.0
    
    @pytest.mark.edge_case
    def test_criar_transacao_valor_negativo(self, client: TestClient):
        """EDGE CASE: Valor negativo é permitido (BUG)."""
        payload = {
            "data": "2024-01-15",
            "descricao": "Valor negativo",
            "valor": -100.0,
            "tipo": "saida",
        }
        
        response = client.post("/transacoes", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valor"] == -100.0
    
    @pytest.mark.edge_case
    def test_criar_transacao_descricao_vazia(self, client: TestClient):
        """EDGE CASE: Descrição vazia é permitida."""
        payload = {
            "data": "2024-01-15",
            "descricao": "",
            "valor": 50.0,
            "tipo": "saida",
        }
        
        response = client.post("/transacoes", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["descricao"] == ""
    
    def test_criar_transacao_tipo_invalido(self, client: TestClient):
        """Testa validação de tipo de transação."""
        payload = {
            "data": "2024-01-15",
            "descricao": "Teste",
            "valor": 50.0,
            "tipo": "invalido",
        }
        
        response = client.post("/transacoes", json=payload)
        
        assert response.status_code == 422  # Validation error


class TestListarTransacoes:
    """Testes para GET /transacoes."""
    
    def test_listar_sem_filtros(self, client: TestClient, session: Session):
        """Testa listagem sem filtros."""
        # Criar transações
        TransacaoFactory.create(session=session, descricao="Transação 1")
        TransacaoFactory.create(session=session, descricao="Transação 2")
        TransacaoFactory.create(session=session, descricao="Transação 3")
        
        response = client.get("/transacoes")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_listar_filtro_mes_ano(self, client: TestClient, session: Session):
        """Testa filtro por mês e ano."""
        # Criar transações em diferentes meses
        TransacaoFactory.create(
            session=session,
            data=date(2024, 1, 15),
            descricao="Janeiro"
        )
        TransacaoFactory.create(
            session=session,
            data=date(2024, 2, 15),
            descricao="Fevereiro"
        )
        
        response = client.get("/transacoes?mes=1&ano=2024")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["descricao"] == "Janeiro"
    
    def test_listar_filtro_data_inicio_data_fim(self, client: TestClient, session: Session):
        """Testa filtro por período customizado."""
        # Criar transações
        TransacaoFactory.create(session=session, data=date(2024, 1, 10))
        TransacaoFactory.create(session=session, data=date(2024, 1, 20))
        TransacaoFactory.create(session=session, data=date(2024, 1, 30))
        
        response = client.get("/transacoes?data_inicio=2024-01-15&data_fim=2024-01-25")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Apenas a transação do dia 20
    
    def test_listar_filtro_categoria(self, client: TestClient, session: Session):
        """Testa filtro por categoria."""
        TransacaoFactory.create(session=session, categoria="Alimentação")
        TransacaoFactory.create(session=session, categoria="Transporte")
        TransacaoFactory.create(session=session, categoria="Alimentação")
        
        response = client.get("/transacoes?categoria=Alimentação")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for transacao in data:
            assert transacao["categoria"] == "Alimentação"
    
    def test_listar_filtro_categoria_null(self, client: TestClient, session: Session):
        """Testa filtro por transações sem categoria."""
        TransacaoFactory.create(session=session, categoria="Alimentação")
        TransacaoFactory.create(session=session, categoria=None)
        TransacaoFactory.create(session=session, categoria=None)
        
        response = client.get("/transacoes?categoria=null")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for transacao in data:
            assert transacao["categoria"] is None
    
    def test_listar_filtro_tags(self, client: TestClient, session: Session):
        """Testa filtro por tags (operação OR)."""
        from app.models_tags import TransacaoTag
        
        # Criar tags
        tag1 = TagFactory.create(session=session, nome="Tag1")
        tag2 = TagFactory.create(session=session, nome="Tag2")
        
        # Criar transações
        t1 = TransacaoFactory.create(session=session, descricao="T1")
        t2 = TransacaoFactory.create(session=session, descricao="T2")
        t3 = TransacaoFactory.create(session=session, descricao="T3")
        
        # Associar tags
        session.add(TransacaoTag(transacao_id=t1.id, tag_id=tag1.id))
        session.add(TransacaoTag(transacao_id=t2.id, tag_id=tag2.id))
        session.commit()
        
        # Filtrar por tag1 OU tag2
        response = client.get(f"/transacoes?tags={tag1.id},{tag2.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # t1 e t2
    
    def test_listar_filtro_tags_invalidas(self, client: TestClient):
        """Testa que tags inválidas retornam 400."""
        response = client.get("/transacoes?tags=abc,xyz")
        
        assert response.status_code == 400
    
    def test_lista_vazia(self, client: TestClient):
        """Testa que retorna lista vazia quando não há transações."""
        response = client.get("/transacoes")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestObterTransacao:
    """Testes para GET /transacoes/{id}."""
    
    def test_obter_transacao_existente(self, client: TestClient, session: Session):
        """Testa obter transação existente."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Transação teste"
        )
        
        response = client.get(f"/transacoes/{transacao.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transacao.id
        assert data["descricao"] == "Transação teste"
    
    def test_obter_transacao_inexistente(self, client: TestClient):
        """Testa que retorna 404 para transação inexistente."""
        response = client.get("/transacoes/99999")
        
        assert response.status_code == 404
    
    def test_obter_transacao_com_tags(self, client: TestClient, session: Session):
        """Testa que tags são carregadas junto."""
        from app.models_tags import TransacaoTag
        
        transacao = TransacaoFactory.create(session=session)
        tag = TagFactory.create(session=session, nome="TestTag")
        
        session.add(TransacaoTag(transacao_id=transacao.id, tag_id=tag.id))
        session.commit()
        
        response = client.get(f"/transacoes/{transacao.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert len(data["tags"]) == 1
        assert data["tags"][0]["nome"] == "TestTag"


class TestAtualizarTransacao:
    """Testes para PATCH /transacoes/{id}."""
    
    def test_atualizar_parcial(self, client: TestClient, session: Session):
        """Testa atualização parcial de campos."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Original",
            categoria="Categoria Original"
        )
        
        payload = {"descricao": "Modificada"}
        
        response = client.patch(f"/transacoes/{transacao.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["descricao"] == "Modificada"
        assert data["categoria"] == "Categoria Original"  # Não mudou
    
    def test_atualizar_valor_preserva_valor_original(self, client: TestClient, session: Session):
        """Testa que valor_original é preservado ao atualizar valor."""
        transacao = TransacaoFactory.create(
            session=session,
            valor=100.0,
            valor_original=None
        )
        
        # Primeira atualização de valor
        response = client.patch(
            f"/transacoes/{transacao.id}",
            json={"valor": 90.0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valor"] == 90.0
        assert data["valor_original"] == 100.0  # Preservado
        
        # Segunda atualização
        response = client.patch(
            f"/transacoes/{transacao.id}",
            json={"valor": 80.0}
        )
        
        data = response.json()
        assert data["valor"] == 80.0
        assert data["valor_original"] == 100.0  # Ainda preservado
    
    def test_atualizar_transacao_inexistente(self, client: TestClient):
        """Testa que retorna 404 para transação inexistente."""
        response = client.patch("/transacoes/99999", json={"descricao": "Teste"})
        
        assert response.status_code == 404


class TestDeletarTransacao:
    """Testes para DELETE /transacoes/{id}."""
    
    def test_deletar_transacao(self, client: TestClient, session: Session):
        """Testa deletar transação."""
        transacao = TransacaoFactory.create(session=session)
        
        response = client.delete(f"/transacoes/{transacao.id}")
        
        assert response.status_code == 204
        
        # Verificar que foi deletada
        response = client.get(f"/transacoes/{transacao.id}")
        assert response.status_code == 404
    
    def test_deletar_transacao_inexistente(self, client: TestClient):
        """Testa que retorna 404 para transação inexistente."""
        response = client.delete("/transacoes/99999")
        
        assert response.status_code == 404


class TestListarCategorias:
    """Testes para GET /transacoes/categorias."""
    
    def test_listar_categorias_unicas(self, client: TestClient, session: Session):
        """Testa que retorna apenas categorias únicas."""
        TransacaoFactory.create(session=session, categoria="Alimentação")
        TransacaoFactory.create(session=session, categoria="Transporte")
        TransacaoFactory.create(session=session, categoria="Alimentação")  # Duplicada
        TransacaoFactory.create(session=session, categoria=None)
        
        response = client.get("/transacoes/categorias")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alimentação e Transporte (None filtrado)
        assert "Alimentação" in data
        assert "Transporte" in data
    
    def test_categorias_ordenadas_alfabeticamente(self, client: TestClient, session: Session):
        """Testa que categorias são retornadas ordenadas."""
        TransacaoFactory.create(session=session, categoria="Zebra")
        TransacaoFactory.create(session=session, categoria="Alpha")
        TransacaoFactory.create(session=session, categoria="Beta")
        
        response = client.get("/transacoes/categorias")
        
        assert response.status_code == 200
        data = response.json()
        assert data == ["Alpha", "Beta", "Zebra"]
    
    def test_categorias_vazia(self, client: TestClient):
        """Testa que retorna lista vazia quando não há transações."""
        response = client.get("/transacoes/categorias")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestResumoMensal:
    """Testes para GET /transacoes/resumo/mensal."""
    
    def test_resumo_com_mes_ano(self, client: TestClient, session: Session):
        """Testa resumo mensal com filtro mes/ano."""
        # Criar transações em janeiro
        TransacaoFactory.create(
            session=session,
            data=date(2024, 1, 15),
            valor=100.0,
            tipo=TipoTransacao.ENTRADA,
            categoria="Salário"
        )
        TransacaoFactory.create(
            session=session,
            data=date(2024, 1, 20),
            valor=50.0,
            tipo=TipoTransacao.SAIDA,
            categoria="Alimentação"
        )
        TransacaoFactory.create(
            session=session,
            data=date(2024, 1, 25),
            valor=30.0,
            tipo=TipoTransacao.SAIDA,
            categoria="Transporte"
        )
        
        response = client.get("/transacoes/resumo/mensal?mes=1&ano=2024")
        
        assert response.status_code == 200
        data = response.json()
        assert data["mes"] == 1
        assert data["ano"] == 2024
        assert data["total_entradas"] == 100.0
        assert data["total_saidas"] == 80.0  # 50 + 30
        assert data["saldo"] == 20.0  # 100 - 80
        assert "entradas_por_categoria" in data
        assert "saidas_por_categoria" in data
        assert data["saidas_por_categoria"]["Alimentação"] == 50.0
        assert data["saidas_por_categoria"]["Transporte"] == 30.0
    
    def test_resumo_com_data_inicio_fim(self, client: TestClient, session: Session):
        """Testa resumo com período customizado."""
        TransacaoFactory.create(
            session=session,
            data=date(2024, 1, 10),
            valor=100.0,
            tipo=TipoTransacao.ENTRADA
        )
        TransacaoFactory.create(
            session=session,
            data=date(2024, 1, 20),
            valor=50.0,
            tipo=TipoTransacao.SAIDA
        )
        TransacaoFactory.create(
            session=session,
            data=date(2024, 1, 30),
            valor=30.0,
            tipo=TipoTransacao.SAIDA
        )
        
        # Filtrar apenas meio do mês
        response = client.get(
            "/transacoes/resumo/mensal?data_inicio=2024-01-15&data_fim=2024-01-25"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_entradas"] == 0.0  # Transação do dia 10 excluída
        assert data["total_saidas"] == 50.0  # Apenas transação do dia 20
    
    def test_resumo_sem_parametros(self, client: TestClient):
        """Testa que retorna 400 se não fornecer parâmetros."""
        response = client.get("/transacoes/resumo/mensal")
        
        assert response.status_code == 400
    
    def test_resumo_categoria_sem_categoria(self, client: TestClient, session: Session):
        """Testa que transações sem categoria aparecem como 'Sem categoria'."""
        TransacaoFactory.create(
            session=session,
            data=date(2024, 1, 15),
            valor=100.0,
            tipo=TipoTransacao.SAIDA,
            categoria=None
        )
        
        response = client.get("/transacoes/resumo/mensal?mes=1&ano=2024")
        
        assert response.status_code == 200
        data = response.json()
        assert "Sem categoria" in data["saidas_por_categoria"]
        assert data["saidas_por_categoria"]["Sem categoria"] == 100.0


class TestRestaurarValor:
    """Testes para POST /transacoes/{id}/restaurar-valor."""
    
    def test_restaurar_valor_original(self, client: TestClient, session: Session):
        """Testa restaurar valor original."""
        transacao = TransacaoFactory.create(
            session=session,
            valor=50.0,
            valor_original=100.0
        )
        
        response = client.post(f"/transacoes/{transacao.id}/restaurar-valor")
        
        assert response.status_code == 200
        data = response.json()
        assert data["valor"] == 100.0
        assert data["valor_original"] == 100.0
    
    def test_restaurar_sem_valor_original(self, client: TestClient, session: Session):
        """Testa que retorna 400 se não houver valor_original."""
        transacao = TransacaoFactory.create(
            session=session,
            valor=50.0,
            valor_original=None
        )
        
        response = client.post(f"/transacoes/{transacao.id}/restaurar-valor")
        
        assert response.status_code == 400
    
    def test_restaurar_transacao_inexistente(self, client: TestClient):
        """Testa que retorna 404 para transação inexistente."""
        response = client.post("/transacoes/99999/restaurar-valor")
        
        assert response.status_code == 404


class TestAdicionarRemoverTags:
    """Testes para adicionar/remover tags de transações."""
    
    def test_adicionar_tag(self, client: TestClient, session: Session):
        """Testa adicionar tag a transação."""
        transacao = TransacaoFactory.create(session=session)
        tag = TagFactory.create(session=session)
        
        response = client.post(f"/transacoes/{transacao.id}/tags/{tag.id}")
        
        assert response.status_code == 204
        
        # Verificar que tag foi adicionada
        response = client.get(f"/transacoes/{transacao.id}")
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == tag.id
    
    def test_adicionar_tag_duplicada_idempotente(self, client: TestClient, session: Session):
        """Testa que adicionar tag duplicada é idempotente."""
        from app.models_tags import TransacaoTag
        
        transacao = TransacaoFactory.create(session=session)
        tag = TagFactory.create(session=session)
        
        # Adicionar tag manualmente
        session.add(TransacaoTag(transacao_id=transacao.id, tag_id=tag.id))
        session.commit()
        
        # Tentar adicionar novamente
        response = client.post(f"/transacoes/{transacao.id}/tags/{tag.id}")
        
        assert response.status_code == 204
        
        # Verificar que não foi duplicada
        response = client.get(f"/transacoes/{transacao.id}")
        data = response.json()
        assert len(data["tags"]) == 1
    
    def test_adicionar_tag_transacao_inexistente(self, client: TestClient, session: Session):
        """Testa que retorna 404 se transação não existe."""
        tag = TagFactory.create(session=session)
        
        response = client.post(f"/transacoes/99999/tags/{tag.id}")
        
        assert response.status_code == 404
    
    def test_adicionar_tag_inexistente(self, client: TestClient, session: Session):
        """Testa que retorna 404 se tag não existe."""
        transacao = TransacaoFactory.create(session=session)
        
        response = client.post(f"/transacoes/{transacao.id}/tags/99999")
        
        assert response.status_code == 404
    
    def test_remover_tag(self, client: TestClient, session: Session):
        """Testa remover tag de transação."""
        from app.models_tags import TransacaoTag
        
        transacao = TransacaoFactory.create(session=session)
        tag = TagFactory.create(session=session)
        
        session.add(TransacaoTag(transacao_id=transacao.id, tag_id=tag.id))
        session.commit()
        
        response = client.delete(f"/transacoes/{transacao.id}/tags/{tag.id}")
        
        assert response.status_code == 204
        
        # Verificar que tag foi removida
        response = client.get(f"/transacoes/{transacao.id}")
        data = response.json()
        assert len(data["tags"]) == 0
    
    def test_remover_tag_nao_associada_idempotente(self, client: TestClient, session: Session):
        """Testa que remover tag não associada é idempotente."""
        transacao = TransacaoFactory.create(session=session)
        tag = TagFactory.create(session=session)
        
        # Tag não está associada
        response = client.delete(f"/transacoes/{transacao.id}/tags/{tag.id}")
        
        assert response.status_code == 204
    
    def test_remover_tag_transacao_inexistente(self, client: TestClient, session: Session):
        """Testa que retorna 404 se transação não existe."""
        tag = TagFactory.create(session=session)
        
        response = client.delete(f"/transacoes/99999/tags/{tag.id}")
        
        assert response.status_code == 404
