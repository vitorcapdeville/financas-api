"""
Configuração do Engine SQLModel - Camada de Infraestrutura
"""
from sqlmodel import create_engine
from app.infrastructure.config import settings

# Engine global (singleton)
engine = create_engine(settings.DATABASE_URL, echo=False)
