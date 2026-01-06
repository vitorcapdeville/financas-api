"""
Use Case: Obter Configuração
"""
from typing import Optional

from app.domain.repositories.configuracao_repository import IConfiguracaoRepository
from app.application.dto.configuracao_dto import ConfiguracaoDTO


class ObterConfiguracaoUseCase:
    """
    Caso de uso para obter uma configuração por chave.
    """
    
    def __init__(self, repository: IConfiguracaoRepository):
        self._repository = repository
    
    def execute(self, chave: str) -> Optional[ConfiguracaoDTO]:
        """
        Obtém configuração por chave.
        
        Args:
            chave: Chave da configuração
            
        Returns:
            ConfiguracaoDTO ou None se não existe
        """
        valor = self._repository.obter(chave)
        
        if valor is None:
            return None
        
        return ConfiguracaoDTO(chave=chave, valor=valor)
