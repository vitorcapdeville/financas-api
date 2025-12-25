from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.routers import transacoes, importacao, configuracoes

app = FastAPI(
    title="Finanças Pessoais API",
    description="API para gerenciamento de finanças pessoais",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(transacoes.router)
app.include_router(importacao.router)
app.include_router(configuracoes.router)


@app.on_event("startup")
def on_startup():
    """Cria as tabelas do banco de dados ao iniciar a aplicação"""
    create_db_and_tables()


@app.get("/")
def root():
    return {
        "message": "Finanças Pessoais API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
