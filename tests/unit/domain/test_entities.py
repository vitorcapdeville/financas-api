"""
Testes unitários para as Entidades de Domínio

Objetivo: Testar a lógica de negócio das entidades sem dependências externas
Padrão: Arrange-Act-Assert
"""
import pytest
from datetime import date
from app.domain.entities.transacao import Transacao
from app.domain.value_objects.tipo_transacao import TipoTransacao


@pytest.mark.unit
class TestTransacao:
    """Testes para a entidade Transacao"""
    
    def test_criar_transacao_valida(self):
        """
        ARRANGE: Preparar dados válidos para uma transação
        ACT: Criar uma transação
        ASSERT: Verificar que foi criada corretamente
        """
        # Arrange
        data = date(2026, 1, 15)
        descricao = "Compra no supermercado"
        valor = 150.50
        tipo = TipoTransacao.SAIDA
        
        # Act
        transacao = Transacao(
            data=data,
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            origem="manual"
        )
        
        # Assert
        assert transacao.data == data
        assert transacao.descricao == descricao
        assert transacao.valor == valor
        assert transacao.tipo == TipoTransacao.SAIDA
        assert transacao.origem == "manual"
        assert transacao.categoria is None
        assert transacao.valor_original == valor  # Inicializado automaticamente
    
    def test_criar_transacao_com_categoria(self):
        """Testa criação de transação com categoria"""
        # Arrange & Act
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Almoço",
            valor=45.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual",
            categoria="Alimentação"
        )
        
        # Assert
        assert transacao.categoria == "Alimentação"
    
    def test_atualizar_categoria(self):
        """Testa atualização de categoria da transação"""
        # Arrange
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        transacao.alterar_categoria("Vestuário")
        
        # Assert
        assert transacao.categoria == "Vestuário"
    
    def test_atualizar_categoria_vazia(self):
        """Testa atualização de categoria para string vazia"""
        # Arrange
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual",
            categoria="Vestuário"
        )
        
        # Act
        transacao.alterar_categoria("")
        
        # Assert
        assert transacao.categoria == ""
    
    def test_atualizar_valor_preserva_original(self):
        """Testa que ao atualizar valor, o original é preservado"""
        # Arrange
        valor_original = 100.00
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=valor_original,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        novo_valor = 120.00
        transacao.alterar_valor(novo_valor)
        
        # Assert
        assert transacao.valor == novo_valor
        assert transacao.valor_original == valor_original
    
    def test_atualizar_valor_multiplas_vezes_preserva_primeiro_original(self):
        """Testa que múltiplas atualizações preservam o primeiro valor original"""
        # Arrange
        valor_inicial = 100.00
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=valor_inicial,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        transacao.alterar_valor(120.00)
        transacao.alterar_valor(150.00)
        
        # Assert
        assert transacao.valor == 150.00
        assert transacao.valor_original == valor_inicial
    
    def test_adicionar_tag(self):
        """Testa adição de tag à transação"""
        # Arrange
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        transacao.adicionar_tag(1)
        transacao.adicionar_tag(2)
        
        # Assert
        assert 1 in transacao.tag_ids
        assert 2 in transacao.tag_ids
        assert len(transacao.tag_ids) == 2
    
    def test_adicionar_tag_duplicada_nao_adiciona(self):
        """Testa que adicionar tag duplicada não cria duplicata"""
        # Arrange
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        transacao.adicionar_tag(1)
        transacao.adicionar_tag(1)  # Duplicada
        
        # Assert
        assert len(transacao.tag_ids) == 1
    
    def test_remover_tag(self):
        """Testa remoção de tag"""
        # Arrange
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        transacao.adicionar_tag(1)
        transacao.adicionar_tag(2)
        
        # Act
        transacao.remover_tag(1)
        
        # Assert
        assert 1 not in transacao.tag_ids
        assert 2 in transacao.tag_ids
    
    def test_eh_entrada_retorna_true_para_tipo_entrada(self):
        """Testa método eh_entrada para transação de entrada"""
        # Arrange & Act
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Salário",
            valor=5000.00,
            tipo=TipoTransacao.ENTRADA,
            origem="manual"
        )
        
        # Assert
        assert transacao.eh_entrada() is True
    
    def test_eh_entrada_retorna_false_para_tipo_saida(self):
        """Testa método eh_entrada para transação de saída"""
        # Arrange & Act
        transacao = Transacao(
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Assert
        assert transacao.eh_entrada() is False
