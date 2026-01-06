"""
Entidade de domínio - Transação
Regras de negócio puras, sem dependências de frameworks
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List

from app.domain.value_objects.tipo_transacao import TipoTransacao


@dataclass
class Transacao:
    """
    Entidade de domínio representando uma transação financeira.
    
    Regras de Negócio:
    - data_fatura deve ser >= data (se fornecida)
    - valor deve ser positivo
    - valor_original preserva o valor inicial antes de edições
    - categoria é opcional mas recomendada para análises
    - tags podem ser associadas para categorização flexível
    """
    
    # Identificação
    id: Optional[int] = None
    
    # Dados principais
    data: date = field(default_factory=date.today)
    descricao: str = ""
    valor: float = 0.0
    tipo: TipoTransacao = TipoTransacao.SAIDA
    
    # Metadados
    categoria: Optional[str] = None
    origem: str = "manual"  # manual, extrato_bancario, fatura_cartao
    observacoes: Optional[str] = None
    
    # Dados de cartão de crédito
    data_fatura: Optional[date] = None
    
    # Histórico
    valor_original: Optional[float] = None
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    
    # Relacionamentos (IDs apenas - sem acoplamento com ORM)
    tag_ids: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Valida regras de negócio após inicialização"""
        self._validar_data_fatura()
        self._validar_valor()
        self._inicializar_valor_original()
    
    def _validar_data_fatura(self):
        """Regra: data_fatura deve ser >= data"""
        if self.data_fatura and self.data_fatura < self.data:
            raise ValueError("data_fatura deve ser maior ou igual a data")
    
    def _validar_valor(self):
        """Regra: valor deve ser positivo"""
        if self.valor < 0:
            raise ValueError("valor deve ser positivo")
    
    def _inicializar_valor_original(self):
        """Regra: valor_original preserva o valor inicial"""
        if self.valor_original is None:
            self.valor_original = self.valor
    
    def alterar_categoria(self, nova_categoria: str):
        """Altera a categoria da transação"""
        self.categoria = nova_categoria
        self.atualizar()
    
    def alterar_valor(self, novo_valor: float):
        """Altera o valor da transação, preservando o original"""
        if novo_valor < 0:
            raise ValueError("valor deve ser positivo")
        self.valor = novo_valor
        self.atualizar()
    
    def adicionar_tag(self, tag_id: int):
        """Adiciona uma tag à transação (se não existir)"""
        if tag_id not in self.tag_ids:
            self.tag_ids.append(tag_id)
            self.atualizar()
    
    def remover_tag(self, tag_id: int):
        """Remove uma tag da transação"""
        if tag_id in self.tag_ids:
            self.tag_ids.remove(tag_id)
            self.atualizar()
    
    def atualizar(self):
        """Marca a transação como atualizada"""
        self.atualizado_em = datetime.now()
    
    def eh_entrada(self) -> bool:
        """Verifica se é uma entrada"""
        return self.tipo == TipoTransacao.ENTRADA
    
    def eh_saida(self) -> bool:
        """Verifica se é uma saída"""
        return self.tipo == TipoTransacao.SAIDA
    
    def tem_categoria(self) -> bool:
        """Verifica se possui categoria"""
        return self.categoria is not None and self.categoria != ""
    
    def descricao_contem(self, texto: str) -> bool:
        """Verifica se a descrição contém o texto (case-insensitive)"""
        return texto.lower() in self.descricao.lower()
    
    def descricao_igual(self, texto: str) -> bool:
        """Verifica se a descrição é exatamente igual ao texto (case-insensitive)"""
        return self.descricao.lower() == texto.lower()
