"""
Testes unitários para Use Cases de Transação

Objetivo: Testar lógica de aplicação usando mocks dos repositórios
Padrão: Arrange-Act-Assert com mocks
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import date
from app.application.use_cases.criar_transacao import CriarTransacaoUseCase
from app.application.use_cases.listar_transacoes import ListarTransacoesUseCase
from app.application.use_cases.atualizar_transacao import AtualizarTransacaoUseCase
from app.application.use_cases.restaurar_valor_original import RestaurarValorOriginalUseCase
from app.application.dto.transacao_dto import CriarTransacaoDTO, AtualizarTransacaoDTO
from app.domain.entities.transacao import Transacao
from app.domain.value_objects.tipo_transacao import TipoTransacao
from app.application.exceptions.application_exceptions import EntityNotFoundException


@pytest.mark.unit
class TestCriarTransacaoUseCase:
    """Testes para CriarTransacaoUseCase"""
    
    def test_criar_transacao_com_sucesso(self):
        """
        ARRANGE: Mock do repositório e DTO válido
        ACT: Executar use case
        ASSERT: Verificar que transação foi criada e salva no repositório
        """
        # Arrange
        mock_repository = Mock()
        transacao_criada = Transacao(
            id=1,
            data=date(2026, 1, 15),
            descricao="Compra teste",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        mock_repository.criar.return_value = transacao_criada
        
        use_case = CriarTransacaoUseCase(mock_repository)
        dto = CriarTransacaoDTO(
            data=date(2026, 1, 15),
            descricao="Compra teste",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        # Act
        resultado = use_case.execute(dto)
        
        # Assert
        mock_repository.criar.assert_called_once()
        assert resultado.id == 1
        assert resultado.descricao == "Compra teste"
        assert resultado.valor == 100.00
    
    def test_criar_transacao_com_categoria(self):
        """Testa criação de transação incluindo categoria"""
        # Arrange
        mock_repository = Mock()
        transacao_criada = Transacao(
            id=1,
            data=date(2026, 1, 15),
            descricao="Almoço",
            valor=45.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual",
            categoria="Alimentação"
        )
        mock_repository.criar.return_value = transacao_criada
        
        use_case = CriarTransacaoUseCase(mock_repository)
        dto = CriarTransacaoDTO(
            data=date(2026, 1, 15),
            descricao="Almoço",
            valor=45.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual",
            categoria="Alimentação"
        )
        
        # Act
        resultado = use_case.execute(dto)
        
        # Assert
        assert resultado.categoria == "Alimentação"


@pytest.mark.unit
class TestListarTransacoesUseCase:
    """Testes para ListarTransacoesUseCase"""
    
    def test_listar_sem_filtros_retorna_todas_transacoes(self):
        """
        ARRANGE: Mock do repositório com lista de transações
        ACT: Executar use case sem filtros
        ASSERT: Verificar que todas as transações foram retornadas
        """
        # Arrange
        mock_transacao_repository = Mock()
        mock_configuracao_repository = Mock()
        transacoes = [
            Transacao(
                id=1,
                data=date(2026, 1, 15),
                descricao="Transação 1",
                valor=100.00,
                tipo=TipoTransacao.SAIDA,
                origem="manual"
            ),
            Transacao(
                id=2,
                data=date(2026, 1, 16),
                descricao="Transação 2",
                valor=200.00,
                tipo=TipoTransacao.ENTRADA,
                origem="manual"
            )
        ]
        mock_transacao_repository.listar.return_value = transacoes
        
        use_case = ListarTransacoesUseCase(
            mock_transacao_repository,
            mock_configuracao_repository
        )
        filtros = MagicMock()
        
        # Act
        resultado = use_case.execute(filtros)
        
        # Assert
        mock_transacao_repository.listar.assert_called_once()
        assert len(resultado) == 2
        assert resultado[0].id == 1
        assert resultado[1].id == 2
    
    def test_listar_com_filtros_passa_filtros_para_repositorio(self):
        """Testa que filtros são passados corretamente para o repositório"""
        # Arrange
        mock_transacao_repository = Mock()
        mock_configuracao_repository = Mock()
        mock_transacao_repository.listar.return_value = []
        
        use_case = ListarTransacoesUseCase(
            mock_transacao_repository,
            mock_configuracao_repository
        )
        
        filtros = MagicMock()
        filtros.categoria = "Alimentação"
        filtros.tipo = TipoTransacao.SAIDA
        
        # Act
        use_case.execute(filtros)
        
        # Assert
        mock_transacao_repository.listar.assert_called_once()


@pytest.mark.unit
class TestAtualizarTransacaoUseCase:
    """Testes para AtualizarTransacaoUseCase"""
    
    def test_atualizar_transacao_existente_com_sucesso(self):
        """
        ARRANGE: Mock do repositório com transação existente
        ACT: Executar use case com dados de atualização
        ASSERT: Verificar que transação foi atualizada
        """
        # Arrange
        transacao_existente = Transacao(
            id=1,
            data=date(2026, 1, 15),
            descricao="Compra antiga",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        mock_repository = Mock()
        mock_repository.buscar_por_id.return_value = transacao_existente
        mock_repository.atualizar.return_value = transacao_existente
        
        use_case = AtualizarTransacaoUseCase(mock_repository)
        dto = AtualizarTransacaoDTO(categoria="Alimentação")
        
        # Act
        resultado = use_case.execute(1, dto)
        
        # Assert
        mock_repository.buscar_por_id.assert_called_once_with(1)
        mock_repository.atualizar.assert_called_once()
        assert resultado.categoria == "Alimentação"
    
    def test_atualizar_transacao_inexistente_lanca_excecao(self):
        """Testa que atualizar transação inexistente lança NotFoundException"""
        # Arrange
        mock_repository = Mock()
        mock_repository.buscar_por_id.return_value = None
        
        use_case = AtualizarTransacaoUseCase(mock_repository)
        dto = AtualizarTransacaoDTO(categoria="Alimentação")
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            use_case.execute(999, dto)
        
        assert "999" in str(exc_info.value)


@pytest.mark.unit
class TestRestaurarValorOriginalUseCase:
    """Testes para RestaurarValorOriginalUseCase"""
    
    def test_restaurar_valor_original_com_sucesso(self):
        """
        ARRANGE: Transação com valor modificado
        ACT: Restaurar valor original
        ASSERT: Verificar que valor foi restaurado
        """
        # Arrange
        transacao = Transacao(
            id=1,
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        transacao.alterar_valor(150.00)  # Modifica valor (original=100, atual=150)
        
        # Transação após restauração (valor volta ao original)
        transacao_restaurada = Transacao(
            id=1,
            data=date(2026, 1, 15),
            descricao="Compra",
            valor=100.00,  # Valor restaurado
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        mock_repository = Mock()
        mock_repository.buscar_por_id.return_value = transacao
        mock_repository.restaurar_valor_original.return_value = transacao_restaurada
        
        use_case = RestaurarValorOriginalUseCase(mock_repository)
        
        # Act
        resultado = use_case.execute(1)
        
        # Assert
        mock_repository.buscar_por_id.assert_called_once_with(1)
        mock_repository.restaurar_valor_original.assert_called_once_with(1)
        assert resultado.valor == 100.00
        # valor_original continua salvo para histórico
        assert resultado.valor_original == 100.00
    
    def test_restaurar_valor_transacao_inexistente_lanca_excecao(self):
        """Testa que restaurar valor de transação inexistente lança exceção"""
        # Arrange
        mock_repository = Mock()
        mock_repository.buscar_por_id.return_value = None
        
        use_case = RestaurarValorOriginalUseCase(mock_repository)
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException):
            use_case.execute(999)
