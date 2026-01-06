"""
Use Case: Listar Todas as Configurações
"""
from typing import Dict

from app.domain.repositories.configuracao_repository import IConfiguracaoRepository


class ListarConfiguracoesUseCase:
    """
    Caso de uso para listar todas as configurações.
    """
    
    def __init__(self, repository: IConfiguracaoRepository):
        self._repository = repository
    
    def execute(self) -> Dict[str, str]:
        """
        Lista todas as configurações.
        
        Returns:
            Dicionário chave → valor
        """
        return self._repository.listar_todas()
