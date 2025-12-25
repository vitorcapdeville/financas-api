from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models_config import Configuracao, ConfiguracaoCreate, ConfiguracaoRead

router = APIRouter(prefix="/configuracoes", tags=["Configurações"])


@router.get("/{chave}")
def obter_configuracao(
    chave: str,
    session: Session = Depends(get_session)
):
    """Obtém uma configuração pela chave"""
    query = select(Configuracao).where(Configuracao.chave == chave)
    config = session.exec(query).first()
    
    if not config:
        return {"chave": chave, "valor": None}
    
    return {"chave": config.chave, "valor": config.valor}


@router.post("/")
def salvar_configuracao(
    configuracao: ConfiguracaoCreate,
    session: Session = Depends(get_session)
):
    """Cria ou atualiza uma configuração"""
    query = select(Configuracao).where(Configuracao.chave == configuracao.chave)
    db_config = session.exec(query).first()
    
    if db_config:
        # Atualiza existente
        db_config.valor = configuracao.valor
        db_config.atualizado_em = datetime.now()
        session.add(db_config)
    else:
        # Cria nova
        db_config = Configuracao.model_validate(configuracao)
        session.add(db_config)
    
    session.commit()
    session.refresh(db_config)
    return {"chave": db_config.chave, "valor": db_config.valor}
