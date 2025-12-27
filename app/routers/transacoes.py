from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, or_
from typing import List, Optional
from datetime import date, datetime

from app.database import get_session
from app.models import Transacao, TransacaoCreate, TransacaoUpdate, TransacaoRead
from app.models_config import Configuracao

router = APIRouter(prefix="/transacoes", tags=["Transações"])


def obter_criterio_data(session: Session) -> str:
    """Obtém o critério de data configurado (data_transacao ou data_fatura)"""
    query = select(Configuracao).where(Configuracao.chave == "criterio_data_transacao")
    config = session.exec(query).first()
    return config.valor if config else "data_transacao"


@router.post("/", response_model=TransacaoRead)
def criar_transacao(
    transacao: TransacaoCreate,
    session: Session = Depends(get_session)
):
    """Cria uma nova transação"""
    db_transacao = Transacao.model_validate(transacao)
    session.add(db_transacao)
    session.commit()
    session.refresh(db_transacao)
    return db_transacao


@router.get("/", response_model=List[TransacaoRead])
def listar_transacoes(
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2000),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    categoria: Optional[str] = None,
    tipo: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Lista todas as transações com filtros opcionais
    
    O filtro de data pode usar o campo 'data' (data da transação) ou 'data_fatura'
    (data de pagamento da fatura) dependendo da configuração 'criterio_data_transacao'.
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
    
    transacoes = session.exec(query).all()
    return transacoes


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


@router.get("/{transacao_id}", response_model=TransacaoRead)
def obter_transacao(
    transacao_id: int,
    session: Session = Depends(get_session)
):
    """Obtém uma transação específica pelo ID"""
    transacao = session.get(Transacao, transacao_id)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return transacao


@router.patch("/{transacao_id}", response_model=TransacaoRead)
def atualizar_transacao(
    transacao_id: int,
    transacao_update: TransacaoUpdate,
    session: Session = Depends(get_session)
):
    """Atualiza uma transação existente"""
    db_transacao = session.get(Transacao, transacao_id)
    if not db_transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    update_data = transacao_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transacao, key, value)
    
    db_transacao.atualizado_em = datetime.now()
    session.add(db_transacao)
    session.commit()
    session.refresh(db_transacao)
    return db_transacao




