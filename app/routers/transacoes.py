from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, or_, func
from typing import List, Optional
from datetime import date, datetime

from app.database import get_session
from app.models import Transacao, TransacaoCreate, TransacaoUpdate
from app.models_config import Configuracao
from app.models_tags import Tag, TransacaoTag, TagRead
from app.schemas import TransacaoReadWithTags

router = APIRouter(prefix="/transacoes", tags=["Transações"])


def obter_criterio_data(session: Session) -> str:
    """Obtém o critério de data configurado (data_transacao ou data_fatura)"""
    query = select(Configuracao).where(Configuracao.chave == "criterio_data_transacao")
    config = session.exec(query).first()
    return config.valor if config else "data_transacao"


@router.post("/", response_model=TransacaoReadWithTags)
def criar_transacao(
    transacao: TransacaoCreate,
    session: Session = Depends(get_session)
):
    """Cria uma nova transação"""
    db_transacao = Transacao.model_validate(transacao)
    # Define valor_original como o valor inicial
    if db_transacao.valor_original is None:
        db_transacao.valor_original = db_transacao.valor
    session.add(db_transacao)
    session.commit()
    session.refresh(db_transacao)
    
    # Retorna com tags vazias
    transacao_dict = db_transacao.model_dump()
    transacao_dict['tags'] = []
    return TransacaoReadWithTags(**transacao_dict)


@router.get("/", response_model=List[TransacaoReadWithTags])
def listar_transacoes(
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2000),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    categoria: Optional[str] = None,
    tipo: Optional[str] = None,
    tags: Optional[str] = Query(None, description="IDs de tags separados por vírgula (ex: '1,2,3')"),
    session: Session = Depends(get_session)
):
    """Lista todas as transações com filtros opcionais
    
    O filtro de data pode usar o campo 'data' (data da transação) ou 'data_fatura'
    (data de pagamento da fatura) dependendo da configuração 'criterio_data_transacao'.
    
    O filtro de tags aceita IDs separados por vírgula e retorna transações que possuem
    QUALQUER UMA das tags especificadas (operação OR).
    """
    query = select(Transacao)
    
    # Obtém o critério de data configurado
    criterio = obter_criterio_data(session)
    
    # Prioriza data_inicio/data_fim se fornecidos, senão usa mes/ano
    if data_inicio and data_fim:
        if criterio == "data_fatura":
            # Usa data_fatura quando disponível, senão data da transação
            query = query.where(
                or_(
                    (Transacao.data_fatura >= data_inicio) & (Transacao.data_fatura <= data_fim),
                    (Transacao.data_fatura.is_(None)) & (Transacao.data >= data_inicio) & (Transacao.data <= data_fim)
                )
            )
        else:
            query = query.where(
                Transacao.data >= data_inicio,
                Transacao.data <= data_fim
            )
    elif mes and ano:
        data_inicio_calc = date(ano, mes, 1)
        if mes < 12:
            data_fim_calc = date(ano, mes + 1, 1)
        else:
            data_fim_calc = date(ano + 1, 1, 1)
        
        if criterio == "data_fatura":
            # Usa data_fatura quando disponível, senão data da transação
            query = query.where(
                or_(
                    (Transacao.data_fatura >= data_inicio_calc) & (Transacao.data_fatura < data_fim_calc),
                    (Transacao.data_fatura.is_(None)) & (Transacao.data >= data_inicio_calc) & (Transacao.data < data_fim_calc)
                )
            )
        else:
            query = query.where(
                Transacao.data >= data_inicio_calc,
                Transacao.data < data_fim_calc
            )
    
    if categoria:
        # Se categoria for 'null', busca transações sem categoria
        if categoria == 'null':
            query = query.where(Transacao.categoria.is_(None))
        else:
            query = query.where(Transacao.categoria == categoria)
    
    if tipo:
        query = query.where(Transacao.tipo == tipo)
    
    # Filtro por tags
    if tags:
        try:
            tag_ids = [int(tag_id.strip()) for tag_id in tags.split(',')]
            # Join com TransacaoTag para filtrar transações que possuem qualquer uma das tags
            query = query.join(TransacaoTag).where(TransacaoTag.tag_id.in_(tag_ids)).distinct()
        except ValueError:
            raise HTTPException(status_code=400, detail="IDs de tags inválidos")
    
    transacoes = session.exec(query).all()
    
    # Carrega as tags para cada transação
    result = []
    for transacao in transacoes:
        # Busca as tags associadas
        tags_query = select(Tag).join(TransacaoTag).where(TransacaoTag.transacao_id == transacao.id)
        transacao_tags = session.exec(tags_query).all()
        
        # Cria o TransacaoReadWithTags com as tags
        transacao_dict = transacao.model_dump()
        transacao_dict['tags'] = [TagRead.model_validate(tag) for tag in transacao_tags]
        result.append(TransacaoReadWithTags(**transacao_dict))
    
    return result


@router.get("/categorias", response_model=List[str])
def listar_categorias(session: Session = Depends(get_session)):
    """Lista todas as categorias únicas existentes"""
    query = select(Transacao.categoria).distinct()
    categorias = session.exec(query).all()
    # Filtra None e retorna lista ordenada
    categorias_validas = [c for c in categorias if c is not None]
    return sorted(categorias_validas)


@router.get("/resumo/mensal")
def resumo_mensal(
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2000),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    tags: Optional[str] = Query(None, description="IDs de tags separados por vírgula (ex: '1,2,3')"),
    session: Session = Depends(get_session)
):
    """Retorna resumo mensal de entradas e saídas por categoria
    
    O filtro de data pode usar o campo 'data' (data da transação) ou 'data_fatura'
    (data de pagamento da fatura) dependendo da configuração 'criterio_data_transacao'.
    """
    # Obtém o critério de data configurado
    criterio = obter_criterio_data(session)
    
    # Prioriza data_inicio/data_fim se fornecidos, senão usa mes/ano
    if data_inicio and data_fim:
        periodo_inicio = data_inicio
        periodo_fim = data_fim
    elif mes and ano:
        periodo_inicio = date(ano, mes, 1)
        if mes < 12:
            periodo_fim = date(ano, mes + 1, 1)
        else:
            periodo_fim = date(ano + 1, 1, 1)
    else:
        raise HTTPException(status_code=400, detail="Forneça mes/ano ou data_inicio/data_fim")
    
    # Aplica o filtro de data baseado no critério configurado
    if criterio == "data_fatura":
        # Usa data_fatura quando disponível, senão data da transação
        query = select(Transacao).where(
            or_(
                (Transacao.data_fatura >= periodo_inicio) & (Transacao.data_fatura <= periodo_fim),
                (Transacao.data_fatura.is_(None)) & (Transacao.data >= periodo_inicio) & (Transacao.data <= periodo_fim)
            )
        )
    else:
        query = select(Transacao).where(
            Transacao.data >= periodo_inicio,
            Transacao.data <= periodo_fim
        )
    
    # Filtro por tags
    if tags:
        try:
            tag_ids = [int(tag_id.strip()) for tag_id in tags.split(',')]
            # Join com TransacaoTag para filtrar transações que possuem qualquer uma das tags
            query = query.join(TransacaoTag).where(TransacaoTag.tag_id.in_(tag_ids)).distinct()
        except ValueError:
            raise HTTPException(status_code=400, detail="IDs de tags inválidos")
    
    transacoes = session.exec(query).all()
    
    entradas = {}
    saidas = {}
    total_entradas = 0.0
    total_saidas = 0.0
    
    for t in transacoes:
        categoria = t.categoria or "Sem categoria"
        if t.tipo == "entrada":
            entradas[categoria] = entradas.get(categoria, 0.0) + t.valor
            total_entradas += t.valor
        else:
            saidas[categoria] = saidas.get(categoria, 0.0) + t.valor
            total_saidas += t.valor
    
    return {
        "mes": mes,
        "ano": ano,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "saldo": total_entradas - total_saidas,
        "entradas_por_categoria": entradas,
        "saidas_por_categoria": saidas
    }


@router.get("/{transacao_id}", response_model=TransacaoReadWithTags)
def obter_transacao(
    transacao_id: int,
    session: Session = Depends(get_session)
):
    """Obtém uma transação específica pelo ID"""
    transacao = session.get(Transacao, transacao_id)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Busca as tags associadas
    tags_query = select(Tag).join(TransacaoTag).where(TransacaoTag.transacao_id == transacao.id)
    transacao_tags = session.exec(tags_query).all()
    
    # Cria o TransacaoReadWithTags com as tags
    transacao_dict = transacao.model_dump()
    transacao_dict['tags'] = [TagRead.model_validate(tag) for tag in transacao_tags]
    return TransacaoReadWithTags(**transacao_dict)


@router.patch("/{transacao_id}", response_model=TransacaoReadWithTags)
def atualizar_transacao(
    transacao_id: int,
    transacao_update: TransacaoUpdate,
    session: Session = Depends(get_session)
):
    """Atualiza uma transação existente"""
    db_transacao = session.get(Transacao, transacao_id)
    if not db_transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Se valor_original ainda não foi definido, define antes de atualizar
    if db_transacao.valor_original is None:
        db_transacao.valor_original = db_transacao.valor
    
    update_data = transacao_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transacao, key, value)
    
    db_transacao.atualizado_em = datetime.now()
    session.add(db_transacao)
    session.commit()
    session.refresh(db_transacao)
    
    # Busca as tags associadas
    tags_query = select(Tag).join(TransacaoTag).where(TransacaoTag.transacao_id == db_transacao.id)
    transacao_tags = session.exec(tags_query).all()
    
    # Cria o TransacaoReadWithTags com as tags
    transacao_dict = db_transacao.model_dump()
    transacao_dict['tags'] = [TagRead.model_validate(tag) for tag in transacao_tags]
    return TransacaoReadWithTags(**transacao_dict)


@router.post("/{transacao_id}/restaurar-valor", response_model=TransacaoReadWithTags)
def restaurar_valor_original(
    transacao_id: int,
    session: Session = Depends(get_session)
):
    """Restaura o valor original de uma transação"""
    db_transacao = session.get(Transacao, transacao_id)
    if not db_transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    if db_transacao.valor_original is None:
        raise HTTPException(status_code=400, detail="Transação não possui valor original salvo")
    
    # Restaura o valor original
    db_transacao.valor = db_transacao.valor_original
    db_transacao.atualizado_em = datetime.now()
    
    session.add(db_transacao)
    session.commit()
    session.refresh(db_transacao)
    
    # Busca as tags associadas
    tags_query = select(Tag).join(TransacaoTag).where(TransacaoTag.transacao_id == db_transacao.id)
    transacao_tags = session.exec(tags_query).all()
    
    # Cria o TransacaoReadWithTags com as tags
    transacao_dict = db_transacao.model_dump()
    transacao_dict['tags'] = [TagRead.model_validate(tag) for tag in transacao_tags]
    return TransacaoReadWithTags(**transacao_dict)


@router.post("/{transacao_id}/tags/{tag_id}", status_code=204)
def adicionar_tag_transacao(
    transacao_id: int,
    tag_id: int,
    session: Session = Depends(get_session)
):
    """Adiciona uma tag a uma transação"""
    # Verifica se transação existe
    transacao = session.get(Transacao, transacao_id)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Verifica se tag existe
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    
    # Verifica se associação já existe
    existing = session.exec(
        select(TransacaoTag).where(
            TransacaoTag.transacao_id == transacao_id,
            TransacaoTag.tag_id == tag_id
        )
    ).first()
    
    if existing:
        # Já está associada, retorna sucesso
        return None
    
    # Cria a associação
    transacao_tag = TransacaoTag(transacao_id=transacao_id, tag_id=tag_id)
    session.add(transacao_tag)
    
    # Atualiza timestamp da transação
    transacao.atualizado_em = datetime.now()
    session.add(transacao)
    
    session.commit()
    return None


@router.delete("/{transacao_id}/tags/{tag_id}", status_code=204)
def remover_tag_transacao(
    transacao_id: int,
    tag_id: int,
    session: Session = Depends(get_session)
):
    """Remove uma tag de uma transação"""
    # Verifica se transação existe
    transacao = session.get(Transacao, transacao_id)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Busca a associação
    transacao_tag = session.exec(
        select(TransacaoTag).where(
            TransacaoTag.transacao_id == transacao_id,
            TransacaoTag.tag_id == tag_id
        )
    ).first()
    
    if not transacao_tag:
        # Não está associada, retorna sucesso
        return None
    
    # Remove a associação
    session.delete(transacao_tag)
    
    # Atualiza timestamp da transação
    transacao.atualizado_em = datetime.now()
    session.add(transacao)
    
    session.commit()
    return None


@router.delete("/{transacao_id}", status_code=204)
def deletar_transacao(
    transacao_id: int,
    session: Session = Depends(get_session)
):
    """
    Deleta uma transação.
    
    CASCADE DELETE: Remove automaticamente todas as associações com tags (TransacaoTag),
    mas mantém as tags originais.
    """
    # Verifica se transação existe
    transacao = session.get(Transacao, transacao_id)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Deleta a transação (CASCADE DELETE cuida das associações)
    session.delete(transacao)
    session.commit()
    
    return None


@router.get("/{transacao_id}/tags", response_model=List[TagRead])
def listar_tags_transacao(
    transacao_id: int,
    session: Session = Depends(get_session)
):
    """Lista todas as tags de uma transação"""
    # Verifica se transação existe
    transacao = session.get(Transacao, transacao_id)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    # Busca as tags associadas
    tags = session.exec(
        select(Tag).join(TransacaoTag).where(TransacaoTag.transacao_id == transacao_id)
    ).all()
    
    return tags
