"""
Caso de uso: Obter Resumo Mensal de Transações
"""
from typing import Dict, List, Optional
from datetime import date

from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.domain.repositories.configuracao_repository import IConfiguracaoRepository
from app.application.dto.transacao_dto import ResumoMensalDTO, FiltrosTransacaoDTO


class ObterResumoMensalUseCase:
    """
    Caso de uso para obter resumo mensal de entradas/saídas agrupadas por categoria.
    
    Responsabilidades:
    - Calcular período baseado em mes/ano ou data_inicio/data_fim
    - Aplicar critério de data configurado (data_transacao ou data_fatura)
    - Agrupar transações por categoria e tipo
    - Calcular totais e saldo
    """
    
    def __init__(
        self,
        transacao_repository: ITransacaoRepository,
        configuracao_repository: IConfiguracaoRepository
    ):
        self._transacao_repository = transacao_repository
        self._configuracao_repository = configuracao_repository
    
    def execute(
        self,
        mes: Optional[int] = None,
        ano: Optional[int] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        tag_ids: Optional[List[int]] = None
    ) -> ResumoMensalDTO:
        """
        Executa o caso de uso de resumo mensal.
        
        Args:
            mes: Mês (1-12)
            ano: Ano (ex: 2024)
            data_inicio: Data de início (prioridade sobre mes/ano)
            data_fim: Data de fim (prioridade sobre mes/ano)
            tag_ids: IDs de tags para filtrar
            
        Returns:
            ResumoMensalDTO com totais e agrupamentos por categoria
            
        Raises:
            ValidationException: Se nem mes/ano nem data_inicio/data_fim fornecidos
        """
        from app.application.exceptions.application_exceptions import ValidationException
        
        # Validar que ao menos um período foi fornecido
        if not (data_inicio and data_fim) and not (mes and ano):
            raise ValidationException("Forneça mes/ano ou data_inicio/data_fim")
        
        # Obter critério de data configurado
        try:
            config = self._configuracao_repository.obter("criterio_data_transacao")
            criterio = config.valor
        except:
            criterio = "data_transacao"  # Default
        
        # Criar filtros
        filtros = FiltrosTransacaoDTO(
            mes=mes,
            ano=ano,
            data_inicio=data_inicio,
            data_fim=data_fim,
            tag_ids=tag_ids,
            criterio_data=criterio
        )
        
        # Buscar transações
        transacoes = self._transacao_repository.listar(filtros)
        
        # Agrupar por categoria e tipo
        entradas_por_categoria: Dict[str, float] = {}
        saidas_por_categoria: Dict[str, float] = {}
        total_entradas = 0.0
        total_saidas = 0.0
        
        for transacao in transacoes:
            categoria = transacao.categoria or "Sem categoria"
            valor = transacao.valor
            
            if transacao.tipo.value == "entrada":
                entradas_por_categoria[categoria] = entradas_por_categoria.get(categoria, 0.0) + valor
                total_entradas += valor
            else:  # saida
                saidas_por_categoria[categoria] = saidas_por_categoria.get(categoria, 0.0) + valor
                total_saidas += valor
        
        # Criar DTO de resumo
        return ResumoMensalDTO(
            mes=mes,
            ano=ano,
            total_entradas=total_entradas,
            total_saidas=total_saidas,
            saldo=total_entradas - total_saidas,
            entradas_por_categoria=entradas_por_categoria,
            saidas_por_categoria=saidas_por_categoria
        )
