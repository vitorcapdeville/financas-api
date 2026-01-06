"""
Configuração do Engine SQLModel - Camada de Infraestrutura
Engine com Lazy Initialization para suportar testes
"""
from typing import Optional
from sqlmodel import create_engine
from sqlalchemy.engine import Engine
from app.infrastructure.config import get_settings


_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """
    Retorna engine SQLModel (singleton com lazy initialization).
    Permite que testes importem módulos sem criar engine de produção.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.DATABASE_URL, echo=False)
    return _engine
