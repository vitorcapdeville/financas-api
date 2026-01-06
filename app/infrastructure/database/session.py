"""
Gerenciamento de Sessões - Camada de Infraestrutura
"""
from typing import Generator
from sqlmodel import Session

from app.infrastructure.database.engine import engine


def get_session() -> Generator[Session, None, None]:
    """
    Dependency que fornece uma sessão SQLModel.
    
    Usado exclusivamente na camada de infraestrutura.
    NUNCA deve vazar para domínio ou aplicação.
    """
    with Session(engine) as session:
        yield session
