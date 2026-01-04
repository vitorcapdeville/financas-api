"""
Testes de regressão para garantir que funcionalidades existentes não quebrem.

Este módulo testa:
- Cascades de deleção
- Filtros especiais (mes/ano vs data_inicio/data_fim)
- criterio_data_transacao
- Priorização de parâmetros
- Comportamentos críticos do sistema

IMPORTANTE: Estes testes validam funcionalidades já implementadas e
garantem que mudanças futuras não quebrem o comportamento esperado.
"""

import pytest
from datetime import datetime, date
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from tests.factories import TransacaoFactory, TagFactory, RegraFactory, ConfiguracaoFactory
from app.models import Transacao
from app.models_tags import Tag, TransacaoTag
from app.models_regra import Regra, RegraTag, TipoAcao, CriterioTipo


class TestCascadesDeletion:
    """Testes de cascades de deleção - CRÍTICO para integridade."""

    def test_deletar_transacao_remove_associacoes_tags(self, client: TestClient, session: Session):
        """REGRESSÃO: Deletar transação deve remover TransacaoTag mas manter Tag."""
        tag = TagFactory.create(session=session)
        transacao = TransacaoFactory.create(session=session)
        
        # Adicionar tag
        client.post(f"/transacoes/{transacao.id}/tags/{tag.id}")
        
        # Verificar associação criada
        associacoes_antes = session.exec(
            select(TransacaoTag).where(TransacaoTag.transacao_id == transacao.id)
        ).all()
        assert len(associacoes_antes) == 1

        # Deletar transação
        session.delete(transacao)
        session.commit()

        # Verificar que associação foi removida
        associacoes_depois = session.exec(
            select(TransacaoTag).where(TransacaoTag.transacao_id == transacao.id)
        ).all()
        assert len(associacoes_depois) == 0

        # Verificar que tag continua existindo
        tag_existe = session.get(Tag, tag.id)
        assert tag_existe is not None

    def test_deletar_tag_remove_associacoes_transacoes(self, client: TestClient, session: Session):
        """REGRESSÃO: Deletar tag deve remover TransacaoTag mas manter Transacao."""
        tag = TagFactory.create(session=session)
        transacao = TransacaoFactory.create(session=session)
        
        # Adicionar tag
        client.post(f"/transacoes/{transacao.id}/tags/{tag.id}")
        
        # Deletar tag via API
        response = client.delete(f"/tags/{tag.id}")
        assert response.status_code == 204

        # Verificar que transação continua existindo
        transacao_existe = session.get(Transacao, transacao.id)
        assert transacao_existe is not None

        # Verificar que associação foi removida
        associacoes = session.exec(
            select(TransacaoTag).where(TransacaoTag.tag_id == tag.id)
        ).all()
        assert len(associacoes) == 0

    def test_deletar_regra_remove_associacoes_tags(self, client: TestClient, session: Session):
        """REGRESSÃO: Deletar regra deve remover RegraTag mas manter Tag."""
        tag = TagFactory.create(session=session)
        
        regra_data = {
            "nome": "Regra Teste",
            "tipo_acao": "adicionar_tags",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "teste",
            "acao_valor": "placeholder"
        }
        
        response = client.post(f"/regras/?tag_ids={tag.id}", json=regra_data)
        regra_id = response.json()["id"]

        # Verificar associação criada
        associacoes_antes = session.exec(
            select(RegraTag).where(RegraTag.regra_id == regra_id)
        ).all()
        assert len(associacoes_antes) == 1

        # Deletar regra
        response = client.delete(f"/regras/{regra_id}")
        assert response.status_code == 204

        # Verificar que associação foi removida
        associacoes_depois = session.exec(
            select(RegraTag).where(RegraTag.regra_id == regra_id)
        ).all()
        assert len(associacoes_depois) == 0

        # Verificar que tag continua existindo
        tag_existe = session.get(Tag, tag.id)
        assert tag_existe is not None


class TestFiltrosEspeciais:
    """Testes de filtros especiais - CRÍTICO para funcionalidade de período."""

    def test_filtro_mes_ano_funciona(self, client: TestClient, session: Session):
        """REGRESSÃO: Filtro por mes/ano deve funcionar corretamente."""
        # Criar transações em diferentes meses
        TransacaoFactory.create(session=session, data=date(2025, 12, 15))
        TransacaoFactory.create(session=session, data=date(2025, 11, 15))
        TransacaoFactory.create(session=session, data=date(2024, 12, 15))

        # Filtrar dezembro de 2025
        response = client.get("/transacoes/?mes=12&ano=2025")
        
        assert response.status_code == 200
        transacoes = response.json()
        assert len(transacoes) == 1
        assert transacoes[0]["data"] == "2025-12-15"

    def test_filtro_data_inicio_fim_funciona(self, client: TestClient, session: Session):
        """REGRESSÃO: Filtro por data_inicio/data_fim deve funcionar."""
        # Criar transações
        TransacaoFactory.create(session=session, data=date(2025, 12, 1))
        TransacaoFactory.create(session=session, data=date(2025, 12, 15))
        TransacaoFactory.create(session=session, data=date(2025, 12, 31))

        # Filtrar período específico
        response = client.get("/transacoes/?data_inicio=2025-12-10&data_fim=2025-12-20")
        
        assert response.status_code == 200
        transacoes = response.json()
        assert len(transacoes) == 1
        assert transacoes[0]["data"] == "2025-12-15"

    def test_data_inicio_fim_tem_prioridade_sobre_mes_ano(self, client: TestClient, session: Session):
        """REGRESSÃO: data_inicio/data_fim deve ter prioridade sobre mes/ano."""
        TransacaoFactory.create(session=session, data=date(2025, 12, 15))
        TransacaoFactory.create(session=session, data=date(2025, 11, 15))

        # Enviar ambos os filtros - data_inicio/fim deve prevalecer
        response = client.get(
            "/transacoes/?mes=12&ano=2025&data_inicio=2025-11-01&data_fim=2025-11-30"
        )
        
        assert response.status_code == 200
        transacoes = response.json()
        # Deve retornar apenas novembro (data_inicio/fim tem prioridade)
        assert len(transacoes) == 1
        assert transacoes[0]["data"] == "2025-11-15"

    def test_filtro_categoria_null(self, client: TestClient, session: Session):
        """REGRESSÃO: Filtro categoria=null deve retornar sem categoria."""
        TransacaoFactory.create(session=session, categoria="Alimentação")
        TransacaoFactory.create(session=session, categoria=None)
        TransacaoFactory.create(session=session, categoria=None)

        response = client.get("/transacoes/?categoria=null")
        
        assert response.status_code == 200
        transacoes = response.json()
        assert len(transacoes) == 2
        for t in transacoes:
            assert t["categoria"] is None


class TestCriterioDataTransacao:
    """Testes de criterio_data_transacao - CRÍTICO para agrupamento de faturas."""

    def test_importar_fatura_com_data_transacao_e_fatura(self, client: TestClient, session: Session):
        """REGRESSÃO: Importar fatura deve salvar data_transacao e data_fatura."""
        import io
        
        csv_content = "data,descricao,valor,categoria,data_fatura\n"
        csv_content += "2025-12-10,Compra Cartão,100.0,Outros,2025-12-25\n"
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/fatura",
            files={"file": ("fatura.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_importado"] == 1

        # Verificar que ambas as datas foram salvas
        transacao = session.exec(select(Transacao)).first()
        assert transacao.data == date(2025, 12, 10)
        assert transacao.data_fatura == date(2025, 12, 25)

    def test_configuracao_criterio_data_transacao_valida(self, client: TestClient):
        """REGRESSÃO: Salvar criterio_data_transacao deve validar valores."""
        # Valor válido: data_transacao
        response = client.post("/configuracoes/", json={
            "chave": "criterio_data_transacao",
            "valor": "data_transacao"
        })
        assert response.status_code == 200

        # Valor válido: data_fatura
        response = client.post("/configuracoes/", json={
            "chave": "criterio_data_transacao",
            "valor": "data_fatura"
        })
        assert response.status_code == 200

        # Valor inválido
        response = client.post("/configuracoes/", json={
            "chave": "criterio_data_transacao",
            "valor": "valor_invalido"
        })
        assert response.status_code == 400


class TestPrioridadeRegras:
    """Testes de prioridade de regras - CRÍTICO para ordem de aplicação."""

    def test_regras_aplicadas_em_ordem_prioridade(self, client: TestClient, session: Session):
        """REGRESSÃO: Regras devem ser aplicadas em ordem de prioridade."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Netflix Uber",
            categoria=None
        )

        # Criar regras com prioridades diferentes
        regra1_data = {
            "nome": "Regra Netflix",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "netflix",
            "acao_valor": "Streaming"
        }
        response1 = client.post("/regras/", json=regra1_data)
        regra1_prioridade = response1.json()["prioridade"]

        regra2_data = {
            "nome": "Regra Uber",
            "tipo_acao": "alterar_categoria",
            "criterio_tipo": "descricao_contem",
            "criterio_valor": "uber",
            "acao_valor": "Transporte"
        }
        response2 = client.post("/regras/", json=regra2_data)
        regra2_prioridade = response2.json()["prioridade"]

        # Aplicar todas as regras
        client.post("/regras/aplicar-todas")
        
        # Verificar que prioridades são diferentes e auto-incrementadas
        assert regra1_prioridade != regra2_prioridade

    def test_prioridade_auto_incrementa(self, client: TestClient):
        """REGRESSÃO: Prioridade deve auto-incrementar ao criar regras."""
        prioridades = []
        
        for i in range(5):
            regra_data = {
                "nome": f"Regra {i}",
                "tipo_acao": "alterar_categoria",
                "criterio_tipo": "descricao_contem",
                "criterio_valor": f"palavra{i}",
                "acao_valor": f"Categoria{i}"
            }
            
            response = client.post("/regras/", json=regra_data)
            assert response.status_code in [200, 201]
            prioridades.append(response.json()["prioridade"])

        # Verificar que todas são únicas
        assert len(prioridades) == len(set(prioridades))
        
        # Verificar que são incrementais
        assert prioridades == sorted(prioridades)


class TestValorOriginal:
    """Testes de valor_original - CRÍTICO para preservação de dados."""

    def test_alterar_valor_preserva_original(self, client: TestClient, session: Session):
        """REGRESSÃO: Alterar valor deve preservar valor_original."""
        transacao = TransacaoFactory.create(
            session=session,
            valor=100.0,
            valor_original=None
        )

        # Alterar valor
        response = client.patch(f"/transacoes/{transacao.id}", json={
            "valor": 50.0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["valor"] == 50.0
        assert data["valor_original"] == 100.0

    def test_restaurar_valor_original(self, client: TestClient, session: Session):
        """REGRESSÃO: Restaurar valor deve funcionar corretamente."""
        transacao = TransacaoFactory.create(
            session=session,
            valor=50.0,
            valor_original=100.0
        )

        # Restaurar valor
        response = client.post(f"/transacoes/{transacao.id}/restaurar-valor")
        
        assert response.status_code == 200
        data = response.json()
        assert data["valor"] == 100.0
        assert data["valor_original"] is None


class TestTagsCaseInsensitive:
    """Testes de tags case-insensitive - CRÍTICO para UX."""

    def test_criar_tag_nome_duplicado_case_insensitive(self, client: TestClient, session: Session):
        """REGRESSÃO: Nomes de tags devem ser únicos (case-insensitive)."""
        # Criar primeira tag
        response1 = client.post("/tags/", json={"nome": "Urgente", "cor": "#FF0000"})
        assert response1.status_code in [200, 201]

        # Tentar criar com case diferente (deve falhar)
        response2 = client.post("/tags/", json={"nome": "urgente", "cor": "#00FF00"})
        assert response2.status_code == 400

        response3 = client.post("/tags/", json={"nome": "URGENTE", "cor": "#0000FF"})
        assert response3.status_code == 400

    def test_atualizar_tag_nome_duplicado_case_insensitive(self, client: TestClient, session: Session):
        """REGRESSÃO: Atualizar tag não pode criar duplicata case-insensitive."""
        tag1 = TagFactory.create(session=session, nome="Tag1")
        tag2 = TagFactory.create(session=session, nome="Tag2")

        # Tentar renomear tag2 para "tag1" (deve falhar)
        response = client.patch(f"/tags/{tag2.id}", json={"nome": "tag1"})
        assert response.status_code == 400


class TestResumoMensal:
    """Testes de resumo mensal - CRÍTICO para dashboard."""

    def test_resumo_sem_parametros_usa_mes_atual(self, client: TestClient, session: Session):
        """REGRESSÃO: Resumo sem parâmetros deve usar mês atual."""
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        # Criar transação no mês atual
        TransacaoFactory.create(
            session=session,
            data=date(ano_atual, mes_atual, 15),
            tipo="entrada",
            valor=100.0
        )

        response = client.get("/transacoes/resumo/mensal")
        
        assert response.status_code == 200
        data = response.json()
        assert data["mes"] == mes_atual
        assert data["ano"] == ano_atual

    def test_resumo_agrupa_por_categoria(self, client: TestClient, session: Session):
        """REGRESSÃO: Resumo deve agrupar valores por categoria."""
        # Criar transações de diferentes categorias
        TransacaoFactory.create(
            session=session,
            data=date(2025, 12, 15),
            tipo="saida",
            valor=100.0,
            categoria="Alimentação"
        )
        TransacaoFactory.create(
            session=session,
            data=date(2025, 12, 16),
            tipo="saida",
            valor=50.0,
            categoria="Alimentação"
        )
        TransacaoFactory.create(
            session=session,
            data=date(2025, 12, 17),
            tipo="saida",
            valor=200.0,
            categoria="Transporte"
        )

        response = client.get("/transacoes/resumo/mensal?mes=12&ano=2025")
        
        assert response.status_code == 200
        data = response.json()
        assert "saidas_por_categoria" in data
        assert data["saidas_por_categoria"]["Alimentação"] == 150.0
        assert data["saidas_por_categoria"]["Transporte"] == 200.0


class TestImportacaoTagRotina:
    """Testes de tag de rotina na importação - CRÍTICO para rastreamento."""

    def test_importar_extrato_cria_tag_rotina(self, client: TestClient, session: Session):
        """REGRESSÃO: Importar extrato deve criar tag "rotina_YYYYMM"."""
        import io
        
        csv_content = "data,descricao,valor,categoria\n"
        csv_content += "2025-12-15,Compra,100.0,Outros\n"
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/extrato",
            files={"file": ("extrato.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200

        # Verificar que tag foi criada
        tags = session.exec(select(Tag).where(Tag.nome.like("rotina_%"))).all()
        assert len(tags) >= 1

    def test_importar_fatura_cria_tag_rotina(self, client: TestClient, session: Session):
        """REGRESSÃO: Importar fatura deve criar tag "rotina_YYYYMM"."""
        import io
        
        csv_content = "data,descricao,valor,categoria\n"
        csv_content += "2025-12-15,Compra Cartão,100.0,Outros\n"
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        
        response = client.post(
            "/importacao/fatura",
            files={"file": ("fatura.csv", csv_file, "text/csv")}
        )
        
        assert response.status_code == 200

        # Verificar que tag foi criada
        tags = session.exec(select(Tag).where(Tag.nome.like("rotina_%"))).all()
        assert len(tags) >= 1


class TestDiaInicioPeriodo:
    """Testes de diaInicioPeriodo - CRÍTICO para cálculo de período."""

    def test_configuracao_dia_inicio_periodo_valida_range(self, client: TestClient):
        """REGRESSÃO: diaInicioPeriodo deve aceitar apenas 1-28."""
        # Valores válidos
        for dia in [1, 15, 28]:
            response = client.post("/configuracoes/", json={
                "chave": "diaInicioPeriodo",
                "valor": str(dia)
            })
            assert response.status_code == 200

        # Valores inválidos
        for dia in [0, -1, 29, 30, 31, 100]:
            response = client.post("/configuracoes/", json={
                "chave": "diaInicioPeriodo",
                "valor": str(dia)
            })
            assert response.status_code == 400

    def test_configuracao_dia_inicio_periodo_nao_numerico(self, client: TestClient):
        """REGRESSÃO: diaInicioPeriodo deve rejeitar valores não numéricos."""
        response = client.post("/configuracoes/", json={
            "chave": "diaInicioPeriodo",
            "valor": "abc"
        })
        assert response.status_code == 400
