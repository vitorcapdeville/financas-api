"""Caso de uso: Criar Tag"""

from app.domain.repositories.tag_repository import ITagRepository
from app.domain.entities.tag import Tag
from app.application.dto.tag_dto import CriarTagDTO, TagDTO
from app.application.exceptions.application_exceptions import ValidationException


class CriarTagUseCase:
    """
    Caso de uso para criar uma nova tag.
    
    Responsabilidades:
    - Validar dados de entrada
    - Criar entidade Tag
    - Persistir via repositório
    - Retornar DTO
    """
    
    def __init__(self, tag_repository: ITagRepository):
        self._tag_repository = tag_repository
    
    def execute(self, dto: CriarTagDTO) -> TagDTO:
        """
        Executa o caso de uso de criação de tag.
        
        Args:
            dto: Dados para criar a tag
            
        Returns:
            TagDTO com dados da tag criada
            
        Raises:
            ValidationException: Se dados inválidos
        """
        # Validar unicidade do nome
        tag_existente = self._tag_repository.buscar_por_nome(dto.nome)
        if tag_existente:
            raise ValidationException(f"Já existe uma tag com o nome '{dto.nome}'")
        
        # Criar entidade de domínio
        tag = Tag(
            nome=dto.nome,
            cor=dto.cor
        )
        
        # Persistir
        tag_criada = self._tag_repository.criar(tag)
        
        # Retornar DTO
        return self._to_dto(tag_criada)
    
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
