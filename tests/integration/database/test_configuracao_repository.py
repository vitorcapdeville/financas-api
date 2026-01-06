"""
Testes de integração para ConfiguracaoRepository
Valida operações CRUD com banco de dados real
"""
import pytest
from sqlmodel import Session

from app.domain.entities.configuracao import Configuracao
from app.infrastructure.database.repositories.configuracao_repository import ConfiguracaoRepository


@pytest.mark.integration
class TestConfiguracaoRepositoryIntegration:
    """Testes de integração do repositório de configurações"""
    
    def test_criar_e_buscar_por_chave(self, db_session: Session):
        """
        ARRANGE: Configuração válida
        ACT: Criar e buscar por chave
        ASSERT: Configuração é persistida e recuperada corretamente
        """
        # Arrange
        repository = ConfiguracaoRepository(db_session)
        
        # Act
        repository.salvar("teste_config", "valor_teste")
        valor_buscado = repository.obter("teste_config")
        
        # Assert
        assert valor_buscado is not None
        assert valor_buscado == "valor_teste"
    
    def test_buscar_por_chave_inexistente_retorna_none(self, db_session: Session):
        """
        ARRANGE: Repositório sem a configuração
        ACT: Buscar por chave inexistente
        ASSERT: Retorna None
        """
        # Arrange
        repository = ConfiguracaoRepository(db_session)
        
        # Act
        valor_buscado = repository.obter("chave_inexistente_xyz")
        
        # Assert
        assert valor_buscado is None
    
    def test_listar_todas_configuracoes(self, db_session: Session):
        """
        ARRANGE: Múltiplas configurações no banco
        ACT: Listar todas
        ASSERT: Retorna todas as configurações
        """
        # Arrange
        repository = ConfiguracaoRepository(db_session)
        
        repository.salvar("config_a", "valor_a")
        repository.salvar("config_b", "valor_b")
        repository.salvar("config_c", "valor_c")
        
        # Act
        configs = repository.listar_todas()
        
        # Assert
        assert len(configs) >= 3
        assert "config_a" in configs
        assert "config_b" in configs
        assert "config_c" in configs
    
    def test_salvar_atualiza_configuracao_existente(self, db_session: Session):
        """
        ARRANGE: Configuração já existente
        ACT: Salvar novamente com novo valor (upsert)
        ASSERT: Valor é atualizado
        """
        # Arrange
        repository = ConfiguracaoRepository(db_session)
        
        # Criar configuração inicial
        repository.salvar("dia_inicio", "1")
        
        # Act - Salvar novamente com novo valor
        repository.salvar("dia_inicio", "25")
        
        # Buscar novamente
        valor_buscado = repository.obter("dia_inicio")
        
        # Assert
        assert valor_buscado == "25"  # Valor atualizado
    
    def test_deletar_configuracao(self, db_session: Session):
        """
        ARRANGE: Configuração existente
        ACT: Deletar por chave
        ASSERT: Configuração é removida do banco
        """
        # Arrange
        repository = ConfiguracaoRepository(db_session)
        repository.salvar("to_delete", "delete_me")
        
        # Act
        repository.deletar("to_delete")
        config_buscada = repository.obter("to_delete")
        
        # Assert
        assert config_buscada is None
    
    def test_deletar_configuracao_inexistente_nao_lanca_erro(self, db_session: Session):
        """
        ARRANGE: Chave inexistente
        ACT: Tentar deletar
        ASSERT: Não lança exceção
        """
        # Arrange
        repository = ConfiguracaoRepository(db_session)
        
        # Act & Assert - Não deve lançar exceção
        repository.deletar("chave_inexistente_abc")
    
    def test_chave_unica_constraint(self, db_session: Session):
        """
        ARRANGE: Duas configurações com mesma chave
        ACT: Salvar segunda configuração
        ASSERT: Primeira é atualizada (não cria duplicata)
        """
        # Arrange
        repository = ConfiguracaoRepository(db_session)
        
        repository.salvar("unique_key", "valor1")
        
        # Act
        repository.salvar("unique_key", "valor2")
        
        # Buscar todas configurações
        all_configs = repository.listar_todas()
        
        # Assert - Deve existir apenas 1 configuração com essa chave
        assert len(all_configs) == 1
        assert all_configs["unique_key"] == "valor2"  # Valor atualizado
