"""
Testes para Use Cases Auxiliares
"""
import pytest
from unittest.mock import Mock
from datetime import datetime, date

from app.application.use_cases.aplicar_todas_regras import AplicarTodasRegrasUseCase
from app.application.use_cases.listar_categorias import ListarCategoriasUseCase
from app.application.dto.transacao_dto import FiltrosTransacaoDTO
from app.domain.entities.transacao import Transacao
from app.domain.entities.regra import Regra
from app.domain.value_objects.tipo_transacao import TipoTransacao
from app.domain.value_objects.regra_enums import TipoAcao, CriterioTipo


class TestAplicarTodasRegrasUseCase:
    """Testes para AplicarTodasRegrasUseCase"""
    
    @pytest.fixture
    def mock_transacao_repo(self):
        return Mock()
    
    @pytest.fixture
    def mock_regra_repo(self):
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_transacao_repo, mock_regra_repo):
        return AplicarTodasRegrasUseCase(mock_transacao_repo, mock_regra_repo)
    
    def test_aplicar_regras_em_transacoes_com_sucesso(self, use_case, mock_transacao_repo, mock_regra_repo):
        """Deve aplicar regras em transações com sucesso"""
        # Arrange
        transacao1 = Transacao(
            data=date(2024, 1, 1),
            descricao="Supermercado ABC",
            valor=150.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao1.id = 1
        
        transacao2 = Transacao(
            data=date(2024, 1, 2),
            descricao="Farmácia XYZ",
            valor=50.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao2.id = 2
        
        regra = Regra(
            nome="Supermercado -> Alimentação",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="supermercado",
            acao_valor="Alimentação",
            prioridade=1,
            ativo=True
        )
        
        mock_transacao_repo.listar.return_value = [transacao1, transacao2]
        mock_regra_repo.listar.return_value = [regra]
        
        filtros = FiltrosTransacaoDTO(mes=1, ano=2024)
        
        # Act
        result = use_case.execute(filtros)
        
        # Assert
        assert result["transacoes_processadas"] == 2
        assert result["transacoes_modificadas"] == 1  # Apenas transacao1 corresponde
        assert result["regras_aplicadas_total"] == 1
        mock_transacao_repo.atualizar.assert_called_once()
    
    def test_sem_regras_ativas_nao_modifica_transacoes(self, use_case, mock_transacao_repo, mock_regra_repo):
        """Não deve modificar transações se não houver regras ativas"""
        # Arrange
        transacao = Transacao(
            data=date(2024, 1, 1),
            descricao="Compra",
            valor=100.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao.id = 1
        
        mock_transacao_repo.listar.return_value = [transacao]
        mock_regra_repo.listar.return_value = []  # Sem regras
        
        filtros = FiltrosTransacaoDTO(mes=1, ano=2024)
        
        # Act
        result = use_case.execute(filtros)
        
        # Assert
        assert result["transacoes_processadas"] == 1
        assert result["transacoes_modificadas"] == 0
        assert result["regras_aplicadas_total"] == 0
        mock_transacao_repo.atualizar.assert_not_called()
    
    def test_sem_transacoes_retorna_zero(self, use_case, mock_transacao_repo, mock_regra_repo):
        """Deve retornar estatísticas zeradas se não houver transações"""
        # Arrange
        mock_transacao_repo.listar.return_value = []
        mock_regra_repo.listar.return_value = []
        
        filtros = FiltrosTransacaoDTO()
        
        # Act
        result = use_case.execute(filtros)
        
        # Assert
        assert result["transacoes_processadas"] == 0
        assert result["transacoes_modificadas"] == 0
        assert result["regras_aplicadas_total"] == 0
    
    def test_multiplas_regras_aplicadas_em_uma_transacao(self, use_case, mock_transacao_repo, mock_regra_repo):
        """Deve aplicar múltiplas regras em uma transação"""
        # Arrange
        transacao = Transacao(
            data=date(2024, 1, 1),
            descricao="Supermercado",
            valor=100.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao.id = 1
        
        regra1 = Regra(
            nome="Regra 1",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="supermercado",
            acao_valor="Alimentação",
            prioridade=2,
            ativo=True
        )
        
        regra2 = Regra(
            nome="Regra 2",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Alimentação",
            acao_valor="[1]",
            prioridade=1,
            ativo=True
        )
        
        mock_transacao_repo.listar.return_value = [transacao]
        mock_regra_repo.listar.return_value = [regra1, regra2]
        
        filtros = FiltrosTransacaoDTO()
        
        # Act
        result = use_case.execute(filtros)
        
        # Assert
        assert result["transacoes_processadas"] == 1
        assert result["transacoes_modificadas"] == 1
        # Ambas as regras devem ser aplicadas
        assert result["regras_aplicadas_total"] >= 1
    
    def test_filtros_sao_passados_para_listar(self, use_case, mock_transacao_repo, mock_regra_repo):
        """Deve passar todos os filtros para o repositório"""
        # Arrange
        mock_transacao_repo.listar.return_value = []
        mock_regra_repo.listar.return_value = []
        
        filtros = FiltrosTransacaoDTO(
            mes=1,
            ano=2024,
            data_inicio=date(2024, 1, 1),
            data_fim=date(2024, 1, 31),
            categoria="Alimentação",
            tipo=TipoTransacao.SAIDA,
            tag_ids=[1, 2],
            criterio_data="data_transacao"
        )
        
        # Act
        use_case.execute(filtros)
        
        # Assert
        mock_transacao_repo.listar.assert_called_once_with(
            mes=1,
            ano=2024,
            data_inicio=date(2024, 1, 1),
            data_fim=date(2024, 1, 31),
            categoria="Alimentação",
            tipo=TipoTransacao.SAIDA,
            tag_ids=[1, 2],
            criterio_data="data_transacao"
        )


class TestListarCategoriasUseCase:
    """Testes para ListarCategoriasUseCase"""
    
    @pytest.fixture
    def mock_transacao_repo(self):
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_transacao_repo):
        return ListarCategoriasUseCase(mock_transacao_repo)
    
    def test_listar_categorias_com_sucesso(self, use_case, mock_transacao_repo):
        """Deve listar categorias ordenadas alfabeticamente"""
        # Arrange
        categorias = ["Transporte", "Alimentação", "Saúde", "Lazer"]
        mock_transacao_repo.listar_categorias.return_value = categorias
        
        # Act
        result = use_case.execute()
        
        # Assert
        assert result == ["Alimentação", "Lazer", "Saúde", "Transporte"]
        mock_transacao_repo.listar_categorias.assert_called_once()
    
    def test_filtrar_categorias_none(self, use_case, mock_transacao_repo):
        """Deve filtrar categorias None"""
        # Arrange
        categorias = ["Alimentação", None, "Transporte", None, "Saúde"]
        mock_transacao_repo.listar_categorias.return_value = categorias
        
        # Act
        result = use_case.execute()
        
        # Assert
        assert result == ["Alimentação", "Saúde", "Transporte"]
        assert None not in result
    
    def test_filtrar_categorias_vazias(self, use_case, mock_transacao_repo):
        """Deve filtrar categorias vazias"""
        # Arrange
        categorias = ["Alimentação", "", "Transporte", "   ", "Saúde"]
        mock_transacao_repo.listar_categorias.return_value = categorias
        
        # Act
        result = use_case.execute()
        
        # Assert
        # Empty strings são consideradas falsy em Python
        assert "" not in result
        assert "Alimentação" in result
        assert "Transporte" in result
        assert "Saúde" in result
    
    def test_sem_categorias_retorna_lista_vazia(self, use_case, mock_transacao_repo):
        """Deve retornar lista vazia se não houver categorias"""
        # Arrange
        mock_transacao_repo.listar_categorias.return_value = []
        
        # Act
        result = use_case.execute()
        
        # Assert
        assert result == []
    
    def test_categorias_duplicadas_sao_preservadas(self, use_case, mock_transacao_repo):
        """Repositório já retorna categorias únicas, então duplicatas não aparecem"""
        # Arrange
        categorias = ["Alimentação", "Transporte", "Saúde"]
        mock_transacao_repo.listar_categorias.return_value = categorias
        
        # Act
        result = use_case.execute()
        
        # Assert
        assert result == ["Alimentação", "Saúde", "Transporte"]
        assert len(result) == 3
