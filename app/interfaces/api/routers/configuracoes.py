"""
Router refatorado para Configurações usando Clean Architecture
"""
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.obter_configuracao import ObterConfiguracaoUseCase
from app.application.use_cases.salvar_configuracao import SalvarConfiguracaoUseCase
from app.application.use_cases.listar_configuracoes import ListarConfiguracoesUseCase
from app.application.use_cases.deletar_configuracao import DeletarConfiguracaoUseCase
from app.application.dto.configuracao_dto import SalvarConfiguracaoDTO
from app.application.exceptions import EntityNotFoundException
from app.interfaces.api.schemas.request_response import ConfiguracaoRequest, ConfiguracaoResponse
from app.interfaces.api.dependencies import (
    get_obter_configuracao_use_case,
    get_salvar_configuracao_use_case,
    get_listar_configuracoes_use_case,
    get_deletar_configuracao_use_case
)


router = APIRouter(
    prefix="/configuracoes",
    tags=["Configurações"]
)


@router.get("", response_model=Dict[str, str])
def listar_configuracoes(
    use_case: ListarConfiguracoesUseCase = Depends(get_listar_configuracoes_use_case)
):
    """
    Lista todas as configurações.
    
    Returns:
        Dicionário com todas as configurações (chave → valor)
    """
    try:
        return use_case.execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{chave}", response_model=ConfiguracaoResponse)
def obter_configuracao(
    chave: str,
    use_case: ObterConfiguracaoUseCase = Depends(get_obter_configuracao_use_case)
):
    """
    Obtém uma configuração específica por chave.
    
    Args:
        chave: Chave da configuração
        
    Returns:
        Configuração encontrada
        
    Raises:
        404: Configuração não encontrada
    """
    dto = use_case.execute(chave)
    
    if not dto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração '{chave}' não encontrada"
        )
    
    return ConfiguracaoResponse(chave=dto.chave, valor=dto.valor)


@router.post("", response_model=ConfiguracaoResponse, status_code=status.HTTP_201_CREATED)
def salvar_configuracao(
    request: ConfiguracaoRequest,
    use_case: SalvarConfiguracaoUseCase = Depends(get_salvar_configuracao_use_case)
):
    """
    Salva ou atualiza uma configuração.
    
    Args:
        request: Dados da configuração
        
    Returns:
        Configuração salva
        
    Raises:
        400: Dados inválidos
    """
    try:
        dto = SalvarConfiguracaoDTO(chave=request.chave, valor=request.valor)
        resultado = use_case.execute(dto)
        
        return ConfiguracaoResponse(chave=resultado.chave, valor=resultado.valor)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{chave}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_configuracao(
    chave: str,
    use_case: DeletarConfiguracaoUseCase = Depends(get_deletar_configuracao_use_case)
):
    """
    Deleta uma configuração.
    
    Args:
        chave: Chave da configuração a deletar
        
    Raises:
        404: Configuração não encontrada
    """
    try:
        use_case.execute(chave)
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
