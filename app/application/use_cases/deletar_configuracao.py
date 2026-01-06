"""
Use Case: Deletar Configuração
"""
from app.domain.repositories.configuracao_repository import IConfiguracaoRepository
from app.application.exceptions import EntityNotFoundException


class DeletarConfiguracaoUseCase:
    """
    Caso de uso para deletar uma configuração.
    """
    
    def __init__(self, repository: IConfiguracaoRepository):
        self._repository = repository
    
    def execute(self, chave: str) -> bool:
        """
        Deleta configuração por chave.
        
        Args:
            chave: Chave da configuração
            
        Returns:
            True se deletado, False se não existe
            
        Raises:
            EntityNotFoundException: Se configuração não existe
        """
        sucesso = self._repository.deletar(chave)
        
        if not sucesso:
            raise EntityNotFoundException("Configuracao", chave)
        
        return True
