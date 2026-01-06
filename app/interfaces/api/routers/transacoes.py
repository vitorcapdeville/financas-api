"""
Router de Transações - Refatorado com Clean Architecture
Camada de Apresentação (Interfaces)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from datetime import date

from app.interfaces.api.schemas.request_response import (
    TransacaoCreateRequest,
    TransacaoUpdateRequest,
    TransacaoResponse,
    ResumoMensalResponse,
    TagResponse
)
from app.interfaces.api.dependencies import (
    get_criar_transacao_use_case,
    get_listar_transacoes_use_case,
    get_atualizar_transacao_use_case,
    get_obter_resumo_mensal_use_case,
    get_listar_categorias_use_case,
    get_restaurar_valor_original_use_case,
    get_adicionar_tag_transacao_use_case,
    get_remover_tag_transacao_use_case,
    get_listar_tags_transacao_use_case,
    get_transacao_repository
)
from app.application.use_cases.criar_transacao import CriarTransacaoUseCase
from app.application.use_cases.listar_transacoes import ListarTransacoesUseCase
from app.application.use_cases.atualizar_transacao import AtualizarTransacaoUseCase
from app.application.use_cases.obter_resumo_mensal import ObterResumoMensalUseCase
from app.application.use_cases.listar_categorias import ListarCategoriasUseCase
from app.application.use_cases.restaurar_valor_original import RestaurarValorOriginalUseCase
from app.application.use_cases.adicionar_tag_transacao import AdicionarTagTransacaoUseCase
from app.application.use_cases.remover_tag_transacao import RemoverTagTransacaoUseCase
from app.application.use_cases.listar_tags_transacao import ListarTagsTransacaoUseCase
from app.application.dto.transacao_dto import (
    CriarTransacaoDTO,
    AtualizarTransacaoDTO,
    FiltrosTransacaoDTO,
    TransacaoDTO
)
from app.application.exceptions.application_exceptions import (
    ValidationException,
    EntityNotFoundException
)
from app.domain.value_objects.tipo_transacao import TipoTransacao
from app.infrastructure.database.repositories.transacao_repository import TransacaoRepository


router = APIRouter(prefix="/transacoes", tags=["Transações"])


@router.post("/", response_model=TransacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_transacao(
    request: TransacaoCreateRequest,
    use_case: CriarTransacaoUseCase = Depends(get_criar_transacao_use_case)
):
    """
    Cria uma nova transação.
    
    Exemplo de endpoint refatorado com Clean Architecture:
    - Recebe request Pydantic (camada de apresentação)
    - Converte para DTO da aplicação
    - Executa caso de uso (lógica de negócio isolada)
    - Retorna response Pydantic
    """
    try:
        # Converte request → DTO
        dto = CriarTransacaoDTO(
            data=request.data,
            descricao=request.descricao,
            valor=request.valor,
            tipo=TipoTransacao(request.tipo),
            categoria=request.categoria,
            origem=request.origem,
            observacoes=request.observacoes,
            data_fatura=request.data_fatura
        )
        
        # Executa caso de uso
        resultado = use_case.execute(dto)
        
        # Converte DTO → Response
        return _dto_to_response(resultado)
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=List[TransacaoResponse])
def listar_transacoes(
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2000),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    categoria: Optional[str] = None,
    tipo: Optional[str] = None,
    tags: Optional[str] = Query(None, description="IDs separados por vírgula"),
    use_case: ListarTransacoesUseCase = Depends(get_listar_transacoes_use_case)
):
    """
    Lista transações com filtros opcionais.
    
    Exemplo de listagem com Clean Architecture.
    """
    try:
        # Parse de tags
        tag_ids = None
        if tags:
            tag_ids = [int(t) for t in tags.split(",")]
        
        # Parse de tipo
        tipo_enum = None
        if tipo:
            tipo_enum = TipoTransacao(tipo)
        
        # Cria DTO de filtros
        filtros = FiltrosTransacaoDTO(
            mes=mes,
            ano=ano,
            data_inicio=data_inicio,
            data_fim=data_fim,
            categoria=categoria,
            tipo=tipo_enum,
            tag_ids=tag_ids
        )
        
        # Executa caso de uso
        resultados = use_case.execute(filtros)
        
        # Converte DTOs → Responses
        return [_dto_to_response(dto) for dto in resultados]
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/categorias", response_model=List[str])
def listar_categorias(
    use_case: ListarCategoriasUseCase = Depends(get_listar_categorias_use_case)
):
    """
    Lista todas as categorias únicas existentes nas transações.
    
    Returns:
        Lista de strings com categorias ordenadas alfabeticamente
    """
    try:
        return use_case.execute()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/resumo/mensal", response_model=ResumoMensalResponse)
def obter_resumo_mensal(
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2000),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    tags: Optional[str] = Query(None, description="IDs separados por vírgula"),
    use_case: ObterResumoMensalUseCase = Depends(get_obter_resumo_mensal_use_case)
):
    """
    Retorna resumo mensal de entradas/saídas agrupadas por categoria.
    
    Usado pelo dashboard principal.
    O filtro de data respeita a configuração 'criterio_data_transacao'.
    """
    try:
        # Parse de tags
        tag_ids = None
        if tags:
            tag_ids = [int(t) for t in tags.split(",")]
        
        # Executar caso de uso
        resultado = use_case.execute(
            mes=mes,
            ano=ano,
            data_inicio=data_inicio,
            data_fim=data_fim,
            tag_ids=tag_ids
        )
        
        # Converter DTO → Response
        return ResumoMensalResponse(
            mes=resultado.mes,
            ano=resultado.ano,
            total_entradas=resultado.total_entradas,
            total_saidas=resultado.total_saidas,
            saldo=resultado.saldo,
            entradas_por_categoria=resultado.entradas_por_categoria,
            saidas_por_categoria=resultado.saidas_por_categoria
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{transacao_id}", response_model=TransacaoResponse)
def buscar_transacao(
    transacao_id: int,
    repository: TransacaoRepository = Depends(get_transacao_repository)
):
    """
    Busca uma transação por ID.
    
    Nota: Para operações CRUD simples, podemos usar o repositório diretamente.
    Para lógica de negócio complexa, crie um caso de uso.
    """
    transacao = repository.buscar_por_id(transacao_id)
    if not transacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transacao {transacao_id} não encontrada"
        )
    
    # Converte entidade → Response
    return TransacaoResponse(
        id=transacao.id,
        data=transacao.data,
        descricao=transacao.descricao,
        valor=transacao.valor,
        valor_original=transacao.valor_original,
        tipo=transacao.tipo.value,
        categoria=transacao.categoria,
        origem=transacao.origem,
        observacoes=transacao.observacoes,
        data_fatura=transacao.data_fatura,
        criado_em=transacao.criado_em,
        atualizado_em=transacao.atualizado_em,
        tag_ids=transacao.tag_ids
    )


@router.patch("/{transacao_id}", response_model=TransacaoResponse)
def atualizar_transacao(
    transacao_id: int,
    request: TransacaoUpdateRequest,
    use_case: AtualizarTransacaoUseCase = Depends(get_atualizar_transacao_use_case)
):
    """
    Atualiza uma transação existente.
    
    Apenas os campos fornecidos serão atualizados (PATCH parcial).
    """
    try:
        # Converte request → DTO
        dto = AtualizarTransacaoDTO(
            descricao=request.descricao,
            valor=request.valor,
            categoria=request.categoria,
            observacoes=request.observacoes,
            data_fatura=request.data_fatura
        )
        
        # Executa caso de uso
        resultado = use_case.execute(transacao_id, dto)
        
        # Converte DTO → Response
        return _dto_to_response(resultado)
        
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{transacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_transacao(
    transacao_id: int,
    repository: TransacaoRepository = Depends(get_transacao_repository)
):
    """Deleta uma transação"""
    sucesso = repository.deletar(transacao_id)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transacao {transacao_id} não encontrada"
        )


@router.post("/{transacao_id}/restaurar-valor", response_model=TransacaoResponse)
def restaurar_valor_original(
    transacao_id: int,
    use_case: RestaurarValorOriginalUseCase = Depends(get_restaurar_valor_original_use_case)
):
    """
    Restaura o valor original de uma transação.
    
    Útil quando o valor foi modificado por regras e quer desfazer.
    """
    try:
        resultado = use_case.execute(transacao_id)
        return _dto_to_response(resultado)
        
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{transacao_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def adicionar_tag_transacao(
    transacao_id: int,
    tag_id: int,
    use_case: AdicionarTagTransacaoUseCase = Depends(get_adicionar_tag_transacao_use_case)
):
    """
    Adiciona uma tag a uma transação.
    
    Evita duplicatas automaticamente - se já estiver associada, retorna sucesso.
    """
    try:
        use_case.execute(transacao_id, tag_id)
        return None
        
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{transacao_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_tag_transacao(
    transacao_id: int,
    tag_id: int,
    use_case: RemoverTagTransacaoUseCase = Depends(get_remover_tag_transacao_use_case)
):
    """
    Remove uma tag de uma transação.
    
    Se não estiver associada, retorna sucesso.
    """
    try:
        use_case.execute(transacao_id, tag_id)
        return None
        
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{transacao_id}/tags", response_model=List[TagResponse])
def listar_tags_transacao(
    transacao_id: int,
    use_case: ListarTagsTransacaoUseCase = Depends(get_listar_tags_transacao_use_case)
):
    """
    Lista todas as tags de uma transação.
    """
    try:
        tags = use_case.execute(transacao_id)
        
        # Converter DTOs → Responses
        return [
            TagResponse(
                id=tag.id,
                nome=tag.nome,
                cor=tag.cor,
                descricao=tag.descricao,
                criado_em=tag.criado_em,
                atualizado_em=tag.atualizado_em
            )
            for tag in tags
        ]
        
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _dto_to_response(dto: TransacaoDTO) -> TransacaoResponse:
    """Converte DTO de aplicação → Response de apresentação"""
    return TransacaoResponse(
        id=dto.id,
        data=dto.data,
        descricao=dto.descricao,
        valor=dto.valor,
        valor_original=dto.valor_original,
        tipo=dto.tipo.value,
        categoria=dto.categoria,
        origem=dto.origem,
        observacoes=dto.observacoes,
        data_fatura=dto.data_fatura,
        criado_em=dto.criado_em,
        atualizado_em=dto.atualizado_em,
        tag_ids=dto.tag_ids
    )
