"""
Testes unitários para Value Objects de Domínio

Objetivo: Testar validações e comportamento dos value objects
"""
import pytest
from app.domain.value_objects.tipo_transacao import TipoTransacao
from app.domain.value_objects.regra_enums import CriterioTipo, TipoAcao


@pytest.mark.unit
class TestTipoTransacao:
    """Testes para o value object TipoTransacao"""
    
    def test_tipo_entrada_tem_valor_correto(self):
        """Testa que ENTRADA tem o valor 'entrada'"""
        assert TipoTransacao.ENTRADA.value == "entrada"
    
    def test_tipo_saida_tem_valor_correto(self):
        """Testa que SAIDA tem o valor 'saida'"""
        assert TipoTransacao.SAIDA.value == "saida"
    
    def test_enum_possui_apenas_dois_valores(self):
        """Testa que o enum possui apenas ENTRADA e SAIDA"""
        valores = list(TipoTransacao)
        assert len(valores) == 2
        assert TipoTransacao.ENTRADA in valores
        assert TipoTransacao.SAIDA in valores


@pytest.mark.unit
class TestCriterioTipo:
    """Testes para o value object CriterioTipo"""
    
    def test_criterio_descricao_exata_tem_valor_correto(self):
        """Testa que DESCRICAO_EXATA tem o valor correto"""
        assert CriterioTipo.DESCRICAO_EXATA.value == "descricao_exata"
    
    def test_criterio_descricao_contem_tem_valor_correto(self):
        """Testa que DESCRICAO_CONTEM tem o valor correto"""
        assert CriterioTipo.DESCRICAO_CONTEM.value == "descricao_contem"
    
    def test_criterio_categoria_tem_valor_correto(self):
        """Testa que CATEGORIA tem o valor correto"""
        assert CriterioTipo.CATEGORIA.value == "categoria"
    
    def test_enum_possui_tres_valores(self):
        """Testa que o enum possui três valores"""
        valores = list(CriterioTipo)
        assert len(valores) == 3
        assert CriterioTipo.DESCRICAO_EXATA in valores
        assert CriterioTipo.DESCRICAO_CONTEM in valores
        assert CriterioTipo.CATEGORIA in valores


@pytest.mark.unit
class TestTipoAcao:
    """Testes para o value object TipoAcao"""
    
    def test_tipo_acao_alterar_categoria_tem_valor_correto(self):
        """Testa que ALTERAR_CATEGORIA tem o valor 'alterar_categoria'"""
        assert TipoAcao.ALTERAR_CATEGORIA.value == "alterar_categoria"
    
    def test_tipo_acao_adicionar_tags_tem_valor_correto(self):
        """Testa que ADICIONAR_TAGS tem o valor 'adicionar_tags'"""
        assert TipoAcao.ADICIONAR_TAGS.value == "adicionar_tags"
    
    def test_tipo_acao_alterar_valor_tem_valor_correto(self):
        """Testa que ALTERAR_VALOR tem o valor 'alterar_valor'"""
        assert TipoAcao.ALTERAR_VALOR.value == "alterar_valor"
    
    def test_enum_possui_tres_valores(self):
        """Testa que o enum possui três valores"""
        valores = list(TipoAcao)
        assert len(valores) == 3
        assert TipoAcao.ALTERAR_CATEGORIA in valores
        assert TipoAcao.ADICIONAR_TAGS in valores
        assert TipoAcao.ALTERAR_VALOR in valores
