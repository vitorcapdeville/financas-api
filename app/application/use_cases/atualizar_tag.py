"""Caso de uso: Atualizar Tag"""

from app.domain.repositories.tag_repository import ITagRepository
from app.domain.entities.tag import Tag
from app.application.dto.tag_dto import AtualizarTagDTO, TagDTO
from app.application.exceptions.application_exceptions import (
    EntityNotFoundException,
    ValidationException
)


class AtualizarTagUseCase:
    """
    Caso de uso para atualizar uma tag existente.
    
    Responsabilidades:
    - Validar que tag existe
    - Validar unicidade do novo nome (se alterado)
    - Atualizar entidade
    - Persistir via repositório
    """
    
    def __init__(self, tag_repository: ITagRepository):
        self._tag_repository = tag_repository
    
    def execute(self, tag_id: int, dto: AtualizarTagDTO) -> TagDTO:
        """
        Executa o caso de uso de atualização de tag.
        
        Args:
            tag_id: ID da tag a atualizar
            dto: Dados para atualização
            
        Returns:
            TagDTO com dados atualizados
            
        Raises:
            EntityNotFoundException: Se tag não existe
            ValidationException: Se novo nome já está em uso
        """
        # Buscar tag existente
        tag = self._tag_repository.buscar_por_id(tag_id)
        if not tag:
            raise EntityNotFoundException("Tag", tag_id)
        
        # Validar unicidade do novo nome (se foi alterado)
        if dto.nome and dto.nome != tag.nome:
            tag_com_nome = self._tag_repository.buscar_por_nome(dto.nome)
            if tag_com_nome:
                raise ValidationException(f"Já existe uma tag com o nome '{dto.nome}'")
        
        # Atualizar campos fornecidos
        if dto.nome is not None:
            tag.atualizar_nome(dto.nome)
        
        if dto.cor is not None:
            tag.atualizar_cor(dto.cor)
        
        # Persistir
        tag_atualizada = self._tag_repository.atualizar(tag)
        
        # Retornar DTO
        return self._to_dto(tag_atualizada)
    
    def _to_dto(self, tag: Tag) -> TagDTO:
        """Converte entidade para DTO"""
        return TagDTO(
            id=tag.id,
            nome=tag.nome,
            cor=tag.cor,
            descricao=tag.descricao,
            criado_em=tag.criado_em,
            atualizado_em=tag.atualizado_em
        )
