"""
Caso de uso: Adicionar Tag a Transação
"""
from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.domain.repositories.tag_repository import ITagRepository
from app.application.exceptions.application_exceptions import EntityNotFoundException


class AdicionarTagTransacaoUseCase:
    """
    Caso de uso para adicionar uma tag a uma transação.
    
    Responsabilidades:
    - Validar que transação e tag existem
    - Adicionar associação (evita duplicatas)
    """
    
    def __init__(
        self,
        transacao_repository: ITransacaoRepository,
        tag_repository: ITagRepository
    ):
        self._transacao_repository = transacao_repository
        self._tag_repository = tag_repository
    
    def execute(self, transacao_id: int, tag_id: int) -> None:
        """
        Executa o caso de uso de adicionar tag.
        
        Args:
            transacao_id: ID da transação
            tag_id: ID da tag
            
        Raises:
            EntityNotFoundException: Se transação ou tag não existirem
        """
        # Validar que transação existe
        transacao = self._transacao_repository.buscar_por_id(transacao_id)
        if not transacao:
            raise EntityNotFoundException("Transacao", transacao_id)
        
        # Validar que tag existe
        tag = self._tag_repository.buscar_por_id(tag_id)
        if not tag:
            raise EntityNotFoundException("Tag", tag_id)
        
        # Adicionar tag (repositório já trata duplicatas)
        self._transacao_repository.adicionar_tag(transacao_id, tag_id)
