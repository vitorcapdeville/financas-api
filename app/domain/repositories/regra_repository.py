"""
Interface (Port) de Repositório de Regras
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.regra import Regra


class IRegraRepository(ABC):
    """
    Interface abstrata para operações de persistência de Regras.
    
    Princípio DIP: O domínio define a interface, a infraestrutura implementa.
    """
    
    @abstractmethod
    def criar(self, regra: Regra) -> Regra:
        """
        Cria uma nova regra.
        
        Args:
            regra: Entidade de domínio
            
        Returns:
            Regra criada com ID e prioridade gerados
        """
        pass
    
    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Regra]:
        """Busca regra por ID"""
        pass
    
    @abstractmethod
    def listar(self, apenas_ativas: bool = False) -> List[Regra]:
        """
        Lista regras ordenadas por prioridade (maior primeiro).
        
        Args:
            apenas_ativas: Se True, retorna apenas regras ativas
        """
        pass
    
    @abstractmethod
    def atualizar(self, regra: Regra) -> Regra:
        """
        Atualiza uma regra existente.
        
        Raises:
            ValueError: Se a regra não existe
        """
        pass
    
    @abstractmethod
    def deletar(self, id: int) -> bool:
        """Deleta uma regra"""
        pass
    
    @abstractmethod
    def obter_proxima_prioridade(self) -> int:
        """Calcula a próxima prioridade (max atual + 1)"""
        pass
    
    @abstractmethod
    def reordenar(self, nova_ordem: List[int]) -> bool:
        """
        Reordena regras baseado em lista de IDs.
        
        Args:
            nova_ordem: Lista de IDs na ordem desejada (índice 0 = maior prioridade)
        """
        pass
