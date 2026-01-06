"""
Testes para Use Cases de Tags em Transações
"""
import pytest
from unittest.mock import Mock
from datetime import datetime

from app.application.use_cases.adicionar_tag_transacao import AdicionarTagTransacaoUseCase
from app.application.use_cases.remover_tag_transacao import RemoverTagTransacaoUseCase
from app.application.use_cases.listar_tags_transacao import ListarTagsTransacaoUseCase
from app.application.exceptions.application_exceptions import EntityNotFoundException
from app.domain.entities.transacao import Transacao
from app.domain.entities.tag import Tag
from app.domain.value_objects.tipo_transacao import TipoTransacao


class TestAdicionarTagTransacaoUseCase:
    """Testes para AdicionarTagTransacaoUseCase"""
    
    @pytest.fixture
    def mock_transacao_repo(self):
        return Mock()
    
    @pytest.fixture
    def mock_tag_repo(self):
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_transacao_repo, mock_tag_repo):
        return AdicionarTagTransacaoUseCase(mock_transacao_repo, mock_tag_repo)
    
    def test_adicionar_tag_com_sucesso(self, use_case, mock_transacao_repo, mock_tag_repo):
        """Deve adicionar tag à transação com sucesso"""
        # Arrange
        transacao = Transacao(
            data=datetime(2024, 1, 1).date(),
            descricao="Compra",
            valor=100.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao.id = 1
        
        tag = Tag(nome="Importante", cor="#FF0000")
        tag.id = 1
        
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_tag_repo.buscar_por_id.return_value = tag
        
        # Act
        use_case.execute(transacao_id=1, tag_id=1)
        
        # Assert
        mock_transacao_repo.buscar_por_id.assert_called_once_with(1)
        mock_tag_repo.buscar_por_id.assert_called_once_with(1)
        mock_transacao_repo.adicionar_tag.assert_called_once_with(1, 1)
    
    def test_transacao_inexistente_lanca_excecao(self, use_case, mock_transacao_repo, mock_tag_repo):
        """Deve lançar exceção se transação não existir"""
        # Arrange
        mock_transacao_repo.buscar_por_id.return_value = None
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            use_case.execute(transacao_id=999, tag_id=1)
        
        assert "Transacao" in str(exc_info.value)
        assert "999" in str(exc_info.value)
        mock_tag_repo.buscar_por_id.assert_not_called()
        mock_transacao_repo.adicionar_tag.assert_not_called()
    
    def test_tag_inexistente_lanca_excecao(self, use_case, mock_transacao_repo, mock_tag_repo):
        """Deve lançar exceção se tag não existir"""
        # Arrange
        transacao = Transacao(
            data=datetime(2024, 1, 1).date(),
            descricao="Compra",
            valor=100.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao.id = 1
        
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_tag_repo.buscar_por_id.return_value = None
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            use_case.execute(transacao_id=1, tag_id=999)
        
        assert "Tag" in str(exc_info.value)
        assert "999" in str(exc_info.value)
        mock_transacao_repo.adicionar_tag.assert_not_called()


class TestRemoverTagTransacaoUseCase:
    """Testes para RemoverTagTransacaoUseCase"""
    
    @pytest.fixture
    def mock_transacao_repo(self):
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_transacao_repo):
        return RemoverTagTransacaoUseCase(mock_transacao_repo)
    
    def test_remover_tag_com_sucesso(self, use_case, mock_transacao_repo):
        """Deve remover tag da transação com sucesso"""
        # Arrange
        transacao = Transacao(
            data=datetime(2024, 1, 1).date(),
            descricao="Compra",
            valor=100.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao.id = 1
        transacao.tag_ids = [1, 2, 3]
        
        mock_transacao_repo.buscar_por_id.return_value = transacao
        
        # Act
        use_case.execute(transacao_id=1, tag_id=2)
        
        # Assert
        mock_transacao_repo.buscar_por_id.assert_called_once_with(1)
        mock_transacao_repo.remover_tag.assert_called_once_with(1, 2)
    
    def test_transacao_inexistente_lanca_excecao(self, use_case, mock_transacao_repo):
        """Deve lançar exceção se transação não existir"""
        # Arrange
        mock_transacao_repo.buscar_por_id.return_value = None
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            use_case.execute(transacao_id=999, tag_id=1)
        
        assert "Transacao" in str(exc_info.value)
        assert "999" in str(exc_info.value)
        mock_transacao_repo.remover_tag.assert_not_called()


class TestListarTagsTransacaoUseCase:
    """Testes para ListarTagsTransacaoUseCase"""
    
    @pytest.fixture
    def mock_transacao_repo(self):
        return Mock()
    
    @pytest.fixture
    def mock_tag_repo(self):
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_transacao_repo, mock_tag_repo):
        return ListarTagsTransacaoUseCase(mock_transacao_repo, mock_tag_repo)
    
    def test_listar_tags_com_sucesso(self, use_case, mock_transacao_repo, mock_tag_repo):
        """Deve listar tags da transação com sucesso"""
        # Arrange
        transacao = Transacao(
            data=datetime(2024, 1, 1).date(),
            descricao="Compra",
            valor=100.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao.id = 1
        transacao.tag_ids = [1, 2]
        
        tag1 = Tag(nome="Importante", cor="#FF0000")
        tag1.id = 1
        tag2 = Tag(nome="Urgente", cor="#00FF00")
        tag2.id = 2
        
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_tag_repo.listar_por_ids.return_value = [tag1, tag2]
        
        # Act
        result = use_case.execute(transacao_id=1)
        
        # Assert
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].nome == "Importante"
        assert result[1].id == 2
        assert result[1].nome == "Urgente"
        mock_transacao_repo.buscar_por_id.assert_called_once_with(1)
        mock_tag_repo.listar_por_ids.assert_called_once_with([1, 2])
    
    def test_transacao_sem_tags_retorna_lista_vazia(self, use_case, mock_transacao_repo, mock_tag_repo):
        """Deve retornar lista vazia se transação não tem tags"""
        # Arrange
        transacao = Transacao(
            data=datetime(2024, 1, 1).date(),
            descricao="Compra",
            valor=100.0,
            tipo=TipoTransacao.SAIDA
        )
        transacao.id = 1
        transacao.tag_ids = []
        
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_tag_repo.listar_por_ids.return_value = []
        
        # Act
        result = use_case.execute(transacao_id=1)
        
        # Assert
        assert len(result) == 0
        mock_tag_repo.listar_por_ids.assert_called_once_with([])
    
    def test_transacao_inexistente_lanca_excecao(self, use_case, mock_transacao_repo, mock_tag_repo):
        """Deve lançar exceção se transação não existir"""
        # Arrange
        mock_transacao_repo.buscar_por_id.return_value = None
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            use_case.execute(transacao_id=999)
        
        assert "Transacao" in str(exc_info.value)
        assert "999" in str(exc_info.value)
        mock_tag_repo.listar_por_ids.assert_not_called()
