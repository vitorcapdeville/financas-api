from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Configuracao(SQLModel, table=True):
    __tablename__ = "configuracoes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    chave: str = Field(unique=True, index=True)
    valor: str
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)


class ConfiguracaoCreate(SQLModel):
    chave: str
    valor: str


class ConfiguracaoRead(SQLModel):
    id: int
    chave: str
    valor: str
    criado_em: datetime
    atualizado_em: datetime
