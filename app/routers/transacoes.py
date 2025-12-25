from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import date, datetime

from app.database import get_session
from app.models import Transacao, TransacaoCreate, TransacaoUpdate, TransacaoRead

router = APIRouter(prefix="/transacoes", tags=["Transações"])


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
    categoria: Optional[str] = None,
    tipo: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Lista todas as transações com filtros opcionais"""
    query = select(Transacao)
    
    if mes and ano:
        data_inicio = date(ano, mes, 1)
        if mes < 12:
            data_fim = date(ano, mes + 1, 1)
        else:
            data_fim = date(ano + 1, 1, 1)
        query = query.where(
            Transacao.data >= data_inicio,
            Transacao.data < data_fim
        )
    
    if categoria:
        query = query.where(Transacao.categoria == categoria)
    
    if tipo:
        query = query.where(Transacao.tipo == tipo)
    
    transacoes = session.exec(query).all()
    return transacoes


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


@router.delete("/{transacao_id}")
def deletar_transacao(
    transacao_id: int,
    session: Session = Depends(get_session)
):
    """Deleta uma transação"""
    transacao = session.get(Transacao, transacao_id)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    session.delete(transacao)
    session.commit()
    return {"message": "Transação deletada com sucesso"}


@router.get("/resumo/mensal")
def resumo_mensal(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000),
    session: Session = Depends(get_session)
):
    """Retorna resumo mensal de entradas e saídas por categoria"""
    data_inicio = date(ano, mes, 1)
    if mes < 12:
        data_fim = date(ano, mes + 1, 1)
    else:
        data_fim = date(ano + 1, 1, 1)
    
    query = select(Transacao).where(
        Transacao.data >= data_inicio,
        Transacao.data < data_fim
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
