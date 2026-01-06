"""
Implementação concreta do repositório de Transações usando SQLModel
"""
from datetime import date
from typing import List, Optional

from sqlmodel import Session, select, or_, func

from app.domain.entities.transacao import Transacao
from app.domain.value_objects.tipo_transacao import TipoTransacao
from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.infrastructure.database.models.transacao_model import TransacaoModel
from app.infrastructure.database.models.tag_model import TransacaoTagModel


class TransacaoRepository(ITransacaoRepository):
    """
    Implementação concreta de ITransacaoRepository usando SQLModel.
    
    Responsabilidades:
    - Traduzir entidades de domínio ↔ models SQLModel
    - Executar operações de persistência
    - Isolar SQLModel da camada de domínio
    
    Princípios SOLID:
    - LSP: Substituível por ITransacaoRepository
    - DIP: Implementa abstração do domínio
    """
    
    def __init__(self, session: Session):
        self._session = session
    
    def criar(self, transacao: Transacao) -> Transacao:
        """Cria uma nova transação"""
        # Converte entidade de domínio → model SQLModel
        model = self._to_model(transacao)
        
        # Persiste
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        
        # Converte model SQLModel → entidade de domínio
        return self._to_entity(model)
    
    def buscar_por_id(self, id: int) -> Optional[Transacao]:
        """Busca transação por ID"""
        model = self._session.get(TransacaoModel, id)
        if not model:
            return None
        return self._to_entity(model)
    
    def listar(
        self,
        mes: Optional[int] = None,
        ano: Optional[int] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        categoria: Optional[str] = None,
        tipo: Optional[TipoTransacao] = None,
        tag_ids: Optional[List[int]] = None,
        criterio_data: str = "data_transacao"
    ) -> List[Transacao]:
        """Lista transações com filtros"""
        query = select(TransacaoModel)
        
        # Filtro de período
        if data_inicio and data_fim:
            query = self._aplicar_filtro_data(query, data_inicio, data_fim, criterio_data)
        elif mes and ano:
            data_inicio_calc = date(ano, mes, 1)
            if mes < 12:
                data_fim_calc = date(ano, mes + 1, 1)
            else:
                data_fim_calc = date(ano + 1, 1, 1)
            query = self._aplicar_filtro_data(query, data_inicio_calc, data_fim_calc, criterio_data)
        
        # Filtro de categoria
        if categoria:
            query = query.where(TransacaoModel.categoria == categoria)
        
        # Filtro de tipo
        if tipo:
            query = query.where(TransacaoModel.tipo == tipo.name)  # UPPERCASE
        
        # Filtro de tags (OR)
        if tag_ids:
            query = query.join(TransacaoTagModel).where(
                TransacaoTagModel.tag_id.in_(tag_ids)
            ).distinct()
        
        # Ordena por data DESC
        query = query.order_by(TransacaoModel.data.desc())
        
        models = self._session.exec(query).all()
        return [self._to_entity(m) for m in models]
    
    def atualizar(self, transacao: Transacao) -> Transacao:
        """Atualiza transação existente"""
        if not transacao.id:
            raise ValueError("Transacao deve ter ID para atualizar")
        
        model = self._session.get(TransacaoModel, transacao.id)
        if not model:
            raise ValueError(f"Transacao {transacao.id} não encontrada")
        
        # Atualiza campos
        model.data = transacao.data
        model.descricao = transacao.descricao
        model.valor = transacao.valor
        model.valor_original = transacao.valor_original
        model.tipo = transacao.tipo.name  # UPPERCASE para ENUM PostgreSQL
        model.categoria = transacao.categoria
        model.origem = transacao.origem
        model.observacoes = transacao.observacoes
        model.data_fatura = transacao.data_fatura
        model.atualizado_em = transacao.atualizado_em
        
        # Atualiza tags (remove antigas e adiciona novas)
        # Remove tags existentes
        stmt = select(TransacaoTagModel).where(TransacaoTagModel.transacao_id == transacao.id)
        existing_tags = self._session.exec(stmt).all()
        for tag_rel in existing_tags:
            self._session.delete(tag_rel)
        
        # Adiciona novas tags
        for tag_id in transacao.tag_ids:
            tag_rel = TransacaoTagModel(transacao_id=transacao.id, tag_id=tag_id)
            self._session.add(tag_rel)
        
        self._session.commit()
        self._session.refresh(model)
        
        return self._to_entity(model)
    
    def deletar(self, id: int) -> bool:
        """Deleta transação"""
        model = self._session.get(TransacaoModel, id)
        if not model:
            return False
        
        self._session.delete(model)
        self._session.commit()
        return True
    
    def listar_por_ids(self, ids: List[int]) -> List[Transacao]:
        """Lista transações por IDs"""
        query = select(TransacaoModel).where(TransacaoModel.id.in_(ids))
        models = self._session.exec(query).all()
        return [self._to_entity(m) for m in models]
    
    def contar(
        self,
        mes: Optional[int] = None,
        ano: Optional[int] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        criterio_data: str = "data_transacao"
    ) -> int:
        """Conta transações com filtros"""
        query = select(func.count(TransacaoModel.id))
        
        if data_inicio and data_fim:
            query = self._aplicar_filtro_data_count(query, data_inicio, data_fim, criterio_data)
        elif mes and ano:
            data_inicio_calc = date(ano, mes, 1)
            if mes < 12:
                data_fim_calc = date(ano, mes + 1, 1)
            else:
                data_fim_calc = date(ano + 1, 1, 1)
            query = self._aplicar_filtro_data_count(query, data_inicio_calc, data_fim_calc, criterio_data)
        
        return self._session.exec(query).one()
    
    def _aplicar_filtro_data(self, query, data_inicio: date, data_fim: date, criterio: str):
        """Aplica filtro de data na query"""
        if criterio == "data_fatura":
            return query.where(
                or_(
                    (TransacaoModel.data_fatura >= data_inicio) & (TransacaoModel.data_fatura <= data_fim),
                    (TransacaoModel.data_fatura.is_(None)) & (TransacaoModel.data >= data_inicio) & (TransacaoModel.data <= data_fim)
                )
            )
        else:
            return query.where(
                TransacaoModel.data >= data_inicio,
                TransacaoModel.data <= data_fim
            )
    
    def _aplicar_filtro_data_count(self, query, data_inicio: date, data_fim: date, criterio: str):
        """Aplica filtro de data na query de contagem"""
        if criterio == "data_fatura":
            return query.where(
                or_(
                    (TransacaoModel.data_fatura >= data_inicio) & (TransacaoModel.data_fatura <= data_fim),
                    (TransacaoModel.data_fatura.is_(None)) & (TransacaoModel.data >= data_inicio) & (TransacaoModel.data <= data_fim)
                )
            )
        else:
            return query.where(
                TransacaoModel.data >= data_inicio,
                TransacaoModel.data <= data_fim
            )
    
    def listar_categorias(self) -> List[str]:
        """Lista todas as categorias únicas"""
        query = select(TransacaoModel.categoria).distinct()
        categorias = self._session.exec(query).all()
        return list(categorias)
    
    def restaurar_valor_original(self, id: int) -> Transacao:
        """Restaura o valor original de uma transação"""
        model = self._session.get(TransacaoModel, id)
        if not model:
            return None
        
        # Restaurar valor
        model.valor = model.valor_original
        from datetime import datetime
        model.atualizado_em = datetime.now()
        
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        
        return self._to_entity(model)
    
    def adicionar_tag(self, transacao_id: int, tag_id: int) -> None:
        """Adiciona uma tag a uma transação (evita duplicatas)"""
        # Verifica se já existe a associação
        existing = self._session.exec(
            select(TransacaoTagModel).where(
                TransacaoTagModel.transacao_id == transacao_id,
                TransacaoTagModel.tag_id == tag_id
            )
        ).first()
        
        if existing:
            return  # Já existe, não precisa adicionar
        
        # Cria a associação
        associacao = TransacaoTagModel(transacao_id=transacao_id, tag_id=tag_id)
        self._session.add(associacao)
        
        # Atualiza timestamp da transação
        transacao = self._session.get(TransacaoModel, transacao_id)
        if transacao:
            from datetime import datetime
            transacao.atualizado_em = datetime.now()
            self._session.add(transacao)
        
        self._session.commit()
    
    def remover_tag(self, transacao_id: int, tag_id: int) -> None:
        """Remove uma tag de uma transação"""
        # Busca a associação
        associacao = self._session.exec(
            select(TransacaoTagModel).where(
                TransacaoTagModel.transacao_id == transacao_id,
                TransacaoTagModel.tag_id == tag_id
            )
        ).first()
        
        if not associacao:
            return  # Não existe, nada a fazer
        
        # Remove a associação
        self._session.delete(associacao)
        
        # Atualiza timestamp da transação
        transacao = self._session.get(TransacaoModel, transacao_id)
        if transacao:
            from datetime import datetime
            transacao.atualizado_em = datetime.now()
            self._session.add(transacao)
        
        self._session.commit()
    
    def _to_entity(self, model: TransacaoModel) -> Transacao:
        """Converte SQLModel → Entidade de Domínio"""
        # Busca IDs de tags
        tag_ids = [t.tag_id for t in model.tags] if model.tags else []
        
        return Transacao(
            id=model.id,
            data=model.data,
            descricao=model.descricao,
            valor=model.valor,
            valor_original=model.valor_original,
            tipo=TipoTransacao[model.tipo],  # Converter UPPERCASE para enum
            categoria=model.categoria,
            origem=model.origem,
            observacoes=model.observacoes,
            data_fatura=model.data_fatura,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
            tag_ids=tag_ids
        )
    
    def _to_model(self, entity: Transacao) -> TransacaoModel:
        """Converte Entidade de Domínio → SQLModel"""
        return TransacaoModel(
            id=entity.id,
            data=entity.data,
            descricao=entity.descricao,
            valor=entity.valor,
            valor_original=entity.valor_original,
            tipo=entity.tipo.name,  # UPPERCASE para ENUM PostgreSQL
            categoria=entity.categoria,
            origem=entity.origem,
            observacoes=entity.observacoes,
            data_fatura=entity.data_fatura,
            criado_em=entity.criado_em,
            atualizado_em=entity.atualizado_em
        )
