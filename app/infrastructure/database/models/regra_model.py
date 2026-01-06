"""
SQLModel Models para Regras
"""
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Integer, ForeignKey
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.database.models.tag_model import TagModel


class RegraModel(SQLModel, table=True):
    """
    Model SQLModel para persistência de Regras.
    
    IMPORTANTE: Model de infraestrutura, NÃO entidade de domínio.
    """
    
    __tablename__ = "regra"  # type: ignore
    __table_args__ = {'extend_existing': True}  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True, index=True, description="Nome único da regra")
    tipo_acao: str = Field(description="alterar_categoria, adicionar_tags, alterar_valor")
    criterio_tipo: str = Field(description="descricao_exata, descricao_contem, categoria")
    criterio_valor: str = Field(description="Valor do critério")
    acao_valor: str = Field(description="Valor da ação (categoria, JSON de tag IDs, ou percentual)")
    prioridade: int = Field(unique=True, index=True, description="Ordem de execução (maior = primeiro)")
    ativo: bool = Field(default=True, description="Se a regra está ativa")
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)
    
    # Relacionamento many-to-many com tags (para ADICIONAR_TAGS)
    tags: List["RegraTagModel"] = Relationship(
        back_populates="regra",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class RegraTagModel(SQLModel, table=True):
    """
    Tabela de associação entre Regra e Tag.
    """
    
    __tablename__ = "regratag"  # type: ignore
    __table_args__ = {'extend_existing': True}  # type: ignore
    
    regra_id: int = Field(sa_column=Column(Integer, ForeignKey("regra.id", ondelete="CASCADE"), primary_key=True))
    tag_id: int = Field(sa_column=Column(Integer, ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True))
    
    # Relacionamentos
    regra: "RegraModel" = Relationship(back_populates="tags")
    tag: "TagModel" = Relationship()
