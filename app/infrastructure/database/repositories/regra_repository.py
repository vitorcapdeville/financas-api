"""
Implementação concreta do repositório de Regras usando SQLModel
"""
from typing import List, Optional
import json

from sqlmodel import Session, select, func

from app.domain.entities.regra import Regra
from app.domain.repositories.regra_repository import IRegraRepository
from app.domain.value_objects.regra_enums import TipoAcao, CriterioTipo
from app.infrastructure.database.models.regra_model import RegraModel, RegraTagModel


class RegraRepository(IRegraRepository):
    """
    Implementação concreta de IRegraRepository usando SQLModel.
    
    Responsabilidades:
    - Traduzir entidades de domínio ↔ models SQLModel
    - Gerenciar associações com tags (RegraTagModel)
    - Garantir unicidade de nome e prioridade
    - Isolar SQLModel da camada de domínio
    """
    
    def __init__(self, session: Session):
        self._session = session
    
    def criar(self, regra: Regra) -> Regra:
        """Cria uma nova regra"""
        # Verifica duplicidade de nome
        if self._nome_existe(regra.nome):
            raise ValueError(f"Regra com nome '{regra.nome}' já existe")
        
        # Se não tem prioridade, calcula
        if regra.prioridade == 0:
            regra.prioridade = self.obter_proxima_prioridade()
        
        model = self._to_model(regra)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        
        # Associa tags se tipo_acao for ADICIONAR_TAGS
        if regra.tipo_acao == TipoAcao.ADICIONAR_TAGS and regra.tag_ids:
            self._sincronizar_tags(model.id, regra.tag_ids)
        
        return self._to_entity(model)
    
    def buscar_por_id(self, id: int) -> Optional[Regra]:
        """Busca regra por ID"""
        model = self._session.get(RegraModel, id)
        if not model:
            return None
        return self._to_entity(model)
    
    def buscar_por_nome(self, nome: str) -> Optional[Regra]:
        """Busca regra por nome (case-insensitive)"""
        query = select(RegraModel).where(func.lower(RegraModel.nome) == nome.lower())
        model = self._session.exec(query).first()
        if not model:
            return None
        return self._to_entity(model)
    
    def listar(self, apenas_ativas: bool = False) -> List[Regra]:
        """
        Lista regras ordenadas por prioridade (maior primeiro).
        
        Args:
            apenas_ativas: Se True, retorna apenas regras ativas
        """
        query = select(RegraModel).order_by(RegraModel.prioridade.desc())
        
        if apenas_ativas:
            query = query.where(RegraModel.ativo == True)
        
        models = self._session.exec(query).all()
        return [self._to_entity(m) for m in models]
    
    def atualizar(self, regra: Regra) -> Regra:
        """Atualiza regra existente"""
        if not regra.id:
            raise ValueError("Regra deve ter ID para atualizar")
        
        model = self._session.get(RegraModel, regra.id)
        if not model:
            raise ValueError(f"Regra {regra.id} não encontrada")
        
        # Verifica duplicidade de nome (excluindo o próprio ID)
        if regra.nome != model.nome and self._nome_existe(regra.nome, excluir_id=regra.id):
            raise ValueError(f"Regra com nome '{regra.nome}' já existe")
        
        # Verifica duplicidade de prioridade (excluindo o próprio ID)
        if regra.prioridade != model.prioridade and self._prioridade_existe(regra.prioridade, excluir_id=regra.id):
            raise ValueError(f"Prioridade {regra.prioridade} já está em uso")
        
        # Atualiza campos
        model.nome = regra.nome
        model.tipo_acao = regra.tipo_acao.name  # UPPERCASE para ENUM PostgreSQL
        model.criterio_tipo = regra.criterio_tipo.name  # UPPERCASE para ENUM PostgreSQL
        model.criterio_valor = regra.criterio_valor
        model.acao_valor = regra.acao_valor
        model.prioridade = regra.prioridade
        model.ativo = regra.ativo
        model.atualizado_em = regra.atualizado_em
        
        self._session.commit()
        
        # Sincroniza tags se tipo_acao for ADICIONAR_TAGS
        if regra.tipo_acao == TipoAcao.ADICIONAR_TAGS:
            self._sincronizar_tags(model.id, regra.tag_ids)
        
        self._session.refresh(model)
        
        return self._to_entity(model)
    
    def deletar(self, id: int) -> bool:
        """Deleta regra (cascade deleta associações com tags)"""
        model = self._session.get(RegraModel, id)
        if not model:
            return False
        
        self._session.delete(model)
        self._session.commit()
        return True
    
    def obter_proxima_prioridade(self) -> int:
        """Calcula a próxima prioridade (max atual + 1)"""
        query = select(func.max(RegraModel.prioridade))
        max_prioridade = self._session.exec(query).one()
        return (max_prioridade or 0) + 1
    
    def reordenar(self, nova_ordem: List[int]) -> bool:
        """
        Reordena regras baseado em lista de IDs.
        
        Args:
            nova_ordem: Lista de IDs na ordem desejada (índice 0 = maior prioridade)
        """
        # Valida que todos os IDs existem
        for regra_id in nova_ordem:
            if not self._session.get(RegraModel, regra_id):
                raise ValueError(f"Regra {regra_id} não encontrada")
        
        # Primeiro, define todas as prioridades como negativas temporariamente
        # para evitar conflitos de UNIQUE constraint
        for regra_id in nova_ordem:
            model = self._session.get(RegraModel, regra_id)
            if model:
                model.prioridade = -regra_id  # Prioridade temporária negativa
        
        self._session.flush()  # Commit das prioridades temporárias
        
        # Agora atualiza com as prioridades finais
        max_prioridade = len(nova_ordem)
        for idx, regra_id in enumerate(nova_ordem):
            model = self._session.get(RegraModel, regra_id)
            if model:
                # Prioridade decrescente: primeiro item = maior prioridade
                model.prioridade = max_prioridade - idx
        
        self._session.commit()
        return True
    
    def _sincronizar_tags(self, regra_id: int, tag_ids: List[int]):
        """
        Sincroniza tags associadas a uma regra.
        Remove associações antigas e adiciona novas.
        """
        # Remove associações antigas
        query = select(RegraTagModel).where(RegraTagModel.regra_id == regra_id)
        associacoes_antigas = self._session.exec(query).all()
        for assoc in associacoes_antigas:
            self._session.delete(assoc)
        
        # Adiciona novas associações
        for tag_id in tag_ids:
            nova_assoc = RegraTagModel(regra_id=regra_id, tag_id=tag_id)
            self._session.add(nova_assoc)
        
        self._session.commit()
    
    def _nome_existe(self, nome: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica se nome já existe (case-insensitive)"""
        query = select(func.count(RegraModel.id)).where(
            func.lower(RegraModel.nome) == nome.lower()
        )
        
        if excluir_id:
            query = query.where(RegraModel.id != excluir_id)
        
        count = self._session.exec(query).one()
        return count > 0
    
    def _prioridade_existe(self, prioridade: int, excluir_id: Optional[int] = None) -> bool:
        """Verifica se prioridade já existe"""
        query = select(func.count(RegraModel.id)).where(
            RegraModel.prioridade == prioridade
        )
        
        if excluir_id:
            query = query.where(RegraModel.id != excluir_id)
        
        count = self._session.exec(query).one()
        return count > 0
    
    def _to_entity(self, model: RegraModel) -> Regra:
        """Converte SQLModel → Entidade de Domínio"""
        # Carrega tag_ids se tipo_acao for ADICIONAR_TAGS
        tag_ids = []
        if model.tipo_acao == TipoAcao.ADICIONAR_TAGS.name:  # Comparar com UPPERCASE
            query = select(RegraTagModel.tag_id).where(RegraTagModel.regra_id == model.id)
            tag_ids = list(self._session.exec(query).all())
        
        return Regra(
            id=model.id,
            nome=model.nome,
            tipo_acao=TipoAcao[model.tipo_acao],  # Converter UPPERCASE para enum
            criterio_tipo=CriterioTipo[model.criterio_tipo],  # Converter UPPERCASE para enum
            criterio_valor=model.criterio_valor,
            acao_valor=model.acao_valor,
            prioridade=model.prioridade,
            ativo=model.ativo,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
            tag_ids=tag_ids
        )
    
    def _to_model(self, entity: Regra) -> RegraModel:
        """Converte Entidade de Domínio → SQLModel"""
        return RegraModel(
            id=entity.id,
            nome=entity.nome,
            tipo_acao=entity.tipo_acao.name,  # UPPERCASE para ENUM PostgreSQL
            criterio_tipo=entity.criterio_tipo.name,  # UPPERCASE para ENUM PostgreSQL
            criterio_valor=entity.criterio_valor,
            acao_valor=entity.acao_valor,
            prioridade=entity.prioridade,
            ativo=entity.ativo,
            criado_em=entity.criado_em,
            atualizado_em=entity.atualizado_em
        )
