"""Caso de uso: Deletar Tag"""

from app.domain.repositories.tag_repository import ITagRepository
from app.application.exceptions.application_exceptions import EntityNotFoundException


class DeletarTagUseCase:
    """
    Caso de uso para deletar uma tag.
    
    Responsabilidades:
    - Validar que tag existe
    - Deletar via repositório
    - Relacionamentos são gerenciados pelo banco (CASCADE)
    """
    
    def __init__(self, tag_repository: ITagRepository):
        self._tag_repository = tag_repository
    
    def execute(self, tag_id: int) -> None:
        """
        Executa o caso de uso de deleção de tag.
        
        Args:
            tag_id: ID da tag a deletar
            
        Raises:
            EntityNotFoundException: Se tag não existe
        """
        # Validar que tag existe
        tag = self._tag_repository.buscar_por_id(tag_id)
        if not tag:
            raise EntityNotFoundException("Tag", tag_id)
        
        # Deletar
        # Nota: Relacionamentos com transações são deletados em cascata
        self._tag_repository.deletar(tag_id)
