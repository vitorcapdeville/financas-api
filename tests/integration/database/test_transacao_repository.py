"""
Testes de integração para TransacaoRepository
Valida operações CRUD com banco de dados real
"""
import pytest
from datetime import date, datetime
from sqlmodel import Session

from app.domain.entities.transacao import Transacao, TipoTransacao
from app.infrastructure.database.repositories.transacao_repository import TransacaoRepository


@pytest.mark.integration
class TestTransacaoRepositoryIntegration:
    """Testes de integração do repositório de transações"""
    
    def test_criar_e_buscar_por_id(self, db_session: Session):
        """
        ARRANGE: Transação válida
        ACT: Criar e buscar por ID
        ASSERT: Transação é persistida e recuperada corretamente
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        transacao = Transacao(
            data=date(2025, 1, 15),
            descricao="Test transaction",
            valor=100.50,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        transacao_criada = repository.criar(transacao)
        transacao_buscada = repository.buscar_por_id(transacao_criada.id)
        
        # Assert
        assert transacao_buscada is not None
        assert transacao_buscada.id == transacao_criada.id
        assert transacao_buscada.descricao == "Test transaction"
        assert transacao_buscada.valor == 100.50
        assert transacao_buscada.tipo == TipoTransacao.SAIDA
    
    def test_listar_todas_transacoes(self, db_session: Session):
        """
        ARRANGE: Múltiplas transações no banco
        ACT: Listar sem filtros
        ASSERT: Retorna todas as transações
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        
        transacao1 = Transacao(
            data=date(2025, 1, 10),
            descricao="Transacao 1",
            valor=50.00,
            tipo=TipoTransacao.ENTRADA,
            origem="manual"
        )
        
        transacao2 = Transacao(
            data=date(2025, 1, 15),
            descricao="Transacao 2",
            valor=75.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        repository.criar(transacao1)
        repository.criar(transacao2)
        
        # Act
        transacoes = repository.listar()
        
        # Assert
        assert len(transacoes) >= 2
        descricoes = [t.descricao for t in transacoes]
        assert "Transacao 1" in descricoes
        assert "Transacao 2" in descricoes
    
    def test_listar_com_filtro_tipo(self, db_session: Session):
        """
        ARRANGE: Transações de entrada e saída
        ACT: Filtrar por tipo ENTRADA
        ASSERT: Retorna apenas entradas
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        
        entrada = Transacao(
            data=date(2025, 1, 10),
            descricao="Entrada",
            valor=100.00,
            tipo=TipoTransacao.ENTRADA,
            origem="manual"
        )
        
        saida = Transacao(
            data=date(2025, 1, 15),
            descricao="Saida",
            valor=50.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        repository.criar(entrada)
        repository.criar(saida)
        
        # Act
        transacoes = repository.listar(tipo=TipoTransacao.ENTRADA)
        
        # Assert
        assert all(t.tipo == TipoTransacao.ENTRADA for t in transacoes)
        descricoes = [t.descricao for t in transacoes]
        assert "Entrada" in descricoes
        assert "Saida" not in descricoes
    
    def test_listar_com_filtro_categoria(self, db_session: Session):
        """
        ARRANGE: Transações com categorias diferentes
        ACT: Filtrar por categoria específica
        ASSERT: Retorna apenas transações da categoria
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        
        transacao1 = Transacao(
            data=date(2025, 1, 10),
            descricao="Compra mercado",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            categoria="Alimentação",
            origem="manual"
        )
        
        transacao2 = Transacao(
            data=date(2025, 1, 15),
            descricao="Combustível",
            valor=200.00,
            tipo=TipoTransacao.SAIDA,
            categoria="Transporte",
            origem="manual"
        )
        
        repository.criar(transacao1)
        repository.criar(transacao2)
        
        # Act
        transacoes = repository.listar(categoria="Alimentação")
        
        # Assert
        assert all(t.categoria == "Alimentação" for t in transacoes)
        descricoes = [t.descricao for t in transacoes]
        assert "Compra mercado" in descricoes
        assert "Combustível" not in descricoes
    
    def test_listar_com_filtro_periodo_data(self, db_session: Session):
        """
        ARRANGE: Transações em datas diferentes
        ACT: Filtrar por período específico
        ASSERT: Retorna apenas transações no período
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        
        # Transação dentro do período
        transacao_dentro = Transacao(
            data=date(2025, 1, 15),
            descricao="Dentro do período",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Transação fora do período
        transacao_fora = Transacao(
            data=date(2025, 2, 20),
            descricao="Fora do período",
            valor=50.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        repository.criar(transacao_dentro)
        repository.criar(transacao_fora)
        
        # Act
        transacoes = repository.listar(
            data_inicio=date(2025, 1, 1),
            data_fim=date(2025, 1, 31)
        )
        
        # Assert
        descricoes = [t.descricao for t in transacoes]
        assert "Dentro do período" in descricoes
        assert "Fora do período" not in descricoes
    
    def test_atualizar_transacao(self, db_session: Session):
        """
        ARRANGE: Transação existente
        ACT: Atualizar categoria
        ASSERT: Mudança é persistida
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        transacao = Transacao(
            data=date(2025, 1, 15),
            descricao="Test",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        transacao_criada = repository.criar(transacao)
        
        # Act
        transacao_criada.alterar_categoria("Nova Categoria")
        repository.atualizar(transacao_criada)
        
        # Buscar novamente para validar persistência
        transacao_atualizada = repository.buscar_por_id(transacao_criada.id)
        
        # Assert
        assert transacao_atualizada.categoria == "Nova Categoria"
        assert transacao_atualizada.atualizado_em > transacao_atualizada.criado_em
    
    def test_deletar_transacao(self, db_session: Session):
        """
        ARRANGE: Transação existente
        ACT: Deletar transação
        ASSERT: Transação é removida do banco
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        transacao = Transacao(
            data=date(2025, 1, 15),
            descricao="To be deleted",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        transacao_criada = repository.criar(transacao)
        transacao_id = transacao_criada.id
        
        # Act
        repository.deletar(transacao_id)
        transacao_buscada = repository.buscar_por_id(transacao_id)
        
        # Assert
        assert transacao_buscada is None
    
    def test_restaurar_valor_original(self, db_session: Session):
        """
        ARRANGE: Transação com valor modificado
        ACT: Restaurar valor original
        ASSERT: Valor volta ao original
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        transacao = Transacao(
            data=date(2025, 1, 15),
            descricao="Test",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        transacao_criada = repository.criar(transacao)
        
        # Modificar valor
        transacao_criada.alterar_valor(50.00)
        repository.atualizar(transacao_criada)
        
        # Act
        repository.restaurar_valor_original(transacao_criada.id)
        
        # Buscar novamente
        transacao_restaurada = repository.buscar_por_id(transacao_criada.id)
        
        # Assert
        assert transacao_restaurada.valor == 100.00  # Valor original
        assert transacao_restaurada.valor_original == 100.00
    
    def test_adicionar_tag_em_transacao(self, db_session: Session):
        """
        ARRANGE: Transação sem tags
        ACT: Adicionar tag
        ASSERT: Tag é adicionada e persistida
        """
        # Arrange
        repository = TransacaoRepository(db_session)
        transacao = Transacao(
            data=date(2025, 1, 15),
            descricao="Test",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        transacao_criada = repository.criar(transacao)
        
        # Act
        transacao_criada.adicionar_tag(1)
        transacao_criada.adicionar_tag(2)
        repository.atualizar(transacao_criada)
        
        # Buscar novamente
        transacao_atualizada = repository.buscar_por_id(transacao_criada.id)
        
        # Assert
        assert 1 in transacao_atualizada.tag_ids
        assert 2 in transacao_atualizada.tag_ids
        assert len(transacao_atualizada.tag_ids) == 2
