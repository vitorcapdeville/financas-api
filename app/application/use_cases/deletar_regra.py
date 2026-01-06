"""Caso de uso: Deletar Regra"""

from app.domain.repositories.regra_repository import IRegraRepository
from app.application.exceptions.application_exceptions import EntityNotFoundException


class DeletarRegraUseCase:
    """
    Caso de uso para deletar uma regra.
    
    Responsabilidades:
    - Validar que regra existe
    - Deletar via repositório
    - Relacionamentos são gerenciados pelo banco (CASCADE)
    """
    
    def __init__(self, regra_repository: IRegraRepository):
        self._regra_repository = regra_repository
    
    def execute(self, regra_id: int) -> None:
        """
        Executa o caso de uso de deleção de regra.
        
        Args:
            regra_id: ID da regra a deletar
            
        Raises:
            EntityNotFoundException: Se regra não existe
        """
        # Validar que regra existe
        regra = self._regra_repository.buscar_por_id(regra_id)
        if not regra:
            raise EntityNotFoundException("Regra", regra_id)
        
        # Deletar
        # Nota: Relacionamentos com tags são deletados em cascata
        self._regra_repository.deletar(regra_id)
