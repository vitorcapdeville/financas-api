"""
SQLModel Model para Configurações
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class ConfiguracaoModel(SQLModel, table=True):
    """
    Model SQLModel para persistência de Configurações.
    
    Sistema key-value para armazenar preferências da aplicação.
    """
    
    __tablename__ = "configuracoes"  # type: ignore
    __table_args__ = {'extend_existing': True}  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    chave: str = Field(unique=True, index=True, description="Chave única da configuração")
    valor: str = Field(description="Valor da configuração (string)")
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)
