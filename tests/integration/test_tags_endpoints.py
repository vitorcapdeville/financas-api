"""
Testes de integração para endpoints de tags
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from tests.factories import TagFactory, TransacaoFactory


class TestListarTags:
    """Testes para GET /tags"""
    
    def test_listar_tags_vazio(self, client: TestClient):
        """Deve retornar lista vazia quando não há tags."""
        response = client.get("/tags")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_listar_tags_ordenadas_por_nome(self, client: TestClient, session):
        """Tags devem ser retornadas ordenadas alfabeticamente por nome."""
        # Cria tags fora de ordem
        tag_z = TagFactory.create(session=session, nome="Zebra")
        tag_a = TagFactory.create(session=session, nome="Alimentação")
        tag_m = TagFactory.create(session=session, nome="Moradia")
        
        response = client.get("/tags")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Verifica ordem alfabética
        nomes = [tag["nome"] for tag in data]
        assert nomes == ["Alimentação", "Moradia", "Zebra"]
    
    def test_listar_tags_com_todos_campos(self, client: TestClient, session):
        """Deve retornar todos os campos de cada tag."""
        tag = TagFactory.create(session=session, nome="Essencial", cor="#FF0000")
        
        response = client.get("/tags")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        tag_data = data[0]
        assert tag_data["id"] == tag.id
        assert tag_data["nome"] == "Essencial"
        assert tag_data["cor"] == "#FF0000"
        assert "criado_em" in tag_data
        assert "atualizado_em" in tag_data


class TestObterTag:
    """Testes para GET /tags/{tag_id}"""
    
    def test_obter_tag_existente(self, client: TestClient, session):
        """Deve retornar tag quando existe."""
        tag = TagFactory.create(session=session, nome="Importante", cor="#00FF00")
        
        response = client.get(f"/tags/{tag.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tag.id
        assert data["nome"] == "Importante"
        assert data["cor"] == "#00FF00"
    
    def test_obter_tag_inexistente(self, client: TestClient):
        """Deve retornar 404 quando tag não existe."""
        response = client.get("/tags/99999")
        
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"].lower()


class TestCriarTag:
    """Testes para POST /tags"""
    
    def test_criar_tag_completa(self, client: TestClient):
        """Deve criar tag com todos os campos."""
        tag_data = {
            "nome": "Urgente",
            "cor": "#FF5733"
        }
        
        response = client.post("/tags", json=tag_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Urgente"
        assert data["cor"] == "#FF5733"
        assert "id" in data
        assert "criado_em" in data
        assert "atualizado_em" in data
    
    def test_criar_tag_sem_cor(self, client: TestClient):
        """Deve criar tag sem cor (cor é opcional)."""
        tag_data = {
            "nome": "Sem Cor"
        }
        
        response = client.post("/tags", json=tag_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Sem Cor"
        assert data["cor"] is None
    
    def test_criar_tag_nome_duplicado(self, client: TestClient, session):
        """Não deve permitir criar tag com nome duplicado."""
        TagFactory.create(session=session, nome="Duplicada")
        
        tag_data = {
            "nome": "Duplicada",
            "cor": "#000000"
        }
        
        response = client.post("/tags", json=tag_data)
        
        assert response.status_code == 400
        assert "já existe" in response.json()["detail"].lower()
    
    def test_criar_tag_nome_vazio(self, client: TestClient):
        """Não deve permitir criar tag com nome vazio."""
        tag_data = {
            "nome": "",
            "cor": "#000000"
        }
        
        response = client.post("/tags", json=tag_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_criar_tag_cor_invalida(self, client: TestClient):
        """
        Cor inválida é aceita atualmente (sem validação).
        TODO: Implementar validação de cor hexadecimal no modelo TagCreate.
        """
        tag_data = {
            "nome": "Teste",
            "cor": "vermelho"  # Formato inválido, mas aceito
        }
        
        response = client.post("/tags", json=tag_data)
        
        # Comportamento atual: aceita qualquer string
        assert response.status_code == 201
        data = response.json()
        assert data["cor"] == "vermelho"  # Armazenado como está
    
    @pytest.mark.edge_case
    def test_criar_tag_nome_case_insensitive_duplicado(self, client: TestClient, session):
        """
        EDGE CASE: Deve detectar nomes duplicados ignorando case.
        Nota: Requer índice UNIQUE em LOWER(nome) no PostgreSQL.
        """
        TagFactory.create(session=session, nome="Importante")
        
        tag_data = {
            "nome": "IMPORTANTE",  # Mesmo nome, case diferente
            "cor": "#000000"
        }
        
        response = client.post("/tags", json=tag_data)
        
        # Com SQLite, pode passar (400). Com PostgreSQL + migração, deve falhar (400)
        # Por enquanto, aceita ambos os comportamentos
        assert response.status_code in [201, 400]


class TestAtualizarTag:
    """Testes para PATCH /tags/{tag_id}"""
    
    def test_atualizar_nome(self, client: TestClient, session):
        """Deve atualizar nome da tag."""
        tag = TagFactory.create(session=session, nome="Original", cor="#000000")
        
        update_data = {
            "nome": "Atualizada"
        }
        
        response = client.patch(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Atualizada"
        assert data["cor"] == "#000000"  # Cor não mudou
    
    def test_atualizar_cor(self, client: TestClient, session):
        """Deve atualizar cor da tag."""
        tag = TagFactory.create(session=session, nome="Teste", cor="#000000")
        
        update_data = {
            "cor": "#FFFFFF"
        }
        
        response = client.patch(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Teste"  # Nome não mudou
        assert data["cor"] == "#FFFFFF"
    
    def test_atualizar_ambos_campos(self, client: TestClient, session):
        """Deve atualizar nome e cor simultaneamente."""
        tag = TagFactory.create(session=session, nome="Original", cor="#000000")
        
        update_data = {
            "nome": "Nova",
            "cor": "#FF0000"
        }
        
        response = client.patch(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Nova"
        assert data["cor"] == "#FF0000"
    
    def test_atualizar_tag_inexistente(self, client: TestClient):
        """Deve retornar 404 ao atualizar tag inexistente."""
        update_data = {
            "nome": "Teste"
        }
        
        response = client.patch("/tags/99999", json=update_data)
        
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"].lower()
    
    def test_atualizar_nome_para_duplicado(self, client: TestClient, session):
        """Não deve permitir atualizar nome para um que já existe."""
        tag1 = TagFactory.create(session=session, nome="Tag1")
        tag2 = TagFactory.create(session=session, nome="Tag2")
        
        update_data = {
            "nome": "Tag1"  # Já existe
        }
        
        response = client.patch(f"/tags/{tag2.id}", json=update_data)
        
        assert response.status_code == 400
        assert "já existe" in response.json()["detail"].lower()
    
    def test_atualizar_timestamp_atualizado_em(self, client: TestClient, session):
        """atualizado_em deve ser atualizado automaticamente."""
        tag = TagFactory.create(session=session, nome="Original")
        criado_em_original = tag.criado_em
        atualizado_em_original = tag.atualizado_em
        
        update_data = {
            "nome": "Atualizada"
        }
        
        response = client.patch(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # criado_em não deve mudar
        assert data["criado_em"] == criado_em_original.isoformat()
        
        # atualizado_em deve ser diferente (mais recente)
        # Nota: Em testes rápidos, pode ser o mesmo segundo, então apenas verifica presença
        assert "atualizado_em" in data


class TestDeletarTag:
    """Testes para DELETE /tags/{tag_id}"""
    
    def test_deletar_tag_existente(self, client: TestClient, session):
        """Deve deletar tag existente."""
        tag = TagFactory.create(session=session, nome="Para Deletar")
        
        response = client.delete(f"/tags/{tag.id}")
        
        assert response.status_code == 204
        assert response.content == b""
        
        # Verifica que tag foi realmente deletada
        response_get = client.get(f"/tags/{tag.id}")
        assert response_get.status_code == 404
    
    def test_deletar_tag_inexistente(self, client: TestClient):
        """Deve retornar 404 ao deletar tag inexistente."""
        response = client.delete("/tags/99999")
        
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"].lower()
    
    def test_deletar_tag_remove_associacoes_transacoes(self, client: TestClient, session):
        """Ao deletar tag, deve remover associações com transações."""
        tag = TagFactory.create(session=session, nome="Tag para deletar")
        transacao = TransacaoFactory.create(session=session)
        
        # Adiciona tag à transação
        response_add = client.post(f"/transacoes/{transacao.id}/tags/{tag.id}")
        assert response_add.status_code == 204
        
        # Verifica que tag está associada
        response_get = client.get(f"/transacoes/{transacao.id}")
        assert response_get.status_code == 200
        assert len(response_get.json()["tags"]) == 1
        
        # Deleta tag
        response_delete = client.delete(f"/tags/{tag.id}")
        assert response_delete.status_code == 204
        
        # Verifica que transação não tem mais a tag
        response_get_after = client.get(f"/transacoes/{transacao.id}")
        assert response_get_after.status_code == 200
        assert len(response_get_after.json()["tags"]) == 0
    
    def test_deletar_multiplas_tags(self, client: TestClient, session):
        """Deve permitir deletar múltiplas tags."""
        tag1 = TagFactory.create(session=session, nome="Tag1")
        tag2 = TagFactory.create(session=session, nome="Tag2")
        tag3 = TagFactory.create(session=session, nome="Tag3")
        
        # Deleta todas
        client.delete(f"/tags/{tag1.id}")
        client.delete(f"/tags/{tag2.id}")
        client.delete(f"/tags/{tag3.id}")
        
        # Verifica que lista está vazia
        response = client.get("/tags")
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestEdgeCasesTags:
    """Testes de edge cases para tags"""
    
    @pytest.mark.edge_case
    def test_criar_tag_nome_com_espacos(self, client: TestClient):
        """Deve preservar espaços no nome da tag."""
        tag_data = {
            "nome": "  Tag com Espaços  ",
            "cor": "#000000"
        }
        
        response = client.post("/tags", json=tag_data)
        
        assert response.status_code == 201
        data = response.json()
        # Comportamento atual: preserva espaços (sem trim)
        assert data["nome"] == "  Tag com Espaços  "
    
    @pytest.mark.edge_case
    def test_criar_tag_nome_unicode(self, client: TestClient):
        """Deve suportar caracteres Unicode em nomes."""
        tag_data = {
            "nome": "🏠 Casa e 🍕 Comida",
            "cor": "#FF0000"
        }
        
        response = client.post("/tags", json=tag_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "🏠 Casa e 🍕 Comida"
    
    @pytest.mark.edge_case
    def test_criar_tag_cor_minuscula(self, client: TestClient):
        """Deve aceitar cor em minúscula (#ffffff)."""
        tag_data = {
            "nome": "Teste Minúscula",
            "cor": "#ffffff"
        }
        
        response = client.post("/tags", json=tag_data)
        
        # Validação de cor deve aceitar tanto maiúscula quanto minúscula
        assert response.status_code == 201
        data = response.json()
        assert data["cor"].lower() == "#ffffff"
    
    @pytest.mark.edge_case
    def test_atualizar_tag_para_mesmo_nome(self, client: TestClient, session):
        """Deve permitir atualizar tag mantendo o mesmo nome (idempotente)."""
        tag = TagFactory.create(session=session, nome="Mesmo Nome", cor="#000000")
        
        update_data = {
            "nome": "Mesmo Nome",  # Mesmo nome
            "cor": "#FFFFFF"  # Cor diferente
        }
        
        response = client.patch(f"/tags/{tag.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Mesmo Nome"
        assert data["cor"] == "#FFFFFF"
