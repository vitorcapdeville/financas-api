"""
Schemas Pydantic para API - Camada de Apresentação
Modelos de request/response para FastAPI
"""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Dict


# ===== TRANSAÇÃO =====

class TransacaoCreateRequest(BaseModel):
    """Schema para request de criação de transação"""
    data: date
    descricao: str = Field(min_length=1)
    valor: float = Field(gt=0)
    tipo: str = Field(pattern="^(entrada|saida)$")
    categoria: Optional[str] = None
    origem: str = "manual"
    observacoes: Optional[str] = None
    data_fatura: Optional[date] = None


class TransacaoUpdateRequest(BaseModel):
    """Schema para request de atualização parcial"""
    descricao: Optional[str] = Field(None, min_length=1)
    valor: Optional[float] = Field(None, gt=0)
    categoria: Optional[str] = None
    observacoes: Optional[str] = None
    data_fatura: Optional[date] = None


class TransacaoResponse(BaseModel):
    """Schema para response de transação"""
    id: int
    data: date
    descricao: str
    valor: float
    valor_original: Optional[float]
    tipo: str
    categoria: Optional[str]
    origem: str
    observacoes: Optional[str]
    data_fatura: Optional[date]
    criado_em: datetime
    atualizado_em: datetime
    tag_ids: List[int] = []
    
    class Config:
        from_attributes = True


class ResumoMensalResponse(BaseModel):
    """Schema para response de resumo mensal"""
    mes: Optional[int]
    ano: Optional[int]
    total_entradas: float
    total_saidas: float
    saldo: float
    entradas_por_categoria: Dict[str, float]
    saidas_por_categoria: Dict[str, float]
    
    class Config:
        from_attributes = True


# ===== TAG =====

class TagCreateRequest(BaseModel):
    """Schema para request de criação de tag"""
    nome: str = Field(min_length=1, max_length=50)
    cor: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

# ===== TAG =====

class TagCreateRequest(BaseModel):
    """Schema para request de criação de tag"""
    nome: str = Field(min_length=1)
    cor: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    descricao: Optional[str] = None


class TagUpdateRequest(BaseModel):
    """Schema para request de atualização de tag"""
    nome: Optional[str] = Field(None, min_length=1)
    cor: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    descricao: Optional[str] = None


class TagResponse(BaseModel):
    """Schema para response de tag"""
    id: int
    nome: str
    cor: Optional[str]
    descricao: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
    
    class Config:
        from_attributes = True


# ===== CONFIGURAÇÃO =====

class ConfiguracaoRequest(BaseModel):
    """Schema para request de configuração"""
    chave: str
    valor: str


class ConfiguracaoResponse(BaseModel):
    """Schema para response de configuração"""
    chave: str
    valor: str


# ===== REGRA =====

class RegraCreateRequest(BaseModel):
    """Schema para request de criação de regra"""
    nome: str = Field(min_length=1, max_length=100)
    tipo_acao: str = Field(pattern="^(alterar_categoria|adicionar_tags|alterar_valor)$")
    criterio_tipo: str = Field(pattern="^(descricao_exata|descricao_contem|categoria)$")
    criterio_valor: str = Field(min_length=1)
    acao_valor: str = Field(min_length=1)
    prioridade: Optional[int] = Field(None, ge=0)
    ativo: bool = True
    tag_ids: Optional[List[int]] = None


class RegraUpdateRequest(BaseModel):
    """Schema para request de atualização de regra"""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    tipo_acao: Optional[str] = Field(None, pattern="^(alterar_categoria|adicionar_tags|alterar_valor)$")
    criterio_tipo: Optional[str] = Field(None, pattern="^(descricao_exata|descricao_contem|categoria)$")
    criterio_valor: Optional[str] = Field(None, min_length=1)
    acao_valor: Optional[str] = Field(None, min_length=1)
    prioridade: Optional[int] = Field(None, ge=0)
    ativo: Optional[bool] = None
    tag_ids: Optional[List[int]] = None


class RegraResponse(BaseModel):
    """Schema para response de regra"""
    id: int
    nome: str
    tipo_acao: str
    criterio_tipo: str
    criterio_valor: str
    acao_valor: str
    prioridade: int
    ativo: bool
    tag_ids: List[int]
    
    class Config:
        from_attributes = True


class ResultadoAplicacaoResponse(BaseModel):
    """Schema para response de aplicação de regra"""
    sucesso: bool
    transacoes_modificadas: int
    mensagem: str


# ===== IMPORTAÇÃO =====

class ResultadoImportacaoResponse(BaseModel):
    """Schema para response de importação"""
    total_importado: int
    transacoes_ids: List[int]
    mensagem: str

