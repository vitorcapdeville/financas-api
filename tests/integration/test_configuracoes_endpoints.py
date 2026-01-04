"""
Testes de integração para os endpoints de configurações.

Este módulo testa todos os endpoints relacionados a configurações:
- GET /configuracoes/{chave} - Obter configuração
- POST /configuracoes/ - Salvar/atualizar configuração

Cobertura:
- CRUD de configurações
- Validações específicas (diaInicioPeriodo, criterio_data_transacao)
- Edge cases (valores inválidos, chaves inexistentes, updates)
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.factories import ConfiguracaoFactory


class TestObterConfiguracao:
    """Testes para GET /configuracoes/{chave}"""

    def test_obter_configuracao_existente(self, client: TestClient, session: Session):
        """Deve retornar configuração existente."""
        config = ConfiguracaoFactory.create(
            session=session,
            chave="minha_config",
            valor="valor_teste"
        )

        response = client.get(f"/configuracoes/{config.chave}")

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "minha_config"
        assert data["valor"] == "valor_teste"

    def test_obter_configuracao_inexistente(self, client: TestClient):
        """Deve retornar None para configuração que não existe."""
        response = client.get("/configuracoes/config_inexistente")

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "config_inexistente"
        assert data["valor"] is None

    def test_obter_dia_inicio_periodo(self, client: TestClient, session: Session):
        """Deve retornar configuração de diaInicioPeriodo."""
        ConfiguracaoFactory.create(
            session=session,
            chave="diaInicioPeriodo",
            valor="25"
        )

        response = client.get("/configuracoes/diaInicioPeriodo")

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "diaInicioPeriodo"
        assert data["valor"] == "25"

    def test_obter_criterio_data_transacao(self, client: TestClient, session: Session):
        """Deve retornar configuração de criterio_data_transacao."""
        ConfiguracaoFactory.create(
            session=session,
            chave="criterio_data_transacao",
            valor="data_fatura"
        )

        response = client.get("/configuracoes/criterio_data_transacao")

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "criterio_data_transacao"
        assert data["valor"] == "data_fatura"


class TestSalvarConfiguracao:
    """Testes para POST /configuracoes/"""

    def test_criar_nova_configuracao(self, client: TestClient, session: Session):
        """Deve criar nova configuração."""
        config_data = {
            "chave": "nova_config",
            "valor": "novo_valor"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "nova_config"
        assert data["valor"] == "novo_valor"

        # Verifica se foi salvo no banco
        response_get = client.get("/configuracoes/nova_config")
        assert response_get.json()["valor"] == "novo_valor"

    def test_atualizar_configuracao_existente(self, client: TestClient, session: Session):
        """Deve atualizar configuração existente."""
        config = ConfiguracaoFactory.create(
            session=session,
            chave="config_atualizar",
            valor="valor_antigo"
        )

        config_data = {
            "chave": "config_atualizar",
            "valor": "valor_novo"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "config_atualizar"
        assert data["valor"] == "valor_novo"

        # Verifica se foi atualizado
        response_get = client.get("/configuracoes/config_atualizar")
        assert response_get.json()["valor"] == "valor_novo"

    def test_salvar_dia_inicio_periodo_valido(self, client: TestClient):
        """Deve salvar diaInicioPeriodo com valor válido (1-28)."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "25"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "diaInicioPeriodo"
        assert data["valor"] == "25"

    def test_salvar_dia_inicio_periodo_limite_inferior(self, client: TestClient):
        """Deve aceitar dia 1 como limite inferior."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "1"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["valor"] == "1"

    def test_salvar_dia_inicio_periodo_limite_superior(self, client: TestClient):
        """Deve aceitar dia 28 como limite superior."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "28"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["valor"] == "28"

    def test_salvar_dia_inicio_periodo_menor_que_1(self, client: TestClient):
        """Deve rejeitar diaInicioPeriodo menor que 1."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "0"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 400
        assert "deve estar entre 1 e 28" in response.json()["detail"]

    def test_salvar_dia_inicio_periodo_maior_que_28(self, client: TestClient):
        """Deve rejeitar diaInicioPeriodo maior que 28."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "29"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 400
        assert "deve estar entre 1 e 28" in response.json()["detail"]

    def test_salvar_dia_inicio_periodo_nao_numerico(self, client: TestClient):
        """Deve rejeitar diaInicioPeriodo não numérico."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "abc"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 400
        assert "deve ser um número válido" in response.json()["detail"]

    def test_salvar_dia_inicio_periodo_decimal(self, client: TestClient):
        """Deve rejeitar diaInicioPeriodo decimal."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "15.5"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 400
        assert "número válido" in response.json()["detail"]

    def test_salvar_criterio_data_transacao_valido(self, client: TestClient):
        """Deve salvar criterio_data_transacao com valor 'data_transacao'."""
        config_data = {
            "chave": "criterio_data_transacao",
            "valor": "data_transacao"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "criterio_data_transacao"
        assert data["valor"] == "data_transacao"

    def test_salvar_criterio_data_fatura_valido(self, client: TestClient):
        """Deve salvar criterio_data_transacao com valor 'data_fatura'."""
        config_data = {
            "chave": "criterio_data_transacao",
            "valor": "data_fatura"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "criterio_data_transacao"
        assert data["valor"] == "data_fatura"

    def test_salvar_criterio_data_transacao_invalido(self, client: TestClient):
        """Deve rejeitar criterio_data_transacao com valor inválido."""
        config_data = {
            "chave": "criterio_data_transacao",
            "valor": "valor_invalido"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "criterio_data_transacao deve ser um dos valores" in detail
        assert "data_transacao" in detail
        assert "data_fatura" in detail

    def test_salvar_configuracao_generica_sem_validacao(self, client: TestClient):
        """Deve permitir salvar configurações genéricas sem validação específica."""
        config_data = {
            "chave": "alguma_config_customizada",
            "valor": "qualquer_valor_aqui"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["chave"] == "alguma_config_customizada"
        assert data["valor"] == "qualquer_valor_aqui"


class TestAtualizarConfiguracao:
    """Testes para atualização de configurações existentes."""

    def test_atualizar_dia_inicio_periodo(self, client: TestClient, session: Session):
        """Deve atualizar diaInicioPeriodo existente."""
        ConfiguracaoFactory.create(
            session=session,
            chave="diaInicioPeriodo",
            valor="1"
        )

        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "15"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["valor"] == "15"

        # Verifica atualização
        response_get = client.get("/configuracoes/diaInicioPeriodo")
        assert response_get.json()["valor"] == "15"

    def test_atualizar_criterio_data(self, client: TestClient, session: Session):
        """Deve atualizar criterio_data_transacao existente."""
        ConfiguracaoFactory.create(
            session=session,
            chave="criterio_data_transacao",
            valor="data_transacao"
        )

        config_data = {
            "chave": "criterio_data_transacao",
            "valor": "data_fatura"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["valor"] == "data_fatura"

        # Verifica atualização
        response_get = client.get("/configuracoes/criterio_data_transacao")
        assert response_get.json()["valor"] == "data_fatura"

    def test_multiplas_atualizacoes_mesma_config(self, client: TestClient, session: Session):
        """Deve permitir múltiplas atualizações na mesma configuração."""
        ConfiguracaoFactory.create(
            session=session,
            chave="config_multipla",
            valor="valor1"
        )

        # Primeira atualização
        response1 = client.post("/configuracoes/", json={
            "chave": "config_multipla",
            "valor": "valor2"
        })
        assert response1.status_code == 200
        assert response1.json()["valor"] == "valor2"

        # Segunda atualização
        response2 = client.post("/configuracoes/", json={
            "chave": "config_multipla",
            "valor": "valor3"
        })
        assert response2.status_code == 200
        assert response2.json()["valor"] == "valor3"

        # Terceira atualização
        response3 = client.post("/configuracoes/", json={
            "chave": "config_multipla",
            "valor": "valor_final"
        })
        assert response3.status_code == 200
        assert response3.json()["valor"] == "valor_final"

        # Verifica valor final
        response_get = client.get("/configuracoes/config_multipla")
        assert response_get.json()["valor"] == "valor_final"


class TestEdgeCasesConfiguracoes:
    """Testes de casos extremos e edge cases."""

    def test_chave_com_espacos(self, client: TestClient):
        """Deve permitir chaves com espaços."""
        config_data = {
            "chave": "minha config com espacos",
            "valor": "valor"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["chave"] == "minha config com espacos"

    def test_chave_vazia(self, client: TestClient):
        """Deve permitir chave vazia (sem validação específica no modelo)."""
        config_data = {
            "chave": "",
            "valor": "valor"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["chave"] == ""
        assert response.json()["valor"] == "valor"

    def test_valor_vazio(self, client: TestClient):
        """Deve permitir valor vazio."""
        config_data = {
            "chave": "config_valor_vazio",
            "valor": ""
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["valor"] == ""

    def test_valor_muito_longo(self, client: TestClient):
        """Deve permitir valores longos (texto extenso)."""
        valor_longo = "x" * 10000  # 10k caracteres
        config_data = {
            "chave": "config_valor_longo",
            "valor": valor_longo
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["valor"] == valor_longo

    def test_chave_com_caracteres_especiais(self, client: TestClient):
        """Deve permitir chaves com caracteres especiais."""
        config_data = {
            "chave": "config-com_underline.e-hifen",
            "valor": "valor"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["chave"] == "config-com_underline.e-hifen"

    def test_chave_com_unicode(self, client: TestClient):
        """Deve permitir chaves com caracteres Unicode."""
        config_data = {
            "chave": "configuração_em_português",
            "valor": "valor_com_acentuação"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 200
        assert response.json()["chave"] == "configuração_em_português"
        assert response.json()["valor"] == "valor_com_acentuação"

    def test_dia_inicio_periodo_negativo(self, client: TestClient):
        """Deve rejeitar diaInicioPeriodo negativo."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "-5"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 400
        assert "deve estar entre 1 e 28" in response.json()["detail"]

    def test_dia_inicio_periodo_muito_grande(self, client: TestClient):
        """Deve rejeitar diaInicioPeriodo muito grande (>28)."""
        config_data = {
            "chave": "diaInicioPeriodo",
            "valor": "31"
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 400
        assert "deve estar entre 1 e 28" in response.json()["detail"]

    def test_criterio_data_case_sensitive(self, client: TestClient):
        """Deve rejeitar criterio_data_transacao com case diferente."""
        config_data = {
            "chave": "criterio_data_transacao",
            "valor": "DATA_TRANSACAO"  # Uppercase
        }

        response = client.post("/configuracoes/", json=config_data)

        assert response.status_code == 400
        assert "criterio_data_transacao deve ser um dos valores" in response.json()["detail"]

    def test_obter_multiplas_configuracoes_diferentes(self, client: TestClient, session: Session):
        """Deve permitir obter múltiplas configurações diferentes."""
        ConfiguracaoFactory.create(session=session, chave="config1", valor="valor1")
        ConfiguracaoFactory.create(session=session, chave="config2", valor="valor2")
        ConfiguracaoFactory.create(session=session, chave="config3", valor="valor3")

        response1 = client.get("/configuracoes/config1")
        response2 = client.get("/configuracoes/config2")
        response3 = client.get("/configuracoes/config3")

        assert response1.json()["valor"] == "valor1"
        assert response2.json()["valor"] == "valor2"
        assert response3.json()["valor"] == "valor3"
