"""
Caso de uso: Remover Tag de Transação
"""
from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.application.exceptions.application_exceptions import EntityNotFoundException


class RemoverTagTransacaoUseCase:
    """
    Caso de uso para remover uma tag de uma transação.
    
    Responsabilidades:
    - Validar que transação existe
    - Remover associação com tag
    """
    
    def __init__(self, transacao_repository: ITransacaoRepository):
        self._transacao_repository = transacao_repository
    
    def execute(self, transacao_id: int, tag_id: int) -> None:
        """
        Executa o caso de uso de remover tag.
        
        Args:
            transacao_id: ID da transação
            tag_id: ID da tag
            
        Raises:
            EntityNotFoundException: Se transação não existir
        """
        # Validar que transação existe
        transacao = self._transacao_repository.buscar_por_id(transacao_id)
        if not transacao:
            raise EntityNotFoundException("Transacao", transacao_id)
        
        # Remover tag (repositório já trata se não estiver associada)
        self._transacao_repository.remover_tag(transacao_id, tag_id)
