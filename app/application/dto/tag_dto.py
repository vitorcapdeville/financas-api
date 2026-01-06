"""
DTOs para Tags
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CriarTagDTO:
    """DTO para criação de tag"""
    nome: str
    cor: Optional[str] = None
    descricao: Optional[str] = None


@dataclass
class AtualizarTagDTO:
    """DTO para atualização parcial de tag"""
    nome: Optional[str] = None
    cor: Optional[str] = None
    descricao: Optional[str] = None


@dataclass
class TagDTO:
    """DTO completo de tag (output)"""
    id: int
    nome: str
    cor: Optional[str]
    descricao: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
