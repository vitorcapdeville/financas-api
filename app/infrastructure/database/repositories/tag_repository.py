"""
Implementação concreta do repositório de Tags usando SQLModel
"""
from typing import List, Optional

from sqlmodel import Session, select, func

from app.domain.entities.tag import Tag
from app.domain.repositories.tag_repository import ITagRepository
from app.infrastructure.database.models.tag_model import TagModel


class TagRepository(ITagRepository):
    """
    Implementação concreta de ITagRepository usando SQLModel.
    
    Responsabilidades:
    - Traduzir entidades de domínio ↔ models SQLModel
    - Garantir unicidade case-insensitive de nomes
    - Isolar SQLModel da camada de domínio
    """
    
    def __init__(self, session: Session):
        self._session = session
    
    def criar(self, tag: Tag) -> Tag:
        """Cria uma nova tag"""
        # Verifica duplicidade
        if self.nome_existe(tag.nome):
            raise ValueError(f"Tag com nome '{tag.nome}' já existe")
        
        model = self._to_model(tag)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        
        return self._to_entity(model)
    
    def buscar_por_id(self, id: int) -> Optional[Tag]:
        """Busca tag por ID"""
        model = self._session.get(TagModel, id)
        if not model:
            return None
        return self._to_entity(model)
    
    def buscar_por_nome(self, nome: str) -> Optional[Tag]:
        """Busca tag por nome (case-insensitive)"""
        query = select(TagModel).where(func.lower(TagModel.nome) == nome.lower())
        model = self._session.exec(query).first()
        if not model:
            return None
        return self._to_entity(model)
    
    def listar(self) -> List[Tag]:
        """Lista todas as tags ordenadas por nome"""
        query = select(TagModel).order_by(TagModel.nome)
        models = self._session.exec(query).all()
        return [self._to_entity(m) for m in models]
    
    def atualizar(self, tag: Tag) -> Tag:
        """Atualiza tag existente"""
        if not tag.id:
            raise ValueError("Tag deve ter ID para atualizar")
        
        model = self._session.get(TagModel, tag.id)
        if not model:
            raise ValueError(f"Tag {tag.id} não encontrada")
        
        # Verifica duplicidade de nome (excluindo o próprio ID)
        if tag.nome != model.nome and self.nome_existe(tag.nome, excluir_id=tag.id):
            raise ValueError(f"Tag com nome '{tag.nome}' já existe")
        
        model.nome = tag.nome
        model.cor = tag.cor
        model.descricao = tag.descricao
        model.atualizado_em = tag.atualizado_em
        
        self._session.commit()
        self._session.refresh(model)
        
        return self._to_entity(model)
    
    def deletar(self, id: int) -> bool:
        """Deleta tag"""
        model = self._session.get(TagModel, id)
        if not model:
            return False
        
        self._session.delete(model)
        self._session.commit()
        return True
    
    def nome_existe(self, nome: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica se nome já existe (case-insensitive)"""
        query = select(func.count(TagModel.id)).where(
            func.lower(TagModel.nome) == nome.lower()
        )
        
        if excluir_id:
            query = query.where(TagModel.id != excluir_id)
        
        count = self._session.exec(query).one()
        return count > 0
    
    def listar_por_ids(self, ids: List[int]) -> List[Tag]:
        """Lista tags por múltiplos IDs"""
        if not ids:
            return []
        
        query = select(TagModel).where(TagModel.id.in_(ids))
        models = self._session.exec(query).all()
        return [self._to_entity(model) for model in models]
    
    def _to_entity(self, model: TagModel) -> Tag:
        """Converte SQLModel → Entidade de Domínio"""
        return Tag(
            id=model.id,
            nome=model.nome,
            cor=model.cor,
            descricao=model.descricao,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em
        )
    
    def _to_model(self, entity: Tag) -> TagModel:
        """Converte Entidade de Domínio → SQLModel"""
        return TagModel(
            id=entity.id,
            nome=entity.nome,
            cor=entity.cor,
            descricao=entity.descricao,
            criado_em=entity.criado_em,
            atualizado_em=entity.atualizado_em
        )
