"""
Interface (Port) de Repositório de Tags
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.tag import Tag


class ITagRepository(ABC):
    """
    Interface abstrata para operações de persistência de Tags.
    
    Princípio DIP: O domínio define a interface, a infraestrutura implementa.
    """
    
    @abstractmethod
    def criar(self, tag: Tag) -> Tag:
        """
        Cria uma nova tag.
        
        Args:
            tag: Entidade de domínio
            
        Returns:
            Tag criada com ID gerado
            
        Raises:
            ValueError: Se já existe tag com mesmo nome (case-insensitive)
        """
        pass
    
    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Tag]:
        """Busca tag por ID"""
        pass
    
    @abstractmethod
    def buscar_por_nome(self, nome: str) -> Optional[Tag]:
        """Busca tag por nome (case-insensitive)"""
        pass
    
    @abstractmethod
    def listar(self) -> List[Tag]:
        """Lista todas as tags"""
        pass
    
    @abstractmethod
    def atualizar(self, tag: Tag) -> Tag:
        """
        Atualiza uma tag existente.
        
        Raises:
            ValueError: Se a tag não existe ou nome já está em uso
        """
        pass
    
    @abstractmethod
    def deletar(self, id: int) -> bool:
        """Deleta uma tag"""
        pass
    
    @abstractmethod
    def nome_existe(self, nome: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica se já existe tag com este nome.
        
        Args:
            nome: Nome a verificar (case-insensitive)
            excluir_id: ID a excluir da verificação (para update)
        """
        pass
    
    @abstractmethod
    def listar_por_ids(self, ids: List[int]) -> List[Tag]:
        """
        Lista tags por múltiplos IDs.
        
        Args:
            ids: Lista de identificadores
            
        Returns:
            Lista de tags encontradas
        """
        pass
