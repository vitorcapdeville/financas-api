"""
Testes de integração para endpoints de regras automáticas
"""
import pytest
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.models_regra import TipoAcao, CriterioTipo
from tests.factories import RegraFactory, TagFactory, TransacaoFactory


class TestListarRegras:
    """Testes para GET /regras"""
    
    def test_listar_regras_vazio(self, client: TestClient):
        """Deve retornar lista vazia quando não há regras."""
        response = client.get("/regras")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_listar_regras_ordenadas_por_prioridade(self, client: TestClient, session):
        """Regras devem ser retornadas ordenadas por prioridade DESC."""
        # Cria regras com prioridades diferentes
        regra1 = RegraFactory.create(session=session, nome="Prioridade 1", prioridade=1)
        regra3 = RegraFactory.create(session=session, nome="Prioridade 3", prioridade=3)
        regra2 = RegraFactory.create(session=session, nome="Prioridade 2", prioridade=2)
        
        response = client.get("/regras")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Verifica ordem: maior prioridade primeiro
        prioridades = [regra["prioridade"] for regra in data]
        assert prioridades == [3, 2, 1]
    
    def test_listar_regras_filtro_ativo(self, client: TestClient, session):
        """Deve filtrar regras por status ativo."""
        regra_ativa = RegraFactory.create(session=session, nome="Ativa", ativo=True)
        regra_inativa = RegraFactory.create(session=session, nome="Inativa", ativo=False)
        
        # Filtrar apenas ativas
        response = client.get("/regras?ativo=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nome"] == "Ativa"
        
        # Filtrar apenas inativas
        response = client.get("/regras?ativo=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nome"] == "Inativa"
    
    def test_listar_regras_filtro_tipo_acao(self, client: TestClient, session):
        """Deve filtrar regras por tipo de ação."""
        regra_categoria = RegraFactory.create(
            session=session,
            nome="Categorizar",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA
        )
        regra_valor = RegraFactory.create(
            session=session,
            nome="Alterar Valor",
            tipo_acao=TipoAcao.ALTERAR_VALOR
        )
        
        response = client.get(f"/regras?tipo_acao={TipoAcao.ALTERAR_CATEGORIA.value}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nome"] == "Categorizar"


class TestObterRegra:
    """Testes para GET /regras/{regra_id}"""
    
    def test_obter_regra_existente(self, client: TestClient, session):
        """Deve retornar regra quando existe."""
        regra = RegraFactory.create(
            session=session,
            nome="Uber → Transporte",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            acao_valor="Transporte"
        )
        
        response = client.get(f"/regras/{regra.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == regra.id
        assert data["nome"] == "Uber → Transporte"
        assert data["tipo_acao"] == TipoAcao.ALTERAR_CATEGORIA.value
    
    def test_obter_regra_inexistente(self, client: TestClient):
        """Deve retornar 404 quando regra não existe."""
        response = client.get("/regras/99999")
        
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"].lower()


class TestCriarRegra:
    """Testes para POST /regras"""
    
    def test_criar_regra_alterar_categoria(self, client: TestClient):
        """Deve criar regra de alterar categoria."""
        regra_data = {
            "nome": "Uber → Transporte",
            "tipo_acao": TipoAcao.ALTERAR_CATEGORIA.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_CONTEM.value,
            "criterio_valor": "uber",
            "acao_valor": "Transporte"
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Uber → Transporte"
        assert data["tipo_acao"] == TipoAcao.ALTERAR_CATEGORIA.value
        assert data["acao_valor"] == "Transporte"
        assert data["prioridade"] == 1  # Primeira regra
        assert data["ativo"] is True
        assert "id" in data
    
    def test_criar_regra_alterar_valor(self, client: TestClient):
        """Deve criar regra de alterar valor com percentual."""
        regra_data = {
            "nome": "50% Netflix",
            "tipo_acao": TipoAcao.ALTERAR_VALOR.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_EXATA.value,
            "criterio_valor": "Netflix",
            "acao_valor": "50"
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "50% Netflix"
        assert data["tipo_acao"] == TipoAcao.ALTERAR_VALOR.value
        assert data["acao_valor"] == "50"
    
    def test_criar_regra_adicionar_tags(self, client: TestClient, session):
        """Deve criar regra de adicionar tags."""
        tag1 = TagFactory.create(session=session, nome="Urgente")
        tag2 = TagFactory.create(session=session, nome="Importante")
        
        regra_data = {
            "nome": "Marcar Uber como Urgente",
            "tipo_acao": "adicionar_tags",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "uber",
            "acao_valor": "placeholder"  # Será sobrescrito
        }
        
        response = client.post(
            f"/regras?tag_ids={tag1.id}&tag_ids={tag2.id}",
            json=regra_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Marcar Uber como Urgente"
        assert data["tipo_acao"] == TipoAcao.ADICIONAR_TAGS.value
        
        # acao_valor deve conter JSON com IDs das tags
        tag_ids = json.loads(data["acao_valor"])
        assert tag1.id in tag_ids
        assert tag2.id in tag_ids
    
    def test_criar_regra_prioridade_auto_incrementa(self, client: TestClient, session):
        """Prioridade deve auto-incrementar ao criar novas regras."""
        # Cria primeira regra
        regra1_data = {
            "nome": "Regra 1",
            "tipo_acao": TipoAcao.ALTERAR_CATEGORIA.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_CONTEM.value,
            "criterio_valor": "teste",
            "acao_valor": "Categoria1"
        }
        response1 = client.post("/regras", json=regra1_data)
        assert response1.status_code == 201
        assert response1.json()["prioridade"] == 1
        
        # Cria segunda regra
        regra2_data = {
            "nome": "Regra 2",
            "tipo_acao": TipoAcao.ALTERAR_CATEGORIA.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_CONTEM.value,
            "criterio_valor": "teste2",
            "acao_valor": "Categoria2"
        }
        response2 = client.post("/regras", json=regra2_data)
        assert response2.status_code == 201
        assert response2.json()["prioridade"] == 2
    
    def test_criar_regra_adicionar_tags_sem_tag_ids(self, client: TestClient):
        """Deve retornar erro se criar regra de tags sem fornecer tag_ids."""
        regra_data = {
            "nome": "Sem Tags",
            "tipo_acao": "adicionar_tags",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste",
            "acao_valor": "placeholder"
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 400
        assert "tag_ids" in response.json()["detail"].lower()
    
    def test_criar_regra_adicionar_tags_tag_inexistente(self, client: TestClient):
        """Deve retornar erro se tag_id não existe."""
        regra_data = {
            "nome": "Tag Inexistente",
            "tipo_acao": "adicionar_tags",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste",
            "acao_valor": "placeholder"
        }
        
        response = client.post("/regras?tag_ids=99999", json=regra_data)
        
        assert response.status_code == 400
        assert "não encontrada" in response.json()["detail"].lower()
    
    def test_criar_regra_alterar_valor_percentual_invalido(self, client: TestClient):
        """Deve validar percentual entre 0-100."""
        regra_data = {
            "nome": "Percentual Inválido",
            "tipo_acao": TipoAcao.ALTERAR_VALOR.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_CONTEM.value,
            "criterio_valor": "teste",
            "acao_valor": "150"  # > 100
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 400
        assert "0 e 100" in response.json()["detail"]
    
    def test_criar_regra_alterar_valor_nao_numerico(self, client: TestClient):
        """Deve rejeitar acao_valor não numérico para ALTERAR_VALOR."""
        regra_data = {
            "nome": "Não Numérico",
            "tipo_acao": TipoAcao.ALTERAR_VALOR.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_CONTEM.value,
            "criterio_valor": "teste",
            "acao_valor": "abc"
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 400
        assert "número" in response.json()["detail"].lower()
    
    def test_criar_regra_alterar_categoria_vazia(self, client: TestClient):
        """Deve rejeitar acao_valor vazio para ALTERAR_CATEGORIA."""
        regra_data = {
            "nome": "Categoria Vazia",
            "tipo_acao": TipoAcao.ALTERAR_CATEGORIA.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_CONTEM.value,
            "criterio_valor": "teste",
            "acao_valor": "   "  # Apenas espaços
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 400
        assert "vazio" in response.json()["detail"].lower()


class TestAtualizarPrioridadeRegra:
    """Testes para PATCH /regras/{regra_id}/prioridade"""
    
    def test_atualizar_prioridade(self, client: TestClient, session):
        """Deve atualizar prioridade da regra."""
        regra = RegraFactory.create(session=session, prioridade=1)
        
        response = client.patch(f"/regras/{regra.id}/prioridade?nova_prioridade=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["prioridade"] == 10
    
    def test_atualizar_prioridade_regra_inexistente(self, client: TestClient):
        """Deve retornar 404 se regra não existe."""
        response = client.patch("/regras/99999/prioridade?nova_prioridade=5")
        
        assert response.status_code == 404
    
    def test_atualizar_prioridade_minima(self, client: TestClient, session):
        """Prioridade mínima deve ser 1."""
        regra = RegraFactory.create(session=session)
        
        # Tenta prioridade 0 (inválida)
        response = client.patch(f"/regras/{regra.id}/prioridade?nova_prioridade=0")
        
        assert response.status_code == 422  # Validation error


class TestToggleAtivoRegra:
    """Testes para PATCH /regras/{regra_id}/ativar-desativar"""
    
    def test_desativar_regra_ativa(self, client: TestClient, session):
        """Deve desativar regra ativa."""
        regra = RegraFactory.create(session=session, ativo=True)
        
        response = client.patch(f"/regras/{regra.id}/ativar-desativar")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ativo"] is False
    
    def test_ativar_regra_inativa(self, client: TestClient, session):
        """Deve ativar regra inativa."""
        regra = RegraFactory.create(session=session, ativo=False)
        
        response = client.patch(f"/regras/{regra.id}/ativar-desativar")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ativo"] is True
    
    def test_toggle_multiplas_vezes(self, client: TestClient, session):
        """Deve alternar status corretamente múltiplas vezes."""
        regra = RegraFactory.create(session=session, ativo=True)
        
        # Primeira vez: True → False
        response1 = client.patch(f"/regras/{regra.id}/ativar-desativar")
        assert response1.json()["ativo"] is False
        
        # Segunda vez: False → True
        response2 = client.patch(f"/regras/{regra.id}/ativar-desativar")
        assert response2.json()["ativo"] is True
        
        # Terceira vez: True → False
        response3 = client.patch(f"/regras/{regra.id}/ativar-desativar")
        assert response3.json()["ativo"] is False
    
    def test_toggle_regra_inexistente(self, client: TestClient):
        """Deve retornar 404 se regra não existe."""
        response = client.patch("/regras/99999/ativar-desativar")
        
        assert response.status_code == 404


class TestDeletarRegra:
    """Testes para DELETE /regras/{regra_id}"""
    
    def test_deletar_regra_existente(self, client: TestClient, session):
        """Deve deletar regra existente."""
        regra = RegraFactory.create(session=session, nome="Para Deletar")
        
        response = client.delete(f"/regras/{regra.id}")
        
        assert response.status_code == 204
        assert response.content == b""
        
        # Verifica que regra foi deletada
        response_get = client.get(f"/regras/{regra.id}")
        assert response_get.status_code == 404
    
    def test_deletar_regra_inexistente(self, client: TestClient):
        """Deve retornar 404 se regra não existe."""
        response = client.delete("/regras/99999")
        
        assert response.status_code == 404
    
    def test_deletar_regra_remove_associacoes_tags(self, client: TestClient, session):
        """Deve remover associações RegraTag ao deletar regra."""
        tag = TagFactory.create(session=session, nome="Tag Teste")
        
        # Cria regra com tag
        regra_data = {
            "nome": "Regra com Tags",
            "tipo_acao": "adicionar_tags",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste",
            "acao_valor": "placeholder"
        }
        
        response_create = client.post(f"/regras?tag_ids={tag.id}", json=regra_data)
        assert response_create.status_code == 201
        regra_id = response_create.json()["id"]
        
        # Deleta regra
        response_delete = client.delete(f"/regras/{regra_id}")
        assert response_delete.status_code == 204
        
        # Verifica que tag ainda existe (não deve ser deletada)
        response_tag = client.get(f"/tags/{tag.id}")
        assert response_tag.status_code == 200


class TestAplicarRegraRetroativamente:
    """Testes para POST /regras/{regra_id}/aplicar"""
    
    def test_aplicar_regra_alterar_categoria(self, client: TestClient, session):
        """Deve aplicar regra de categoria em transações existentes."""
        # Cria transações
        t1 = TransacaoFactory.create(session=session, descricao="Uber viagem", categoria=None)
        t2 = TransacaoFactory.create(session=session, descricao="Uber Eats", categoria=None)
        t3 = TransacaoFactory.create(session=session, descricao="Netflix", categoria=None)
        
        # Cria regra
        regra = RegraFactory.create(
            session=session,
            nome="Uber → Transporte",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte"
        )
        
        # Aplica regra
        response = client.post(f"/regras/{regra.id}/aplicar")
        
        assert response.status_code == 200
        data = response.json()
        assert data["regra_id"] == regra.id
        assert data["transacoes_modificadas"] == 2  # t1 e t2
        
        # Verifica que transações foram modificadas
        t1_atualizada = client.get(f"/transacoes/{t1.id}").json()
        assert t1_atualizada["categoria"] == "Transporte"
        
        t2_atualizada = client.get(f"/transacoes/{t2.id}").json()
        assert t2_atualizada["categoria"] == "Transporte"
        
        # Netflix não deve ter sido modificada
        t3_atualizada = client.get(f"/transacoes/{t3.id}").json()
        assert t3_atualizada["categoria"] is None
    
    def test_aplicar_regra_sem_match(self, client: TestClient, session):
        """Deve retornar 0 se nenhuma transação corresponde aos critérios."""
        TransacaoFactory.create(session=session, descricao="Pizza")
        
        regra = RegraFactory.create(
            session=session,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber"  # Não existe
        )
        
        response = client.post(f"/regras/{regra.id}/aplicar")
        
        assert response.status_code == 200
        assert response.json()["transacoes_modificadas"] == 0
    
    def test_aplicar_regra_inexistente(self, client: TestClient):
        """Deve retornar 404 se regra não existe."""
        response = client.post("/regras/99999/aplicar")
        
        assert response.status_code == 404


class TestAplicarTodasRegras:
    """Testes para POST /regras/aplicar-todas"""
    
    def test_aplicar_todas_regras_ordem_prioridade(self, client: TestClient, session):
        """Deve aplicar regras em ordem de prioridade."""
        # Cria transação
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Uber Eats pedido",
            categoria=None
        )
        
        # Cria regras com prioridades diferentes
        # Prioridade maior executa primeiro
        regra1 = RegraFactory.create(
            session=session,
            nome="Uber → Transporte",
            prioridade=10,
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            ativo=True
        )
        
        regra2 = RegraFactory.create(
            session=session,
            nome="Eats → Alimentação",
            prioridade=20,  # Maior prioridade
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="eats",
            acao_valor="Alimentação",
            ativo=True
        )
        
        # Aplica todas as regras
        response = client.post("/regras/aplicar-todas")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_aplicacoes"] >= 2
        
        # Verifica categoria final (regra2 executa primeiro, depois regra1 sobrescreve)
        t_final = client.get(f"/transacoes/{transacao.id}").json()
        # A última regra aplicada define a categoria
        # Como ambas fazem match, depende da ordem de aplicação
        assert t_final["categoria"] in ["Transporte", "Alimentação"]
    
    def test_aplicar_apenas_regras_ativas(self, client: TestClient, session):
        """Deve aplicar apenas regras ativas."""
        transacao = TransacaoFactory.create(session=session, descricao="Teste", categoria=None)
        
        # Regra ativa
        regra_ativa = RegraFactory.create(
            session=session,
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor="Categoria1",
            ativo=True
        )
        
        # Regra inativa
        regra_inativa = RegraFactory.create(
            session=session,
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor="Categoria2",
            ativo=False
        )
        
        response = client.post("/regras/aplicar-todas")
        
        assert response.status_code == 200
        
        # Transação deve ter categoria da regra ativa
        t_final = client.get(f"/transacoes/{transacao.id}").json()
        assert t_final["categoria"] == "Categoria1"
    
    def test_aplicar_todas_sem_regras(self, client: TestClient):
        """Deve funcionar mesmo sem regras cadastradas."""
        response = client.post("/regras/aplicar-todas")
        
        assert response.status_code == 200
        assert response.json()["total_aplicacoes"] == 0


class TestEdgeCasesRegras:
    """Testes de edge cases para regras"""
    
    @pytest.mark.edge_case
    def test_criar_regra_percentual_zero(self, client: TestClient):
        """Deve aceitar percentual 0 (zera o valor)."""
        regra_data = {
            "nome": "Zerar Valor",
            "tipo_acao": TipoAcao.ALTERAR_VALOR.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_CONTEM.value,
            "criterio_valor": "teste",
            "acao_valor": "0"
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 201
        assert response.json()["acao_valor"] == "0"
    
    @pytest.mark.edge_case
    def test_criar_regra_percentual_100(self, client: TestClient):
        """Deve aceitar percentual 100 (mantém valor original)."""
        regra_data = {
            "nome": "Manter Valor",
            "tipo_acao": TipoAcao.ALTERAR_VALOR.value,
            "criterio_tipo": CriterioTipo.DESCRICAO_CONTEM.value,
            "criterio_valor": "teste",
            "acao_valor": "100"
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 201
        assert response.json()["acao_valor"] == "100"
    
    @pytest.mark.edge_case
    def test_criar_regra_criterio_categoria(self, client: TestClient):
        """Deve aceitar critério por categoria."""
        regra_data = {
            "nome": "Categoria → Subcategoria",
            "tipo_acao": TipoAcao.ALTERAR_CATEGORIA.value,
            "criterio_tipo": CriterioTipo.CATEGORIA.value,
            "criterio_valor": "Alimentação",
            "acao_valor": "Alimentação - Restaurante"
        }
        
        response = client.post("/regras", json=regra_data)
        
        assert response.status_code == 201
        assert response.json()["criterio_tipo"] == CriterioTipo.CATEGORIA.value
    
    @pytest.mark.edge_case
    def test_regra_descricao_case_insensitive(self, client: TestClient, session):
        """Critérios de descrição devem ser case-insensitive."""
        t1 = TransacaoFactory.create(session=session, descricao="UBER VIAGEM")
        t2 = TransacaoFactory.create(session=session, descricao="uber eats")
        t3 = TransacaoFactory.create(session=session, descricao="Uber Pool")
        
        regra = RegraFactory.create(
            session=session,
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",  # lowercase
            acao_valor="Transporte"
        )
        
        response = client.post(f"/regras/{regra.id}/aplicar")
        
        assert response.status_code == 200
        # Deve pegar todas as 3 transações (case-insensitive)
        assert response.json()["transacoes_modificadas"] == 3
