"""Caso de uso: Listar Tags"""

from typing import List

from app.domain.repositories.tag_repository import ITagRepository
from app.domain.entities.tag import Tag
from app.application.dto.tag_dto import TagDTO


class ListarTagsUseCase:
    """
    Caso de uso para listar todas as tags.
    
    Responsabilidades:
    - Buscar tags no repositório
    - Converter para DTOs
    - Retornar lista ordenada
    """
    
    def __init__(self, tag_repository: ITagRepository):
        self._tag_repository = tag_repository
    
    def execute(self) -> List[TagDTO]:
        """
        Executa o caso de uso de listagem de tags.
        
        Returns:
            Lista de TagDTOs ordenada por nome
        """
        # Buscar todas as tags
        tags = self._tag_repository.listar()
        
        # Converter para DTOs
        dtos = [self._to_dto(tag) for tag in tags]
        
        # Ordenar por nome
        dtos.sort(key=lambda t: t.nome)
        
        return dtos
    
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
