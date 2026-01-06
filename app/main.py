"""
FastAPI Application - Entry Point
Aplicação refatorada com Clean Architecture e SOLID principles.

Estrutura:
- domain/: Entidades, Value Objects, Interfaces de Repositórios
- application/: Use Cases, DTOs, Exceções
- infrastructure/: Implementações concretas (Repositórios, Models SQLModel)
- interfaces/api/: Routers FastAPI, Schemas Pydantic, Dependency Injection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.interfaces.api.routers import transacoes
from app.interfaces.api.routers import tags
from app.interfaces.api.routers import regras
from app.interfaces.api.routers import configuracoes
from app.interfaces.api.routers import importacao

app = FastAPI(title="Finanças Pessoais API", description="API para gerenciamento de finanças pessoais", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transacoes.router)
app.include_router(tags.router)
app.include_router(regras.router)
app.include_router(configuracoes.router)
app.include_router(importacao.router)


@app.get("/")
def root():
    return {
        "message": "Finanças Pessoais API",
        "docs": "/docs",
        "version": "2.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
