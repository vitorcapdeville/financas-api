from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://financas_user:financas_pass@localhost:5432/financas_db"
    
    class Config:
        env_file = ".env"


settings = Settings()
