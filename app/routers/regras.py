"""
Router para gerenciamento de regras automáticas de transações.

Endpoints:
- GET /regras: Listar regras (ordenadas por prioridade DESC)
- POST /regras: Criar nova regra (prioridade auto-calculada)
- PATCH /regras/{id}/prioridade: Atualizar prioridade de uma regra
- PATCH /regras/{id}/ativar-desativar: Toggle campo ativo
- DELETE /regras/{id}: Deletar regra
- POST /regras/{id}/aplicar: Aplicar regra retroativamente em todas transações
- POST /regras/aplicar-todas: Aplicar todas regras ativas em todas transações
"""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models_regra import (
    Regra,
    RegraTag,
    RegraCreate,
    RegraUpdate,
    RegraRead,
    TipoAcao
)
from app.models_tags import Tag
from app.services.regras import (
    calcular_proxima_prioridade,
    aplicar_regra_em_todas_transacoes,
    aplicar_todas_regras_em_todas_transacoes
)


router = APIRouter(prefix="/regras", tags=["regras"])


@router.get("", response_model=List[RegraRead])
def listar_regras(
    ativo: Optional[bool] = Query(default=None, description="Filtrar por regras ativas/inativas"),
    tipo_acao: Optional[TipoAcao] = Query(default=None, description="Filtrar por tipo de ação"),
    session: Session = Depends(get_session)
):
    """
    Lista todas as regras ordenadas por prioridade (maior primeiro).
    
    Parâmetros opcionais:
    - ativo: True/False para filtrar por status
    - tipo_acao: Filtrar por tipo específico
    """
    query = select(Regra).order_by(Regra.prioridade.desc())
    
    if ativo is not None:
        query = query.where(Regra.ativo == ativo)
    
    if tipo_acao is not None:
        query = query.where(Regra.tipo_acao == tipo_acao)
    
    regras = session.exec(query).all()
    return regras


@router.get("/{regra_id}", response_model=RegraRead)
def obter_regra(
    regra_id: int,
    session: Session = Depends(get_session)
):
    """Obtém uma regra específica por ID."""
    regra = session.get(Regra, regra_id)
    if not regra:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    return regra


@router.post("", response_model=RegraRead, status_code=201)
def criar_regra(
    regra_data: RegraCreate,
    tag_ids: Optional[List[int]] = Query(default=None, description="IDs das tags (apenas para tipo ADICIONAR_TAGS)"),
    session: Session = Depends(get_session)
):
    """
    Cria uma nova regra com prioridade auto-calculada.
    
    Para regras de tipo ADICIONAR_TAGS:
    - Forneça os IDs das tags no parâmetro tag_ids
    - Múltiplas tags podem ser fornecidas
    - acao_valor será preenchido automaticamente com o JSON dos IDs
    
    Para regras de tipo ALTERAR_CATEGORIA:
    - acao_valor deve conter o nome da categoria
    
    Para regras de tipo ALTERAR_VALOR:
    - acao_valor deve conter o percentual (0-100)
    """
    # Calcula prioridade
    prioridade = calcular_proxima_prioridade(session)
    
    # Validações específicas por tipo de ação
    if regra_data.tipo_acao == TipoAcao.ADICIONAR_TAGS:
        if not tag_ids:
            raise HTTPException(
                status_code=400,
                detail="Para regras de adicionar tags, forneça tag_ids"
            )
        
        # Verifica se todas as tags existem
        for tag_id in tag_ids:
            tag = session.get(Tag, tag_id)
            if not tag:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tag com ID {tag_id} não encontrada"
                )
        
        # Armazena os IDs como JSON no acao_valor
        acao_valor = json.dumps(tag_ids)
        
    elif regra_data.tipo_acao == TipoAcao.ALTERAR_VALOR:
        # Valida percentual
        try:
            percentual = float(regra_data.acao_valor)
            if not (0 <= percentual <= 100):
                raise HTTPException(
                    status_code=400,
                    detail="Percentual deve estar entre 0 e 100"
                )
            acao_valor = regra_data.acao_valor
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="acao_valor para ALTERAR_VALOR deve ser um número (percentual 0-100)"
            )
    else:
        # ALTERAR_CATEGORIA
        if not regra_data.acao_valor.strip():
            raise HTTPException(
                status_code=400,
                detail="acao_valor não pode ser vazio para ALTERAR_CATEGORIA"
            )
        acao_valor = regra_data.acao_valor
    
    # Cria a regra
    regra = Regra(
        nome=regra_data.nome,
        tipo_acao=regra_data.tipo_acao,
        criterio_tipo=regra_data.criterio_tipo,
        criterio_valor=regra_data.criterio_valor,
        acao_valor=acao_valor,
        prioridade=prioridade,
        ativo=True  # Sempre ativa por padrão
    )
    
    session.add(regra)
    session.commit()
    session.refresh(regra)
    
    # Se for regra de tags, cria as associações
    if regra_data.tipo_acao == TipoAcao.ADICIONAR_TAGS and tag_ids:
        for tag_id in tag_ids:
            regra_tag = RegraTag(regra_id=regra.id, tag_id=tag_id)
            session.add(regra_tag)
        session.commit()
        session.refresh(regra)
    
    return regra


@router.patch("/{regra_id}/prioridade", response_model=RegraRead)
def atualizar_prioridade(
    regra_id: int,
    nova_prioridade: int = Query(..., ge=1, description="Nova prioridade (mínimo 1)"),
    session: Session = Depends(get_session)
):
    """
    Atualiza apenas a prioridade de uma regra.
    
    Maior prioridade = executada primeiro.
    """
    regra = session.get(Regra, regra_id)
    if not regra:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    
    regra.prioridade = nova_prioridade
    regra.atualizado_em = datetime.now()
    
    session.add(regra)
    session.commit()
    session.refresh(regra)
    
    return regra


@router.patch("/{regra_id}/ativar-desativar", response_model=RegraRead)
def toggle_ativo(
    regra_id: int,
    session: Session = Depends(get_session)
):
    """
    Alterna o status ativo/inativo de uma regra.
    
    Regras inativas não são aplicadas automaticamente.
    """
    regra = session.get(Regra, regra_id)
    if not regra:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    
    regra.ativo = not regra.ativo
    regra.atualizado_em = datetime.now()
    
    session.add(regra)
    session.commit()
    session.refresh(regra)
    
    return regra


@router.delete("/{regra_id}", status_code=204)
def deletar_regra(
    regra_id: int,
    session: Session = Depends(get_session)
):
    """
    Deleta uma regra permanentemente.
    
    ⚠️ ATENÇÃO: Transações que foram modificadas por esta regra
    PERMANECERÃO com as alterações aplicadas. Não há rollback automático.
    """
    regra = session.get(Regra, regra_id)
    if not regra:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    
    # Deleta associações RegraTag (cascade automático se configurado no modelo)
    stmt = select(RegraTag).where(RegraTag.regra_id == regra_id)
    regra_tags = session.exec(stmt).all()
    for rt in regra_tags:
        session.delete(rt)
    
    session.delete(regra)
    session.commit()
    
    return None


@router.post("/{regra_id}/aplicar")
def aplicar_regra_retroativamente(
    regra_id: int,
    session: Session = Depends(get_session)
):
    """
    Aplica uma regra específica em todas as transações existentes
    que correspondem aos critérios.
    
    Retorna o número de transações modificadas.
    """
    regra = session.get(Regra, regra_id)
    if not regra:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    
    num_transacoes = aplicar_regra_em_todas_transacoes(regra_id, session)
    
    return {
        "regra_id": regra_id,
        "regra_nome": regra.nome,
        "transacoes_modificadas": num_transacoes
    }


@router.post("/aplicar-todas")
def aplicar_todas_regras_retroativamente(
    session: Session = Depends(get_session)
):
    """
    Aplica TODAS as regras ativas em TODAS as transações existentes.
    
    As regras são aplicadas em ordem de prioridade (maior primeiro).
    
    ⚠️ Use com cuidado: pode modificar muitas transações de uma vez.
    
    Retorna o número total de aplicações de regras.
    """
    total_aplicacoes = aplicar_todas_regras_em_todas_transacoes(session)
    
    return {
        "total_aplicacoes": total_aplicacoes,
        "mensagem": f"{total_aplicacoes} aplicações de regras realizadas"
    }
