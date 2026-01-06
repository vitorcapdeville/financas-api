"""
Testes unitários para Use Cases de Regras

Objetivo: Testar lógica de aplicação de regras usando mocks
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import date
from app.application.use_cases.criar_regra import CriarRegraUseCase
from app.application.use_cases.listar_regras import ListarRegrasUseCase
from app.application.use_cases.atualizar_regra import AtualizarRegraUseCase
from app.application.use_cases.deletar_regra import DeletarRegraUseCase
from app.application.use_cases.aplicar_regra_em_transacao import AplicarRegraEmTransacaoUseCase
from app.application.use_cases.aplicar_regras import AplicarRegrasEmTransacaoUseCase
from app.application.dto.regra_dto import CriarRegraDTO, AtualizarRegraDTO
from app.domain.entities.regra import Regra
from app.domain.entities.transacao import Transacao
from app.domain.value_objects.regra_enums import TipoAcao, CriterioTipo
from app.domain.value_objects.tipo_transacao import TipoTransacao
from app.application.exceptions.application_exceptions import (
    EntityNotFoundException,
    ValidationException
)


@pytest.mark.unit
class TestCriarRegraUseCase:
    """Testes para CriarRegraUseCase"""
    
    def test_criar_regra_com_sucesso(self):
        """
        ARRANGE: Mock do repositório
        ACT: Criar regra
        ASSERT: Regra criada e persistida
        """
        # Arrange
        mock_repository = Mock()
        mock_repository.buscar_por_nome.return_value = None  # Nome não duplicado
        regra_criada = Regra(
            id=1,
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            prioridade=10,
            ativo=True
        )
        mock_repository.criar.return_value = regra_criada
        
        use_case = CriarRegraUseCase(mock_repository)
        dto = CriarRegraDTO(
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            prioridade=10,
            ativo=True
        )
        
        # Act
        resultado = use_case.execute(dto)
        
        # Assert
        mock_repository.criar.assert_called_once()
        assert resultado.nome == "Categorizar Uber"
        assert resultado.acao_valor == "Transporte"
    
    def test_criar_regra_nome_vazio_lanca_excecao(self):
        """Testa que criar regra com nome vazio lança exceção"""
        # Arrange
        mock_repository = Mock()
        use_case = CriarRegraUseCase(mock_repository)
        dto = CriarRegraDTO(
            nome="",  # Nome vazio
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor="Categoria",
            prioridade=10
        )
        
        # Act & Assert
        with pytest.raises(ValidationException) as exc_info:
            use_case.execute(dto)
        
        assert "nome" in str(exc_info.value).lower()
        mock_repository.criar.assert_not_called()


@pytest.mark.unit
class TestListarRegrasUseCase:
    """Testes para ListarRegrasUseCase"""
    
    def test_listar_regras_retorna_todas_regras(self):
        """
        ARRANGE: Mock do repositório com lista de regras
        ACT: Executar use case
        ASSERT: Verificar que todas as regras foram retornadas
        """
        # Arrange
        mock_repository = Mock()
        regras = [
            Regra(id=1, nome="Regra 1", prioridade=10),
            Regra(id=2, nome="Regra 2", prioridade=5),
            Regra(id=3, nome="Regra 3", prioridade=15)
        ]
        mock_repository.listar.return_value = regras
        
        use_case = ListarRegrasUseCase(mock_repository)
        
        # Act
        resultado = use_case.execute()
        
        # Assert
        mock_repository.listar.assert_called_once()
        assert len(resultado) == 3
        # Deve ordenar por prioridade (decrescente)
        assert resultado[0].prioridade == 15
        assert resultado[1].prioridade == 10
        assert resultado[2].prioridade == 5
    
    def test_listar_regras_vazio_retorna_lista_vazia(self):
        """Testa que repositório vazio retorna lista vazia"""
        # Arrange
        mock_repository = Mock()
        mock_repository.listar.return_value = []
        
        use_case = ListarRegrasUseCase(mock_repository)
        
        # Act
        resultado = use_case.execute()
        
        # Assert
        assert resultado == []


@pytest.mark.unit
class TestAtualizarRegraUseCase:
    """Testes para AtualizarRegraUseCase"""
    
    def test_atualizar_regra_existente_com_sucesso(self):
        """
        ARRANGE: Mock do repositório com regra existente
        ACT: Executar use case com dados de atualização
        ASSERT: Verificar que regra foi atualizada
        """
        # Arrange
        regra_existente = Regra(
            id=1,
            nome="Regra antiga",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor="Antiga"
        )
        
        mock_repository = Mock()
        mock_repository.buscar_por_id.return_value = regra_existente
        mock_repository.buscar_por_nome.return_value = None  # Nome não duplicado
        mock_repository.atualizar.return_value = regra_existente
        
        use_case = AtualizarRegraUseCase(mock_repository)
        dto = AtualizarRegraDTO(nome="Regra atualizada", acao_valor="Nova")
        
        # Act
        resultado = use_case.execute(1, dto)
        
        # Assert
        mock_repository.buscar_por_id.assert_called_once_with(1)
        mock_repository.atualizar.assert_called_once()
        assert resultado.nome == "Regra atualizada"
    
    def test_atualizar_regra_inexistente_lanca_excecao(self):
        """Testa que atualizar regra inexistente lança exceção"""
        # Arrange
        mock_repository = Mock()
        mock_repository.buscar_por_id.return_value = None
        
        use_case = AtualizarRegraUseCase(mock_repository)
        dto = AtualizarRegraDTO(nome="Novo nome")
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException):
            use_case.execute(999, dto)


@pytest.mark.unit
class TestDeletarRegraUseCase:
    """Testes para DeletarRegraUseCase"""
    
    def test_deletar_regra_existente_com_sucesso(self):
        """
        ARRANGE: Mock do repositório com regra existente
        ACT: Executar use case
        ASSERT: Verificar que regra foi deletada
        """
        # Arrange
        regra_existente = Regra(id=1, nome="A Deletar")
        
        mock_repository = Mock()
        mock_repository.buscar_por_id.return_value = regra_existente
        
        use_case = DeletarRegraUseCase(mock_repository)
        
        # Act
        use_case.execute(1)
        
        # Assert
        mock_repository.buscar_por_id.assert_called_once_with(1)
        mock_repository.deletar.assert_called_once_with(1)
    
    def test_deletar_regra_inexistente_lanca_excecao(self):
        """Testa que deletar regra inexistente lança exceção"""
        # Arrange
        mock_repository = Mock()
        mock_repository.buscar_por_id.return_value = None
        
        use_case = DeletarRegraUseCase(mock_repository)
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException):
            use_case.execute(999)
        
        mock_repository.deletar.assert_not_called()


@pytest.mark.unit
class TestAplicarRegraEmTransacaoUseCase:
    """Testes para AplicarRegraEmTransacaoUseCase"""
    
    def test_aplicar_regra_que_corresponde_com_sucesso(self):
        """
        ARRANGE: Regra e transação que correspondem
        ACT: Aplicar regra
        ASSERT: Transação deve ser modificada e persistida
        """
        # Arrange
        regra = Regra(
            id=1,
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            ativo=True
        )
        
        transacao = Transacao(
            id=10,
            data=date(2026, 1, 15),
            descricao="Viagem UBER",
            valor=25.00,
            tipo=TipoTransacao.SAIDA,
            origem="fatura_cartao"
        )
        
        mock_regra_repository = Mock()
        mock_regra_repository.buscar_por_id.return_value = regra
        
        mock_transacao_repository = Mock()
        mock_transacao_repository.buscar_por_id.return_value = transacao
        mock_transacao_repository.atualizar.return_value = transacao
        
        use_case = AplicarRegraEmTransacaoUseCase(
            mock_regra_repository,
            mock_transacao_repository
        )
        
        # Act
        resultado = use_case.execute(regra_id=1, transacao_id=10)
        
        # Assert
        assert resultado.sucesso is True
        assert transacao.categoria == "Transporte"
        mock_transacao_repository.atualizar.assert_called_once()
    
    def test_aplicar_regra_que_nao_corresponde_nao_persiste(self):
        """
        ARRANGE: Regra e transação que NÃO correspondem
        ACT: Aplicar regra
        ASSERT: Transação não deve ser modificada nem persistida
        """
        # Arrange
        regra = Regra(
            id=1,
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            ativo=True
        )
        
        transacao = Transacao(
            id=10,
            data=date(2026, 1, 15),
            descricao="Taxi comum",  # Não contém "uber"
            valor=25.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        mock_regra_repository = Mock()
        mock_regra_repository.buscar_por_id.return_value = regra
        
        mock_transacao_repository = Mock()
        mock_transacao_repository.buscar_por_id.return_value = transacao
        
        use_case = AplicarRegraEmTransacaoUseCase(
            mock_regra_repository,
            mock_transacao_repository
        )
        
        # Act
        resultado = use_case.execute(regra_id=1, transacao_id=10)
        
        # Assert
        assert resultado.sucesso is False
        mock_transacao_repository.atualizar.assert_not_called()
    
    def test_aplicar_regra_inativa_nao_aplica(self):
        """Testa que regra inativa não é aplicada"""
        # Arrange
        regra = Regra(
            id=1,
            nome="Regra desativada",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor="Categoria",
            ativo=False  # Inativa
        )
        
        transacao = Transacao(
            id=10,
            data=date(2026, 1, 15),
            descricao="teste",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        mock_regra_repository = Mock()
        mock_regra_repository.buscar_por_id.return_value = regra
        
        mock_transacao_repository = Mock()
        mock_transacao_repository.buscar_por_id.return_value = transacao
        
        use_case = AplicarRegraEmTransacaoUseCase(
            mock_regra_repository,
            mock_transacao_repository
        )
        
        # Act
        resultado = use_case.execute(regra_id=1, transacao_id=10)
        
        # Assert
        assert resultado.sucesso is False
        mock_transacao_repository.atualizar.assert_not_called()


@pytest.mark.unit
class TestAplicarRegrasEmTransacaoUseCase:
    """Testes para AplicarRegrasEmTransacaoUseCase (aplicar múltiplas regras)"""
    
    def test_aplicar_regras_ordenadas_por_prioridade(self):
        """
        ARRANGE: Múltiplas regras ativas
        ACT: Aplicar todas as regras em uma transação
        ASSERT: Regras devem ser aplicadas em ordem de prioridade (maior primeiro)
        """
        # Arrange
        regra1 = Regra(
            id=1,
            nome="Regra prioridade 5",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="regras",  # Corresponde à descrição "teste de regras"
            acao_valor="Categoria1",
            prioridade=5,
            ativo=True
        )
        
        regra2 = Regra(
            id=2,
            nome="Regra prioridade 10",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",  # Corresponde à descrição "teste de regras"
            acao_valor="[1, 2]",
            tag_ids=[1, 2],
            prioridade=10,
            ativo=True
        )
        
        transacao = Transacao(
            id=10,
            data=date(2026, 1, 15),
            descricao="teste de regras",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        mock_regra_repository = MagicMock()
        mock_regra_repository.listar.return_value = [regra2, regra1]
        
        mock_transacao_repository = MagicMock()
        mock_transacao_repository.buscar_por_id.return_value = transacao
        mock_transacao_repository.atualizar.return_value = transacao
        
        use_case = AplicarRegrasEmTransacaoUseCase(
            mock_transacao_repository,  # primeiro: transacao_repository
            mock_regra_repository       # segundo: regra_repository
        )
        
        # Act
        resultado = use_case.execute(transacao_id=10)
        
        # Assert
        # Ambas regras devem ser aplicadas
        assert transacao.categoria == "Categoria1"
        assert 1 in transacao.tag_ids
        assert 2 in transacao.tag_ids
        assert resultado == 2  # 2 regras aplicadas
        mock_transacao_repository.atualizar.assert_called()
    
    def test_aplicar_regras_sem_regras_ativas_nao_modifica(self):
        """Testa que sem regras ativas, transação não é modificada"""
        # Arrange
        transacao = Transacao(
            id=10,
            data=date(2026, 1, 15),
            descricao="teste",
            valor=100.00,
            tipo=TipoTransacao.SAIDA,
            origem="manual"
        )
        
        mock_regra_repository = MagicMock()
        mock_regra_repository.listar.return_value = []
        
        mock_transacao_repository = MagicMock()
        mock_transacao_repository.buscar_por_id.return_value = transacao
        
        use_case = AplicarRegrasEmTransacaoUseCase(
            mock_transacao_repository,  # primeiro: transacao_repository
            mock_regra_repository       # segundo: regra_repository
        )
        
        # Act
        resultado = use_case.execute(transacao_id=10)
        
        # Assert
        assert resultado == 0  # Nenhuma regra aplicada
        mock_transacao_repository.atualizar.assert_not_called()
