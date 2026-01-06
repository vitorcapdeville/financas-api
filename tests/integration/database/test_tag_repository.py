"""
Testes de integração para TagRepository
Valida operações CRUD com banco de dados real
"""
import pytest
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from app.domain.entities.tag import Tag
from app.infrastructure.database.repositories.tag_repository import TagRepository


@pytest.mark.integration
class TestTagRepositoryIntegration:
    """Testes de integração do repositório de tags"""
    
    def test_criar_e_buscar_por_id(self, db_session: Session):
        """
        ARRANGE: Tag válida
        ACT: Criar e buscar por ID
        ASSERT: Tag é persistida e recuperada corretamente
        """
        # Arrange
        repository = TagRepository(db_session)
        tag = Tag(nome="Categoria Test")
        
        # Act
        tag_criada = repository.criar(tag)
        tag_buscada = repository.buscar_por_id(tag_criada.id)
        
        # Assert
        assert tag_buscada is not None
        assert tag_buscada.id == tag_criada.id
        assert tag_buscada.nome == "Categoria Test"
    
    def test_buscar_por_nome(self, db_session: Session):
        """
        ARRANGE: Tag com nome único
        ACT: Buscar por nome
        ASSERT: Tag é encontrada pelo nome
        """
        # Arrange
        repository = TagRepository(db_session)
        tag = Tag(nome="Alimentação")
        repository.criar(tag)
        
        # Act
        tag_encontrada = repository.buscar_por_nome("Alimentação")
        
        # Assert
        assert tag_encontrada is not None
        assert tag_encontrada.nome == "Alimentação"
    
    def test_buscar_por_nome_case_insensitive(self, db_session: Session):
        """
        ARRANGE: Tag com nome em maiúsculas/minúsculas
        ACT: Buscar com case diferente
        ASSERT: Encontra tag (case-insensitive)
        """
        # Arrange
        repository = TagRepository(db_session)
        tag = Tag(nome="Transporte")
        repository.criar(tag)
        
        # Act
        tag_encontrada = repository.buscar_por_nome("TRANSPORTE")
        
        # Assert
        assert tag_encontrada is not None
        assert tag_encontrada.nome == "Transporte"
    
    def test_buscar_por_nome_inexistente_retorna_none(self, db_session: Session):
        """
        ARRANGE: Repositório sem a tag
        ACT: Buscar por nome inexistente
        ASSERT: Retorna None
        """
        # Arrange
        repository = TagRepository(db_session)
        
        # Act
        tag_encontrada = repository.buscar_por_nome("Tag Inexistente XYZ")
        
        # Assert
        assert tag_encontrada is None
    
    def test_listar_todas_tags(self, db_session: Session):
        """
        ARRANGE: Múltiplas tags no banco
        ACT: Listar todas
        ASSERT: Retorna todas as tags
        """
        # Arrange
        repository = TagRepository(db_session)
        
        tag1 = Tag(nome="Tag A")
        tag2 = Tag(nome="Tag B")
        tag3 = Tag(nome="Tag C")
        
        repository.criar(tag1)
        repository.criar(tag2)
        repository.criar(tag3)
        
        # Act
        tags = repository.listar()
        
        # Assert
        assert len(tags) >= 3
        nomes = [t.nome for t in tags]
        assert "Tag A" in nomes
        assert "Tag B" in nomes
        assert "Tag C" in nomes
    
    def test_listar_por_ids(self, db_session: Session):
        """
        ARRANGE: Múltiplas tags criadas
        ACT: Listar por IDs específicos
        ASSERT: Retorna apenas tags com IDs fornecidos
        """
        # Arrange
        repository = TagRepository(db_session)
        
        tag1 = Tag(nome="Tag X")
        tag2 = Tag(nome="Tag Y")
        tag3 = Tag(nome="Tag Z")
        
        tag1_criada = repository.criar(tag1)
        tag2_criada = repository.criar(tag2)
        tag3_criada = repository.criar(tag3)
        
        # Act
        tags = repository.listar_por_ids([tag1_criada.id, tag3_criada.id])
        
        # Assert
        assert len(tags) == 2
        nomes = [t.nome for t in tags]
        assert "Tag X" in nomes
        assert "Tag Z" in nomes
        assert "Tag Y" not in nomes
    
    def test_listar_por_ids_vazios_retorna_vazio(self, db_session: Session):
        """
        ARRANGE: Tags no banco
        ACT: Listar com lista de IDs vazia
        ASSERT: Retorna lista vazia
        """
        # Arrange
        repository = TagRepository(db_session)
        
        # Act
        tags = repository.listar_por_ids([])
        
        # Assert
        assert tags == []
    
    def test_atualizar_nome_tag(self, db_session: Session):
        """
        ARRANGE: Tag existente
        ACT: Atualizar nome
        ASSERT: Mudança é persistida
        """
        # Arrange
        repository = TagRepository(db_session)
        tag = Tag(nome="Nome Antigo")
        tag_criada = repository.criar(tag)
        
        # Act
        tag_criada.nome = "Nome Novo"
        tag_criada.atualizar()
        repository.atualizar(tag_criada)
        
        # Buscar novamente
        tag_atualizada = repository.buscar_por_id(tag_criada.id)
        
        # Assert
        assert tag_atualizada.nome == "Nome Novo"
        assert tag_atualizada.atualizado_em > tag_atualizada.criado_em
    
    def test_deletar_tag(self, db_session: Session):
        """
        ARRANGE: Tag existente
        ACT: Deletar tag
        ASSERT: Tag é removida do banco
        """
        # Arrange
        repository = TagRepository(db_session)
        tag = Tag(nome="Tag to Delete")
        tag_criada = repository.criar(tag)
        tag_id = tag_criada.id
        
        # Act
        repository.deletar(tag_id)
        tag_buscada = repository.buscar_por_id(tag_id)
        
        # Assert
        assert tag_buscada is None
    
    def test_criar_tag_nome_duplicado_lanca_excecao(self, db_session: Session):
        """
        ARRANGE: Tag com nome já existente
        ACT: Tentar criar tag duplicada
        ASSERT: Lança IntegrityError
        """
        # Arrange
        repository = TagRepository(db_session)
        tag1 = Tag(nome="Duplicada")
        repository.criar(tag1)
        
        # Act & Assert
        tag2 = Tag(nome="Duplicada")
        with pytest.raises(ValueError, match="Tag com nome 'Duplicada' já existe"):
            repository.criar(tag2)
