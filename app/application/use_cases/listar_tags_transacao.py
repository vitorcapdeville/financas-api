"""
Caso de uso: Listar Tags de uma Transação
"""
from typing import List

from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.domain.repositories.tag_repository import ITagRepository
from app.application.dto.tag_dto import TagDTO
from app.application.exceptions.application_exceptions import EntityNotFoundException


class ListarTagsTransacaoUseCase:
    """
    Caso de uso para listar todas as tags de uma transação.
    
    Responsabilidades:
    - Validar que transação existe
    - Buscar tags associadas
    """
    
    def __init__(
        self,
        transacao_repository: ITransacaoRepository,
        tag_repository: ITagRepository
    ):
        self._transacao_repository = transacao_repository
        self._tag_repository = tag_repository
    
    def execute(self, transacao_id: int) -> List[TagDTO]:
        """
        Executa o caso de uso de listar tags da transação.
        
        Args:
            transacao_id: ID da transação
            
        Returns:
            Lista de TagDTOs associados à transação
            
        Raises:
            EntityNotFoundException: Se transação não existir
        """
        # Validar que transação existe
        transacao = self._transacao_repository.buscar_por_id(transacao_id)
        if not transacao:
            raise EntityNotFoundException("Transacao", transacao_id)
        
        # Buscar tags pelos IDs
        tags = self._tag_repository.listar_por_ids(transacao.tag_ids)
        
        # Converter para DTOs
        return [self._to_dto(tag) for tag in tags]
    
    def _to_dto(self, tag) -> TagDTO:
        """Converte entidade para DTO"""
        return TagDTO(
            id=tag.id,
            nome=tag.nome,
            cor=tag.cor,
            descricao=tag.descricao,
            criado_em=tag.criado_em,
            atualizado_em=tag.atualizado_em
        )
