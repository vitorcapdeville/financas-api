"""
Testes unitários para app/services/regras.py.

Testa toda a lógica de negócio relacionada a regras automáticas:
- Verificação de match de critérios
- Aplicação de regras em transações
- Aplicação em massa
- Tratamento de erros
- Edge cases
"""

import pytest
import json
from datetime import date
from sqlmodel import Session

from app.models import Transacao, TipoTransacao
from app.models_tags import Tag, TransacaoTag
from app.models_regra import Regra, RegraTag, TipoAcao, CriterioTipo
from app.services.regras import (
    verificar_transacao_match_criterio,
    aplicar_regra_em_transacao,
    aplicar_todas_regras_ativas,
    calcular_proxima_prioridade,
    aplicar_regra_em_todas_transacoes,
    aplicar_todas_regras_em_todas_transacoes,
)
from tests.factories import TransacaoFactory, TagFactory, RegraFactory


class TestVerificarTransacaoMatchCriterio:
    """Testes para verificar_transacao_match_criterio()."""

    def test_descricao_exata_match(self, session: Session):
        """Testa match com descrição exata."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Netflix",
            valor=50.0,
            tipo=TipoTransacao.SAIDA,
        )
        regra = Regra(
            nome="Regra Netflix",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Netflix",
            acao_valor="Streaming",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is True

    def test_descricao_exata_case_insensitive(self, session: Session):
        """Testa que match é case-insensitive."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="NETFLIX",
            valor=50.0,
            tipo=TipoTransacao.SAIDA,
        )
        regra = Regra(
            nome="Regra Netflix",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="netflix",
            acao_valor="Streaming",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is True

    def test_descricao_exata_no_match(self, session: Session):
        """Testa que não faz match se descrição diferente."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Spotify",
            valor=30.0,
            tipo=TipoTransacao.SAIDA,
        )
        regra = Regra(
            nome="Regra Netflix",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Netflix",
            acao_valor="Streaming",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is False

    def test_descricao_contem_match(self, session: Session):
        """Testa match com descrição contém substring."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Uber viagem centro",
            valor=25.50,
            tipo=TipoTransacao.SAIDA,
        )
        regra = Regra(
            nome="Regra Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is True

    def test_descricao_contem_case_insensitive(self, session: Session):
        """Testa que substring é case-insensitive."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="UBER EATS PEDIDO",
            valor=40.0,
            tipo=TipoTransacao.SAIDA,
        )
        regra = Regra(
            nome="Regra Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is True

    def test_descricao_contem_no_match(self, session: Session):
        """Testa que não faz match se substring não existe."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="99 Taxi",
            valor=20.0,
            tipo=TipoTransacao.SAIDA,
        )
        regra = Regra(
            nome="Regra Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is False

    def test_categoria_match(self, session: Session):
        """Testa match por categoria."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Compra qualquer",
            valor=100.0,
            tipo=TipoTransacao.SAIDA,
            categoria="Alimentação",
        )
        regra = Regra(
            nome="Regra Alimentação",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Alimentação",
            acao_valor="[]",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is True

    def test_categoria_case_insensitive(self, session: Session):
        """Testa que categoria é case-insensitive."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Compra qualquer",
            valor=100.0,
            tipo=TipoTransacao.SAIDA,
            categoria="ALIMENTAÇÃO",
        )
        regra = Regra(
            nome="Regra Alimentação",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="alimentação",
            acao_valor="[]",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is True

    def test_categoria_none_no_match(self, session: Session):
        """Testa que transação sem categoria não faz match."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Sem categoria",
            valor=100.0,
            tipo=TipoTransacao.SAIDA,
            categoria=None,
        )
        regra = Regra(
            nome="Regra Alimentação",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Alimentação",
            acao_valor="[]",
            prioridade=1,
        )

        assert verificar_transacao_match_criterio(transacao, regra) is False


class TestAplicarRegraEmTransacao:
    """Testes para aplicar_regra_em_transacao()."""

    def test_alterar_categoria(self, session: Session):
        """Testa aplicação de regra ALTERAR_CATEGORIA."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Uber viagem",
            categoria=None,
        )
        regra = Regra(
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="Uber",
            acao_valor="Transporte",
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        resultado = aplicar_regra_em_transacao(regra, transacao, session)
        session.commit()
        session.refresh(transacao)

        assert resultado is True
        assert transacao.categoria == "Transporte"

    def test_alterar_categoria_sobrescreve_existente(self, session: Session):
        """Testa que nova categoria sobrescreve a antiga."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Uber viagem",
            categoria="Outros",
        )
        regra = Regra(
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        aplicar_regra_em_transacao(regra, transacao, session)
        session.commit()
        session.refresh(transacao)

        assert transacao.categoria == "Transporte"

    def test_adicionar_tags(self, session: Session):
        """Testa aplicação de regra ADICIONAR_TAGS."""
        transacao = TransacaoFactory.create(session=session)
        tag1 = TagFactory.create(session=session, nome="Tag1")
        tag2 = TagFactory.create(session=session, nome="Tag2")

        regra = Regra(
            nome="Adicionar Tags",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor=transacao.descricao,
            acao_valor=json.dumps([tag1.id, tag2.id]),
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        resultado = aplicar_regra_em_transacao(regra, transacao, session)

        assert resultado is True
        session.commit()
        # Verificar tags adicionadas
        tags_associadas = session.exec(
            TransacaoTag.__table__.select().where(TransacaoTag.transacao_id == transacao.id)
        ).all()
        assert len(tags_associadas) == 2

    def test_adicionar_tags_evita_duplicatas(self, session: Session):
        """Testa que tags duplicadas não são adicionadas."""
        transacao = TransacaoFactory.create(session=session)
        tag = TagFactory.create(session=session)

        # Adicionar tag manualmente
        transacao_tag = TransacaoTag(transacao_id=transacao.id, tag_id=tag.id)
        session.add(transacao_tag)
        session.commit()

        # Aplicar regra que tentaria adicionar a mesma tag
        regra = Regra(
            nome="Adicionar Tag",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="test",
            acao_valor=json.dumps([tag.id]),
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        aplicar_regra_em_transacao(regra, transacao, session)

        # Verificar que não foi duplicada
        from sqlmodel import select

        tags_count = len(session.exec(select(TransacaoTag).where(TransacaoTag.transacao_id == transacao.id)).all())
        assert tags_count == 1

    @pytest.mark.edge_case
    def test_adicionar_tags_json_invalido(self, session: Session):
        """EDGE CASE: JSON inválido retorna False silenciosamente."""
        transacao = TransacaoFactory.create(session=session)

        regra = Regra(
            nome="JSON Inválido",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="test",
            acao_valor="[invalid json",  # JSON malformado
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        resultado = aplicar_regra_em_transacao(regra, transacao, session)

        # Retorna False mas não lança exceção
        assert resultado is False

    @pytest.mark.edge_case
    def test_adicionar_tags_tag_deletada(self, session: Session):
        """EDGE CASE: Tag deletada após criação da regra causa erro silencioso."""
        transacao = TransacaoFactory.create(session=session)
        tag = TagFactory.create(session=session)

        regra = Regra(
            nome="Tag Deletada",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor=transacao.descricao,
            acao_valor=json.dumps([tag.id]),
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        # Deletar tag
        session.delete(tag)
        session.commit()

        # Aplicar regra (tag não existe mais)
        resultado = aplicar_regra_em_transacao(regra, transacao, session)
        session.commit()
        # Não adiciona nada, retorna True
        assert resultado is True

    def test_alterar_valor_com_percentual(self, session: Session):
        """Testa aplicação de regra ALTERAR_VALOR."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Netflix",
            valor=50.0,
            valor_original=None,
        )

        regra = Regra(
            nome="Desconto Netflix",
            tipo_acao=TipoAcao.ALTERAR_VALOR,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Netflix",
            acao_valor="10",  # 10% de desconto
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        resultado = aplicar_regra_em_transacao(regra, transacao, session)
        session.commit()
        session.refresh(transacao)

        assert resultado is True
        assert transacao.valor_original == 50.0  # Preservado
        assert transacao.valor == 5.0  # 10% de 50

    def test_alterar_valor_usa_valor_original_como_base(self, session: Session):
        """Testa que usa valor_original se já existir."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Netflix",
            valor=5.0,  # Já modificado
            valor_original=50.0,  # Valor original
        )

        regra = Regra(
            nome="Desconto Netflix",
            tipo_acao=TipoAcao.ALTERAR_VALOR,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Netflix",
            acao_valor="20",  # 20% de desconto
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        aplicar_regra_em_transacao(regra, transacao, session)
        session.commit()
        session.refresh(transacao)

        assert transacao.valor_original == 50.0  # Não muda
        assert transacao.valor == 10.0  # 20% de 50 (não de 5)

    @pytest.mark.edge_case
    def test_alterar_valor_percentual_zero(self, session: Session):
        """EDGE CASE: Percentual 0 zera o valor (pode não ser desejado)."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Teste",
            valor=100.0,
        )

        regra = Regra(
            nome="Zerar Valor",
            tipo_acao=TipoAcao.ALTERAR_VALOR,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Teste",
            acao_valor="0",
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        aplicar_regra_em_transacao(regra, transacao, session)
        session.commit()
        session.refresh(transacao)

        assert transacao.valor == 0.0
        # TODO: Considerar se percentual 0 deve ser permitido

    @pytest.mark.edge_case
    def test_alterar_valor_conversao_invalida(self, session: Session):
        """EDGE CASE: Conversão de percentual inválida retorna False."""
        transacao = TransacaoFactory.create(session=session)

        regra = Regra(
            nome="Percentual Inválido",
            tipo_acao=TipoAcao.ALTERAR_VALOR,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="test",
            acao_valor="não_é_número",
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        resultado = aplicar_regra_em_transacao(regra, transacao, session)

        assert resultado is False


class TestAplicarTodasRegrasAtivas:
    """Testes para aplicar_todas_regras_ativas()."""

    def test_aplicar_multiplas_regras_em_ordem_prioridade(self, session: Session):
        """Testa que regras são aplicadas em ordem de prioridade."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Uber eats pedido",
            categoria=None,
        )

        # Regra de menor prioridade (executada depois)
        regra1 = Regra(
            nome="Regra 1",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="Uber",
            acao_valor="Transporte",
            prioridade=1,
            ativo=True,
        )

        # Regra de maior prioridade (executada primeiro)
        regra2 = Regra(
            nome="Regra 2",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="eats",
            acao_valor="Alimentação",
            prioridade=2,
            ativo=True,
        )

        session.add(regra1)
        session.add(regra2)
        session.commit()

        count = aplicar_todas_regras_ativas(transacao, session)
        session.commit()
        session.refresh(transacao)

        assert count == 2
        # Regra1 foi aplicada por último então categoria é dela
        assert transacao.categoria == "Transporte"

    def test_aplicar_apenas_regras_ativas(self, session: Session):
        """Testa que apenas regras ativas são aplicadas."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Teste",
        )

        regra_ativa = Regra(
            nome="Ativa",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Teste",
            acao_valor="Categoria1",
            prioridade=1,
            ativo=True,
        )

        regra_inativa = Regra(
            nome="Inativa",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Teste",
            acao_valor="Categoria2",
            prioridade=2,
            ativo=False,  # Inativa
        )

        session.add(regra_ativa)
        session.add(regra_inativa)
        session.commit()

        count = aplicar_todas_regras_ativas(transacao, session)
        session.commit()
        session.refresh(transacao)

        assert count == 1
        assert transacao.categoria == "Categoria1"

    def test_nenhuma_regra_aplicavel(self, session: Session):
        """Testa quando nenhuma regra faz match."""
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Descrição sem match",
        )

        regra = Regra(
            nome="Regra",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Outro texto",
            acao_valor="Categoria",
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        count = aplicar_todas_regras_ativas(transacao, session)

        assert count == 0


class TestCalcularProximaPrioridade:
    """Testes para calcular_proxima_prioridade()."""

    def test_primeira_regra(self, session: Session):
        """Testa prioridade quando não há regras."""
        prioridade = calcular_proxima_prioridade(session)
        assert prioridade == 1

    def test_com_regras_existentes(self, session: Session):
        """Testa prioridade quando já existem regras."""
        RegraFactory.create(session=session, prioridade=5)
        RegraFactory.create(session=session, prioridade=3)
        RegraFactory.create(session=session, prioridade=8)

        prioridade = calcular_proxima_prioridade(session)
        assert prioridade == 9  # max(5,3,8) + 1


class TestAplicarRegraEmTodasTransacoes:
    """Testes para aplicar_regra_em_todas_transacoes()."""

    def test_aplicar_em_multiplas_transacoes(self, session: Session):
        """Testa aplicação de regra em várias transações."""
        # Criar transações que fazem match
        t1 = TransacaoFactory.create(session=session, descricao="Uber viagem 1")
        t2 = TransacaoFactory.create(session=session, descricao="Uber viagem 2")
        t3 = TransacaoFactory.create(session=session, descricao="Taxi")  # Não match

        regra = Regra(
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            prioridade=1,
            ativo=True,
        )
        session.add(regra)
        session.commit()

        count = aplicar_regra_em_todas_transacoes(regra.id, session)

        assert count == 2

        session.refresh(t1)
        session.refresh(t2)
        session.refresh(t3)

        assert t1.categoria == "Transporte"
        assert t2.categoria == "Transporte"
        assert t3.categoria != "Transporte"


class TestAplicarTodasRegrasEmTodasTransacoes:
    """Testes para aplicar_todas_regras_em_todas_transacoes()."""

    def test_aplicar_todas_em_todas(self, session: Session):
        """Testa aplicação massiva de todas regras."""
        # Criar transações
        t1 = TransacaoFactory.create(session=session, descricao="Netflix")
        t2 = TransacaoFactory.create(session=session, descricao="Uber viagem")

        # Criar regras
        regra1 = Regra(
            nome="Categorizar Netflix",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Netflix",
            acao_valor="Streaming",
            prioridade=1,
            ativo=True,
        )
        regra2 = Regra(
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="Uber",
            acao_valor="Transporte",
            prioridade=2,
            ativo=True,
        )
        session.add(regra1)
        session.add(regra2)
        session.commit()

        total = aplicar_todas_regras_em_todas_transacoes(session)

        assert total == 2  # Cada transação teve 1 regra aplicada

        session.commit()
        session.refresh(t1)
        session.refresh(t2)

        assert t1.categoria == "Streaming"
        assert t2.categoria == "Transporte"
