"""
Caso de Uso: Listar Transações
Orquestra a lógica de listagem de transações com filtros
"""
from typing import List

from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.domain.repositories.configuracao_repository import IConfiguracaoRepository
from app.application.dto.transacao_dto import FiltrosTransacaoDTO, TransacaoDTO
from app.domain.entities.transacao import Transacao


class ListarTransacoesUseCase:
    """
    Caso de uso para listar transações com filtros.
    
    Princípio SRP: Responsabilidade única - listar transações
    Princípio DIP: Depende de abstrações (repositórios)
    """
    
    def __init__(
        self,
        transacao_repository: ITransacaoRepository,
        configuracao_repository: IConfiguracaoRepository
    ):
        self._transacao_repository = transacao_repository
        self._configuracao_repository = configuracao_repository
    
    def execute(self, filtros: FiltrosTransacaoDTO) -> List[TransacaoDTO]:
        """
        Executa o caso de uso de listar transações.
        
        Args:
            filtros: Filtros de busca
            
        Returns:
            Lista de DTOs de transações
        """
        # Obtém critério de data da configuração
        criterio = filtros.criterio_data
        if not criterio or criterio not in ["data_transacao", "data_fatura"]:
            criterio_config = self._configuracao_repository.obter("criterio_data_transacao")
            criterio = criterio_config if criterio_config else "data_transacao"
        
        # Busca transações no repositório
        transacoes = self._transacao_repository.listar(
            mes=filtros.mes,
            ano=filtros.ano,
            data_inicio=filtros.data_inicio,
            data_fim=filtros.data_fim,
            categoria=filtros.categoria,
            tipo=filtros.tipo,
            tag_ids=filtros.tag_ids,
            criterio_data=criterio
        )
        
        # Converte para DTOs
        return [self._to_dto(t) for t in transacoes]
    
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
