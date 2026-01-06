"""
SQLModel Models para Tags
"""
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import model_validator

if TYPE_CHECKING:
    from app.infrastructure.database.models.transacao_model import TransacaoModel
    from app.infrastructure.database.models.regra_model import RegraTagModel


class TagModel(SQLModel, table=True):
    """
    Model SQLModel para persistência de Tags.
    
    IMPORTANTE: Model de infraestrutura, NÃO entidade de domínio.
    """
    
    __tablename__ = "tag"  # type: ignore
    __table_args__ = {'extend_existing': True}  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, description="Nome único (case-insensitive)")
    cor: Optional[str] = Field(default=None, description="Cor hexadecimal (ex: #FF5733)")
    descricao: Optional[str] = Field(default=None, description="Descrição")
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)
    
    # Relacionamentos
    transacoes: List["TransacaoTagModel"] = Relationship(
        back_populates="tag",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    @model_validator(mode='after')
    def normalizar_nome(self):
        """Normaliza o nome"""
        if self.nome:
            self.nome = self.nome.strip()
        return self


class TransacaoTagModel(SQLModel, table=True):
    """
    Tabela de associação many-to-many entre Transacao e Tag.
    """
    
    __tablename__ = "transacaotag"  # type: ignore
    __table_args__ = {'extend_existing': True}  # type: ignore
    
    transacao_id: int = Field(foreign_key="transacao.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
    criado_em: datetime = Field(default_factory=datetime.now)
    
    # Relacionamentos
    transacao: "TransacaoModel" = Relationship(back_populates="tags")
    tag: "TagModel" = Relationship(back_populates="transacoes")
