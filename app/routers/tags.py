"""
Router para gerenciamento de tags
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete
from datetime import datetime
from typing import List

from app.database import get_session
from app.models_tags import Tag, TagCreate, TagUpdate, TagRead, TransacaoTag


router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=List[TagRead])
def listar_tags(session: Session = Depends(get_session)):
    """
    Lista todas as tags disponíveis
    """
    tags = session.exec(select(Tag).order_by(Tag.nome)).all()
    return tags


@router.get("/{tag_id}", response_model=TagRead)
def obter_tag(tag_id: int, session: Session = Depends(get_session)):
    """
    Obtém uma tag específica por ID
    """
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    return tag


@router.post("", response_model=TagRead, status_code=201)
def criar_tag(tag_data: TagCreate, session: Session = Depends(get_session)):
    """
    Cria uma nova tag
    """
    # Verifica se já existe uma tag com o mesmo nome
    existing = session.exec(select(Tag).where(Tag.nome == tag_data.nome)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Tag '{tag_data.nome}' já existe")
    
    tag = Tag(**tag_data.model_dump())
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagRead)
def atualizar_tag(
    tag_id: int,
    tag_data: TagUpdate,
    session: Session = Depends(get_session)
):
    """
    Atualiza uma tag existente
    """
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    
    # Se estiver tentando alterar o nome, verifica se não conflita com outra tag
    if tag_data.nome and tag_data.nome != tag.nome:
        existing = session.exec(select(Tag).where(Tag.nome == tag_data.nome)).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Tag '{tag_data.nome}' já existe")
    
    # Atualiza apenas os campos fornecidos
    update_data = tag_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tag, key, value)
    
    tag.atualizado_em = datetime.now()
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
def deletar_tag(tag_id: int, session: Session = Depends(get_session)):
    """
    Deleta uma tag.
    Remove também todas as associações com transações.
    """
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    
    # Remove explicitamente todas as associações com transações
    session.exec(delete(TransacaoTag).where(TransacaoTag.tag_id == tag_id))
    
    # Deleta a tag
    session.delete(tag)
    session.commit()
    return None
