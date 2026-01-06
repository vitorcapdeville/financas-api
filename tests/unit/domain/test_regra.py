"""
Testes unitários para a entidade Regra

Objetivo: Testar lógica de negócio da entidade Regra (matching e aplicação)
"""
import pytest
from datetime import date
from app.domain.entities.regra import Regra
from app.domain.entities.transacao import Transacao
from app.domain.value_objects.regra_enums import TipoAcao, CriterioTipo
from app.domain.value_objects.tipo_transacao import TipoTransacao


@pytest.mark.unit
class TestRegraCorrespondeCriterio:
    """Testes para o método corresponde_criterio"""
    
    def test_descricao_exata_case_insensitive_retorna_true(self):
        """
        ARRANGE: Regra com critério DESCRICAO_EXATA e transação com descrição exata
        ACT: Verificar correspondência
        ASSERT: Deve retornar True (case-insensitive)
        """
        # Arrange
        regra = Regra(
            nome="Regra teste",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Supermercado Extra",
            acao_valor="Alimentação"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="supermercado extra",  # Case diferente
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        resultado = regra.corresponde_criterio(transacao)
        
        # Assert
        assert resultado is True
    
    def test_descricao_exata_diferente_retorna_false(self):
        """Testa que descrição diferente não corresponde"""
        # Arrange
        regra = Regra(
            nome="Regra teste",
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Supermercado Extra",
            acao_valor="Alimentação"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Supermercado ABC",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        resultado = regra.corresponde_criterio(transacao)
        
        # Assert
        assert resultado is False
    
    def test_descricao_contem_case_insensitive_retorna_true(self):
        """
        ARRANGE: Regra com critério DESCRICAO_CONTEM
        ACT: Verificar se transação contém substring
        ASSERT: Deve retornar True (case-insensitive)
        """
        # Arrange
        regra = Regra(
            nome="Regra Uber",
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="UBER",
            acao_valor="Transporte"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Viagem uber eats",  # Contém "uber" em minúsculo
            valor=25.00,
            tipo=TipoTransacao.SAIDA,
            origem="fatura_cartao"
        )
        
        # Act
        resultado = regra.corresponde_criterio(transacao)
        
        # Assert
        assert resultado is True
    
    def test_descricao_contem_nao_encontrado_retorna_false(self):
        """Testa que substring não encontrada retorna False"""
        # Arrange
        regra = Regra(
            nome="Regra Uber",
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="UBER",
            acao_valor="Transporte"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Taxi comum",
            valor=25.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        resultado = regra.corresponde_criterio(transacao)
        
        # Assert
        assert resultado is False
    
    def test_categoria_igual_case_insensitive_retorna_true(self):
        """
        ARRANGE: Regra com critério CATEGORIA
        ACT: Verificar se transação tem categoria correspondente
        ASSERT: Deve retornar True (case-insensitive)
        """
        # Arrange
        regra = Regra(
            nome="Regra Lazer",
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Entretenimento",
            acao_valor="Cinema"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Ingresso cinema",
            valor=40.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual",
            categoria="entretenimento"  # Case diferente
        )
        
        # Act
        resultado = regra.corresponde_criterio(transacao)
        
        # Assert
        assert resultado is True
    
    def test_categoria_sem_categoria_retorna_false(self):
        """Testa que transação sem categoria não corresponde a critério CATEGORIA"""
        # Arrange
        regra = Regra(
            nome="Regra Lazer",
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Entretenimento",
            acao_valor="Cinema"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra qualquer",
            valor=40.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
            # Sem categoria
        )
        
        # Act
        resultado = regra.corresponde_criterio(transacao)
        
        # Assert
        assert resultado is False
    
    def test_categoria_diferente_retorna_false(self):
        """Testa que categoria diferente não corresponde"""
        # Arrange
        regra = Regra(
            nome="Regra Lazer",
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Entretenimento",
            acao_valor="Cinema"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=40.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual",
            categoria="Alimentação"
        )
        
        # Act
        resultado = regra.corresponde_criterio(transacao)
        
        # Assert
        assert resultado is False


@pytest.mark.unit
class TestRegraAplicarEm:
    """Testes para o método aplicar_em"""
    
    def test_alterar_categoria_aplica_com_sucesso(self):
        """
        ARRANGE: Regra de alterar categoria que corresponde à transação
        ACT: Aplicar regra
        ASSERT: Categoria deve ser alterada, retorna True
        """
        # Arrange
        regra = Regra(
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Viagem UBER",
            valor=25.00,
            tipo=TipoTransacao.SAIDA,
            origem="fatura_cartao"
        )
        
        # Act
        resultado = regra.aplicar_em(transacao)
        
        # Assert
        assert resultado is True
        assert transacao.categoria == "Transporte"
    
    def test_adicionar_tags_aplica_com_sucesso(self):
        """
        ARRANGE: Regra de adicionar tags que corresponde à transação
        ACT: Aplicar regra
        ASSERT: Tags devem ser adicionadas, retorna True
        """
        # Arrange
        regra = Regra(
            nome="Adicionar tag importante",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="urgente",
            acao_valor="[1, 2, 3]",  # IDs das tags em JSON
            tag_ids=[1, 2, 3]
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Pagamento urgente",
            valor=500.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        resultado = regra.aplicar_em(transacao)
        
        # Assert
        assert resultado is True
        assert 1 in transacao.tag_ids
        assert 2 in transacao.tag_ids
        assert 3 in transacao.tag_ids
    
    def test_alterar_valor_percentual_valido_aplica_com_sucesso(self):
        """
        ARRANGE: Regra de alterar valor com percentual válido (0-100)
        ACT: Aplicar regra
        ASSERT: Valor deve ser alterado proporcionalmente, retorna True
        """
        # Arrange
        regra = Regra(
            nome="Ajustar valor conversão",
            tipo_acao=TipoAcao.ALTERAR_VALOR,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Compras Exterior",
            acao_valor="110"  # 110% do valor (conversão cambial)
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra Amazon",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="fatura_cartao",
            categoria="Compras Exterior"
        )
        
        # Act
        resultado = regra.aplicar_em(transacao)
        
        # Assert
        assert resultado is False  # Percentual > 100 não é aplicado
    
    def test_alterar_valor_percentual_dentro_range_aplica(self):
        """Testa que percentual 0-100 é aplicado"""
        # Arrange
        regra = Regra(
            nome="Reduzir valor",
            tipo_acao=TipoAcao.ALTERAR_VALOR,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Teste",
            acao_valor="50"  # 50% do valor
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual",
            categoria="Teste"
        )
        
        # Act
        resultado = regra.aplicar_em(transacao)
        
        # Assert
        assert resultado is True
        assert transacao.valor == 50.00  # 50% de 100
        assert transacao.valor_original == 100.00  # Original preservado
    
    def test_alterar_valor_percentual_invalido_retorna_false(self):
        """Testa que percentual inválido (não numérico) retorna False"""
        # Arrange
        regra = Regra(
            nome="Regra inválida",
            tipo_acao=TipoAcao.ALTERAR_VALOR,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Teste",
            acao_valor="abc"  # Não é número
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual",
            categoria="Teste"
        )
        
        # Act
        resultado = regra.aplicar_em(transacao)
        
        # Assert
        assert resultado is False
        assert transacao.valor == 100.00  # Valor não alterado
    
    def test_regra_nao_corresponde_nao_aplica(self):
        """
        ARRANGE: Regra que não corresponde à transação
        ACT: Aplicar regra
        ASSERT: Nada deve ser alterado, retorna False
        """
        # Arrange
        regra = Regra(
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte"
        )
        
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Taxi comum",
            valor=25.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        resultado = regra.aplicar_em(transacao)
        
        # Assert
        assert resultado is False
        assert transacao.categoria is None  # Categoria não alterada


@pytest.mark.unit
class TestRegraAtivarDesativar:
    """Testes para os métodos ativar e desativar"""
    
    def test_ativar_regra_inativa(self):
        """
        ARRANGE: Regra inativa
        ACT: Ativar regra
        ASSERT: ativo deve ser True, atualizado_em atualizado
        """
        # Arrange
        regra = Regra(
            nome="Regra teste",
            ativo=False
        )
        atualizado_anterior = regra.atualizado_em
        
        # Act
        regra.ativar()
        
        # Assert
        assert regra.ativo is True
        assert regra.atualizado_em > atualizado_anterior
    
    def test_desativar_regra_ativa(self):
        """
        ARRANGE: Regra ativa
        ACT: Desativar regra
        ASSERT: ativo deve ser False, atualizado_em atualizado
        """
        # Arrange
        regra = Regra(
            nome="Regra teste",
            ativo=True
        )
        atualizado_anterior = regra.atualizado_em
        
        # Act
        regra.desativar()
        
        # Assert
        assert regra.ativo is False
        assert regra.atualizado_em > atualizado_anterior


@pytest.mark.unit
class TestRegraPostInit:
    """Testes para __post_init__ (parsing de tag_ids)"""
    
    def test_post_init_parseia_tag_ids_de_acao_valor(self):
        """
        ARRANGE: Regra com tipo_acao ADICIONAR_TAGS e acao_valor JSON
        ACT: Criar regra (dispara __post_init__)
        ASSERT: tag_ids deve ser parseado do JSON
        """
        # Arrange & Act
        regra = Regra(
            nome="Adicionar tags",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="importante",
            acao_valor='[10, 20, 30]'
        )
        
        # Assert
        assert regra.tag_ids == [10, 20, 30]
    
    def test_post_init_json_invalido_usa_lista_vazia(self):
        """Testa que JSON inválido resulta em tag_ids vazio"""
        # Arrange & Act
        regra = Regra(
            nome="Regra com JSON inválido",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor='not a json'
        )
        
        # Assert
        assert regra.tag_ids == []
    
    def test_post_init_tag_ids_ja_fornecidos_nao_sobrescreve(self):
        """Testa que tag_ids fornecidos explicitamente não são sobrescritos"""
        # Arrange & Act
        regra = Regra(
            nome="Regra com tag_ids explícitos",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor='[1, 2, 3]',
            tag_ids=[5, 6, 7]  # Já fornecido
        )
        
        # Assert
        assert regra.tag_ids == [5, 6, 7]  # Mantém os fornecidos
