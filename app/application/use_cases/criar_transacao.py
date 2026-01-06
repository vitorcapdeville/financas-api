"""
Caso de Uso: Criar Transação
Orquestra a lógica de criação de uma nova transação
"""
from app.domain.entities.transacao import Transacao
from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.application.dto.transacao_dto import CriarTransacaoDTO, TransacaoDTO
from app.application.exceptions.application_exceptions import ValidationException


class CriarTransacaoUseCase:
    """
    Caso de uso para criar uma nova transação.
    
    Princípio SRP: Responsabilidade única - criar transações
    Princípio DIP: Depende de abstração (ITransacaoRepository), não de implementação
    """
    
    def __init__(self, transacao_repository: ITransacaoRepository):
        self._transacao_repository = transacao_repository
    
    def execute(self, dto: CriarTransacaoDTO) -> TransacaoDTO:
        """
        Executa o caso de uso de criar transação.
        
        Args:
            dto: Dados para criação
            
        Returns:
            DTO com transação criada
            
        Raises:
            ValidationException: Se dados inválidos
        """
        # Validações de negócio
        if dto.valor < 0:
            raise ValidationException("Valor deve ser positivo")
        
        if not dto.descricao or dto.descricao.strip() == "":
            raise ValidationException("Descrição é obrigatória")
        
        # Cria entidade de domínio
        transacao = Transacao(
            data=dto.data,
            descricao=dto.descricao,
            valor=dto.valor,
            tipo=dto.tipo,
            categoria=dto.categoria,
            origem=dto.origem,
            observacoes=dto.observacoes,
            data_fatura=dto.data_fatura
        )
        
        # Persiste via repositório
        transacao_criada = self._transacao_repository.criar(transacao)
        
        # Retorna DTO
        return self._to_dto(transacao_criada)
    
    def _to_dto(self, transacao: Transacao) -> TransacaoDTO:
        """Converte entidade de domínio para DTO"""
        return TransacaoDTO(
            id=transacao.id,
            data=transacao.data,
            descricao=transacao.descricao,
            valor=transacao.valor,
            valor_original=transacao.valor_original,
            tipo=transacao.tipo,
            categoria=transacao.categoria,
            origem=transacao.origem,
            observacoes=transacao.observacoes,
            data_fatura=transacao.data_fatura,
            criado_em=transacao.criado_em,
            atualizado_em=transacao.atualizado_em,
            tag_ids=transacao.tag_ids
        )
