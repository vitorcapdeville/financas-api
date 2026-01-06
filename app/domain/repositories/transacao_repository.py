"""
Interface (Port) de Repositório de Transações
Define o contrato que implementações concretas devem seguir
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.domain.entities.transacao import Transacao
from app.domain.value_objects.tipo_transacao import TipoTransacao


class ITransacaoRepository(ABC):
    """
    Interface abstrata para operações de persistência de Transações.
    
    Princípio DIP: O domínio define a interface, a infraestrutura implementa.
    Princípio ISP: Interface focada apenas em operações de Transação.
    """
    
    @abstractmethod
    def criar(self, transacao: Transacao) -> Transacao:
        """
        Cria uma nova transação no repositório.
        
        Args:
            transacao: Entidade de domínio a ser persistida
            
        Returns:
            Transação criada com ID gerado
        """
        pass
    
    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Transacao]:
        """
        Busca uma transação por ID.
        
        Args:
            id: Identificador da transação
            
        Returns:
            Transação encontrada ou None
        """
        pass
    
    @abstractmethod
    def listar(
        self,
        mes: Optional[int] = None,
        ano: Optional[int] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        categoria: Optional[str] = None,
        tipo: Optional[TipoTransacao] = None,
        tag_ids: Optional[List[int]] = None,
        criterio_data: str = "data_transacao"
    ) -> List[Transacao]:
        """
        Lista transações com filtros opcionais.
        
        Args:
            mes: Mês para filtrar (1-12)
            ano: Ano para filtrar
            data_inicio: Data inicial do período
            data_fim: Data final do período
            categoria: Categoria para filtrar
            tipo: Tipo de transação (entrada/saída)
            tag_ids: Lista de IDs de tags (operação OR)
            criterio_data: "data_transacao" ou "data_fatura"
            
        Returns:
            Lista de transações que atendem aos filtros
        """
        pass
    
    @abstractmethod
    def atualizar(self, transacao: Transacao) -> Transacao:
        """
        Atualiza uma transação existente.
        
        Args:
            transacao: Entidade de domínio com dados atualizados
            
        Returns:
            Transação atualizada
            
        Raises:
            ValueError: Se a transação não existe
        """
        pass
    
    @abstractmethod
    def deletar(self, id: int) -> bool:
        """
        Deleta uma transação.
        
        Args:
            id: Identificador da transação
            
        Returns:
            True se deletou, False se não encontrou
        """
        pass
    
    @abstractmethod
    def listar_por_ids(self, ids: List[int]) -> List[Transacao]:
        """
        Lista transações por múltiplos IDs.
        
        Args:
            ids: Lista de identificadores
            
        Returns:
            Lista de transações encontradas
        """
        pass
    
    @abstractmethod
    def contar(
        self,
        mes: Optional[int] = None,
        ano: Optional[int] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        criterio_data: str = "data_transacao"
    ) -> int:
        """
        Conta transações com filtros opcionais.
        
        Args:
            mes: Mês para filtrar
            ano: Ano para filtrar
            data_inicio: Data inicial do período
            data_fim: Data final do período
            criterio_data: "data_transacao" ou "data_fatura"
            
        Returns:
            Quantidade de transações
        """
        pass
    
    @abstractmethod
    def listar_categorias(self) -> List[str]:
        """
        Lista todas as categorias únicas existentes nas transações.
        
        Returns:
            Lista de categorias únicas (pode conter None)
        """
        pass
    
    @abstractmethod
    def restaurar_valor_original(self, id: int) -> Transacao:
        """
        Restaura o valor original de uma transação.
        
        Args:
            id: ID da transação
            
        Returns:
            Transação com valor restaurado
        """
        pass
    
    @abstractmethod
    def adicionar_tag(self, transacao_id: int, tag_id: int) -> None:
        """
        Adiciona uma tag a uma transação.
        Evita duplicatas automaticamente.
        
        Args:
            transacao_id: ID da transação
            tag_id: ID da tag
        """
        pass
    
    @abstractmethod
    def remover_tag(self, transacao_id: int, tag_id: int) -> None:
        """
        Remove uma tag de uma transação.
        
        Args:
            transacao_id: ID da transação
            tag_id: ID da tag
        """
        pass
