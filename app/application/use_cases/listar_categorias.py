"""
Caso de uso: Listar Categorias Únicas
"""
from typing import List

from app.domain.repositories.transacao_repository import ITransacaoRepository


class ListarCategoriasUseCase:
    """
    Caso de uso para listar todas as categorias únicas das transações.
    
    Responsabilidades:
    - Buscar categorias distintas
    - Filtrar None/vazias
    - Retornar lista ordenada
    """
    
    def __init__(self, transacao_repository: ITransacaoRepository):
        self._transacao_repository = transacao_repository
    
    def execute(self) -> List[str]:
        """
        Executa o caso de uso de listagem de categorias.
        
        Returns:
            Lista de categorias únicas ordenadas alfabeticamente
        """
        categorias = self._transacao_repository.listar_categorias()
        
        # Filtrar None e vazias
        categorias_validas = [c for c in categorias if c]
        
        # Ordenar alfabeticamente
        return sorted(categorias_validas)
