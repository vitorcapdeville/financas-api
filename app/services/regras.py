"""
Serviço de aplicação de regras automáticas em transações.

Este módulo contém a lógica de negócio para:
- Verificar se uma transação corresponde aos critérios de uma regra
- Aplicar uma regra a uma transação
- Aplicar todas as regras ativas a uma transação (ordenadas por prioridade)
- Calcular prioridade para novas regras
"""

import json
from datetime import datetime
from typing import Optional, List

from sqlmodel import Session, select, func

from app.models import Transacao
from app.models_regra import Regra, RegraTag, TipoAcao, CriterioTipo
from app.models_tags import Tag, TransacaoTag


def verificar_transacao_match_criterio(transacao: Transacao, regra: Regra) -> bool:
    """
    Verifica se uma transação corresponde aos critérios de uma regra.
    
    Args:
        transacao: Transação a verificar
        regra: Regra com os critérios
        
    Returns:
        True se a transação corresponde aos critérios, False caso contrário
    """
    if regra.criterio_tipo == CriterioTipo.DESCRICAO_EXATA:
        return transacao.descricao.lower() == regra.criterio_valor.lower()
    
    elif regra.criterio_tipo == CriterioTipo.DESCRICAO_CONTEM:
        return regra.criterio_valor.lower() in transacao.descricao.lower()
    
    elif regra.criterio_tipo == CriterioTipo.CATEGORIA:
        if not transacao.categoria:
            return False
        return transacao.categoria.lower() == regra.criterio_valor.lower()
    
    return False


def aplicar_regra_em_transacao(
    regra: Regra,
    transacao: Transacao,
    session: Session
) -> bool:
    """
    Aplica uma regra a uma transação.
    
    Args:
        regra: Regra a aplicar
        transacao: Transação a modificar
        session: Sessão de banco de dados
        
    Returns:
        True se a regra foi aplicada, False caso contrário
    """
    # Verifica se a transação corresponde aos critérios
    if not verificar_transacao_match_criterio(transacao, regra):
        return False
    
    # Aplica a ação da regra
    if regra.tipo_acao == TipoAcao.ALTERAR_CATEGORIA:
        transacao.categoria = regra.acao_valor
        transacao.atualizado_em = datetime.now()
        
    elif regra.tipo_acao == TipoAcao.ADICIONAR_TAGS:
        # Parse dos IDs de tags do JSON
        try:
            tag_ids = json.loads(regra.acao_valor)
            if not isinstance(tag_ids, list):
                return False
                
            # Busca as tags existentes da transação
            stmt_existing = select(TransacaoTag).where(
                TransacaoTag.transacao_id == transacao.id
            )
            existing_tags = session.exec(stmt_existing).all()
            existing_tag_ids = {tt.tag_id for tt in existing_tags}
            
            # Adiciona apenas tags que ainda não existem
            for tag_id in tag_ids:
                if tag_id not in existing_tag_ids:
                    # Verifica se a tag existe
                    tag = session.get(Tag, tag_id)
                    if tag:
                        transacao_tag = TransacaoTag(
                            transacao_id=transacao.id,
                            tag_id=tag_id
                        )
                        session.add(transacao_tag)
                        
        except (json.JSONDecodeError, TypeError, ValueError):
            return False
            
    elif regra.tipo_acao == TipoAcao.ALTERAR_VALOR:
        # Percentual do valor original
        try:
            percentual = float(regra.acao_valor)
            if not (0 <= percentual <= 100):
                return False
                
            # Usa valor_original como base, ou valor se valor_original não existe
            base_valor = transacao.valor_original if transacao.valor_original is not None else transacao.valor
            
            # Define valor_original se ainda não foi definido
            if transacao.valor_original is None:
                transacao.valor_original = transacao.valor
                
            # Calcula novo valor
            transacao.valor = base_valor * (percentual / 100.0)
            transacao.atualizado_em = datetime.now()
            
        except (ValueError, TypeError):
            return False
    
    return True


def aplicar_todas_regras_ativas(
    transacao: Transacao,
    session: Session
) -> int:
    """
    Aplica todas as regras ativas a uma transação.
    
    Regras são aplicadas em ordem de prioridade (maior primeiro).
    Cada regra é aplicada no máximo uma vez por transação.
    
    Args:
        transacao: Transação a modificar
        session: Sessão de banco de dados
        
    Returns:
        Número de regras aplicadas
    """
    # Busca todas as regras ativas ordenadas por prioridade DESC
    stmt = select(Regra).where(Regra.ativo).order_by(Regra.prioridade.desc())
    regras = session.exec(stmt).all()
    
    regras_aplicadas = 0
    
    for regra in regras:
        if aplicar_regra_em_transacao(regra, transacao, session):
            regras_aplicadas += 1
    
    # Commit será feito pelo chamador
    return regras_aplicadas


def calcular_proxima_prioridade(session: Session) -> int:
    """
    Calcula a próxima prioridade para uma nova regra.
    
    Retorna max(prioridade) + 1, ou 1 se não houver regras.
    
    Args:
        session: Sessão de banco de dados
        
    Returns:
        Próxima prioridade disponível
    """
    stmt = select(func.max(Regra.prioridade))
    max_prioridade = session.exec(stmt).first()
    
    if max_prioridade is None:
        return 1
    
    return max_prioridade + 1


def aplicar_regra_em_todas_transacoes(
    regra_id: int,
    session: Session
) -> int:
    """
    Aplica uma regra específica em todas as transações existentes que correspondem.
    
    Args:
        regra_id: ID da regra a aplicar
        session: Sessão de banco de dados
        
    Returns:
        Número de transações modificadas
    """
    # Busca a regra
    regra = session.get(Regra, regra_id)
    if not regra:
        return 0
    
    # Busca todas as transações
    stmt = select(Transacao)
    transacoes = session.exec(stmt).all()
    
    transacoes_modificadas = 0
    
    for transacao in transacoes:
        if aplicar_regra_em_transacao(regra, transacao, session):
            transacoes_modificadas += 1
    
    session.commit()
    
    return transacoes_modificadas


def aplicar_todas_regras_em_todas_transacoes(session: Session) -> int:
    """
    Aplica todas as regras ativas em todas as transações existentes.
    
    Args:
        session: Sessão de banco de dados
        
    Returns:
        Número total de aplicações (soma de todas as regras × transações afetadas)
    """
    # Busca todas as transações
    stmt = select(Transacao)
    transacoes = session.exec(stmt).all()
    
    total_aplicacoes = 0
    
    for transacao in transacoes:
        aplicacoes = aplicar_todas_regras_ativas(transacao, session)
        total_aplicacoes += aplicacoes
    
    session.commit()
    
    return total_aplicacoes
