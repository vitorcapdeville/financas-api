"""
Modelos de tags e relacionamento com transações
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models_regra import Regra, RegraTag
    from app.models import Transacao


class Tag(SQLModel, table=True):
    """
    Modelo de Tag para categorização flexível de transações.
    Uma tag pode ser associada a múltiplas transações e regras.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, unique=True, description="Nome único da tag")
    cor: Optional[str] = Field(default=None, description="Cor hexadecimal para exibição (ex: #FF5733)")
    descricao: Optional[str] = Field(default=None, description="Descrição do propósito da tag")
    criado_em: datetime = Field(default_factory=datetime.now, description="Data de criação")
    atualizado_em: datetime = Field(default_factory=datetime.now, description="Data da última atualização")

    # Relacionamento com transações (cascade delete)
    transacoes: List["TransacaoTag"] = Relationship(
        back_populates="tag",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class TransacaoTag(SQLModel, table=True):
    """
    Tabela de associação many-to-many entre Transacao e Tag
    """
    transacao_id: int = Field(foreign_key="transacao.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
    criado_em: datetime = Field(default_factory=datetime.now, description="Data de associação")

    # Relacionamentos
    transacao: "Transacao" = Relationship(back_populates="tags")
    tag: Tag = Relationship(back_populates="transacoes")


# Schemas para API

class TagCreate(SQLModel):
    """Schema para criação de tag"""
    nome: str = Field(min_length=1, max_length=50, description="Nome da tag")
    cor: Optional[str] = Field(default=None, regex="^#[0-9A-Fa-f]{6}$", description="Cor hexadecimal")
    descricao: Optional[str] = Field(default=None, max_length=200, description="Descrição da tag")


class TagUpdate(SQLModel):
    """Schema para atualização de tag"""
    nome: Optional[str] = Field(default=None, min_length=1, max_length=50)
    cor: Optional[str] = Field(default=None, regex="^#[0-9A-Fa-f]{6}$")
    descricao: Optional[str] = Field(default=None, max_length=200)


class TagRead(SQLModel):
    """Schema para leitura de tag"""
    id: int
    nome: str
    cor: Optional[str]
    descricao: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
