from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    # Valor default para permitir importação em testes sem .env
    DATABASE_URL: str = "sqlite:///:memory:"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Singleton lazy para Settings - permite override em testes"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Compatibilidade com código existente
settings = get_settings()
