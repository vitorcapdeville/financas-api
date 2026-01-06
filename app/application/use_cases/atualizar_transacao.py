"""
Caso de uso: Atualizar Transação
"""
from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.application.dto.transacao_dto import AtualizarTransacaoDTO, TransacaoDTO
from app.application.exceptions.application_exceptions import EntityNotFoundException


class AtualizarTransacaoUseCase:
    """
    Caso de uso para atualizar uma transação existente.
    
    Responsabilidades:
    - Validar que a transação existe
    - Aplicar atualizações parciais (apenas campos fornecidos)
    - Retornar transação atualizada
    """
    
    def __init__(self, transacao_repository: ITransacaoRepository):
        self._transacao_repository = transacao_repository
    
    def execute(self, transacao_id: int, dto: AtualizarTransacaoDTO) -> TransacaoDTO:
        """
        Executa o caso de uso de atualização de transação.
        
        Args:
            transacao_id: ID da transação a atualizar
            dto: DTO com campos a atualizar (parcial)
            
        Returns:
            TransacaoDTO com dados atualizados
            
        Raises:
            EntityNotFoundException: Se transação não existir
        """
        # Buscar transação
        transacao = self._transacao_repository.buscar_por_id(transacao_id)
        if not transacao:
            raise EntityNotFoundException("Transacao", transacao_id)
        
        # Aplicar atualizações parciais
        if dto.descricao is not None:
            transacao.descricao = dto.descricao
        if dto.valor is not None:
            transacao.valor = dto.valor
        if dto.categoria is not None:
            transacao.categoria = dto.categoria
        if dto.observacoes is not None:
            transacao.observacoes = dto.observacoes
        if dto.data_fatura is not None:
            transacao.data_fatura = dto.data_fatura
        
        # Atualizar transação no repositório
        transacao_atualizada = self._transacao_repository.atualizar(transacao)
        
        # Converter para DTO de retorno
        return self._to_dto(transacao_atualizada)
    
    def _to_dto(self, transacao) -> TransacaoDTO:
        """Converte entidade para DTO"""
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
