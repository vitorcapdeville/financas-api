"""
Router refatorado para Tags - Clean Architecture
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.interfaces.api.schemas.request_response import (
    TagCreateRequest,
    TagUpdateRequest,
    TagResponse
)
from app.interfaces.api.dependencies import (
    get_criar_tag_use_case,
    get_listar_tags_use_case,
    get_atualizar_tag_use_case,
    get_deletar_tag_use_case,
    get_tag_repository
)
from app.application.use_cases.criar_tag import CriarTagUseCase
from app.application.use_cases.listar_tags import ListarTagsUseCase
from app.application.use_cases.atualizar_tag import AtualizarTagUseCase
from app.application.use_cases.deletar_tag import DeletarTagUseCase
from app.application.dto.tag_dto import CriarTagDTO, AtualizarTagDTO
from app.application.exceptions.application_exceptions import (
    ValidationException,
    EntityNotFoundException
)
from app.infrastructure.database.repositories.tag_repository import TagRepository


router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=List[TagResponse])
def listar_tags(
    use_case: ListarTagsUseCase = Depends(get_listar_tags_use_case)
):
    """
    Lista todas as tags disponíveis ordenadas por nome.
    
    Returns:
        Lista de tags
    """
    try:
        dtos = use_case.execute()
        return [_dto_to_response(dto) for dto in dtos]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{tag_id}", response_model=TagResponse)
def obter_tag(
    tag_id: int,
    tag_repo: TagRepository = Depends(get_tag_repository)
):
    """
    Obtém uma tag específica por ID.
    
    Args:
        tag_id: ID da tag
        
    Returns:
        Tag encontrada
        
    Raises:
        404: Tag não encontrada
    """
    tag = tag_repo.buscar_por_id(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag não encontrada"
        )
    
    return TagResponse(
        id=tag.id,
        nome=tag.nome,
        cor=tag.cor,
        descricao=tag.descricao,
        criado_em=tag.criado_em,
        atualizado_em=tag.atualizado_em
    )


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def criar_tag(
    request: TagCreateRequest,
    use_case: CriarTagUseCase = Depends(get_criar_tag_use_case)
):
    """
    Cria uma nova tag.
    
    Args:
        request: Dados da tag (nome obrigatório, cor opcional)
        
    Returns:
        Tag criada
        
    Raises:
        400: Nome já existe ou dados inválidos
    """
    try:
        # Converter request para DTO
        dto = CriarTagDTO(
            nome=request.nome,
            cor=request.cor
        )
        
        # Executar caso de uso
        tag_dto = use_case.execute(dto)
        
        # Converter DTO para response
        return _dto_to_response(tag_dto)
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{tag_id}", response_model=TagResponse)
def atualizar_tag(
    tag_id: int,
    request: TagUpdateRequest,
    use_case: AtualizarTagUseCase = Depends(get_atualizar_tag_use_case)
):
    """
    Atualiza uma tag existente.
    
    Args:
        tag_id: ID da tag a atualizar
        request: Dados para atualização (campos opcionais)
        
    Returns:
        Tag atualizada
        
    Raises:
        404: Tag não encontrada
        400: Nome já existe ou dados inválidos
    """
    try:
        # Converter request para DTO
        dto = AtualizarTagDTO(
            nome=request.nome,
            cor=request.cor
        )
        
        # Executar caso de uso
        tag_dto = use_case.execute(tag_id, dto)
        
        # Converter DTO para response
        return _dto_to_response(tag_dto)
        
    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_tag(
    tag_id: int,
    use_case: DeletarTagUseCase = Depends(get_deletar_tag_use_case)
):
    """
    Deleta uma tag.
    Remove também todas as associações com transações (CASCADE).
    
    Args:
        tag_id: ID da tag a deletar
        
    Raises:
        404: Tag não encontrada
    """
    try:
        use_case.execute(tag_id)
        return None
        
    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ===== FUNÇÕES AUXILIARES =====

def _dto_to_response(dto) -> TagResponse:
    """Converte DTO para response Pydantic"""
    return TagResponse(
        id=dto.id,
        nome=dto.nome,
        cor=dto.cor,
        descricao=dto.descricao,
        criado_em=dto.criado_em,
        atualizado_em=dto.atualizado_em
    )
