"""
Factories para criação de objetos de teste usando FactoryBoy.

Factories fornecem uma forma flexível e reutilizável de criar dados de teste
com valores padrão realistas que podem ser sobrescritos quando necessário.
"""

from datetime import datetime, date, timedelta
import random

import factory
from factory import Faker, LazyAttribute, SubFactory, post_generation
from sqlmodel import Session

from app.models import Transacao, TipoTransacao
from app.models_config import Configuracao
from app.models_tags import Tag, TransacaoTag
from app.models_regra import Regra, RegraTag, TipoAcao, CriterioTipo


class BaseFactory(factory.Factory):
    """Factory base com configuração comum."""
    class Meta:
        abstract = True


class TransacaoFactory(BaseFactory):
    """
    Factory para criar transações de teste.
    
    Exemplos:
        # Transação com valores padrão
        transacao = TransacaoFactory.create(session=session)
        
        # Transação customizada
        transacao = TransacaoFactory.create(
            session=session,
            descricao="Pizza",
            valor=45.90,
            tipo=TipoTransacao.SAIDA
        )
    """
    class Meta:
        model = Transacao
    
    data = LazyAttribute(lambda _: (datetime.now() - timedelta(days=random.randint(0, 90))).date())
    descricao = Faker('sentence', nb_words=4, locale='pt_BR')
    valor = LazyAttribute(lambda _: round(random.uniform(10.0, 500.0), 2))
    tipo = TipoTransacao.SAIDA
    categoria = Faker('random_element', elements=[
        'Alimentação', 'Transporte', 'Moradia', 'Saúde', 
        'Educação', 'Lazer', 'Vestuário', 'Outros'
    ])
    origem = "manual"
    observacoes = None
    data_fatura = None
    valor_original = None
    
    @classmethod
    def create(cls, session: Session = None, **kwargs):
        """Cria e persiste transação no banco."""
        obj = cls.build(**kwargs)
        if session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
        return obj
    
    @classmethod
    def create_batch(cls, size: int, session: Session = None, **kwargs):
        """Cria múltiplas transações."""
        objs = [cls.build(**kwargs) for _ in range(size)]
        if session:
            for obj in objs:
                session.add(obj)
            session.commit()
            for obj in objs:
                session.refresh(obj)
        return objs


class TransacaoEntradaFactory(TransacaoFactory):
    """Factory para criar transações de entrada (receitas)."""
    tipo = TipoTransacao.ENTRADA
    categoria = Faker('random_element', elements=[
        'Salário', 'Freelance', 'Investimentos', 'Outros'
    ])
    valor = LazyAttribute(lambda _: round(random.uniform(1000.0, 5000.0), 2))


class TransacaoSaidaFactory(TransacaoFactory):
    """Factory para criar transações de saída (despesas)."""
    tipo = TipoTransacao.SAIDA


class TransacaoCartaoFactory(TransacaoFactory):
    """Factory para transações de cartão de crédito."""
    origem = "fatura_cartao"
    tipo = TipoTransacao.SAIDA
    data_fatura = LazyAttribute(lambda obj: obj.data + timedelta(days=30))


class TagFactory(BaseFactory):
    """
    Factory para criar tags de teste.
    
    Exemplos:
        tag = TagFactory.create(session=session)
        tag = TagFactory.create(session=session, nome="Urgente", cor="#FF0000")
    """
    class Meta:
        model = Tag
    
    nome = Faker('word', locale='pt_BR')
    cor = Faker('random_element', elements=[
        '#FF5733', '#33FF57', '#3357FF', '#F333FF', 
        '#33FFF3', '#FFC733', '#FF3333', '#33FF33'
    ])
    descricao = Faker('sentence', nb_words=6, locale='pt_BR')
    
    @classmethod
    def create(cls, session: Session = None, **kwargs):
        """Cria e persiste tag no banco."""
        obj = cls.build(**kwargs)
        if session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
        return obj
    
    @classmethod
    def create_batch(cls, size: int, session: Session = None, **kwargs):
        """Cria múltiplas tags."""
        objs = []
        for i in range(size):
            # Garante nomes únicos
            unique_kwargs = {**kwargs, 'nome': f"{kwargs.get('nome', 'Tag')}_{i}"}
            objs.append(cls.build(**unique_kwargs))
        
        if session:
            for obj in objs:
                session.add(obj)
            session.commit()
            for obj in objs:
                session.refresh(obj)
        return objs


class RegraFactory(BaseFactory):
    """
    Factory para criar regras de teste.
    
    Exemplos:
        regra = RegraFactory.create(session=session)
        regra = RegraFactory.create(
            session=session,
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte"
        )
    """
    class Meta:
        model = Regra
    
    nome = Faker('sentence', nb_words=3, locale='pt_BR')
    tipo_acao = TipoAcao.ALTERAR_CATEGORIA
    criterio_tipo = CriterioTipo.DESCRICAO_CONTEM
    criterio_valor = Faker('word', locale='pt_BR')
    acao_valor = "Categoria Padrão"
    prioridade = 1
    ativo = True
    
    @classmethod
    def create(cls, session: Session = None, **kwargs):
        """Cria e persiste regra no banco."""
        obj = cls.build(**kwargs)
        if session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
        return obj


class RegraAlterarCategoriaFactory(RegraFactory):
    """Factory para regras de alterar categoria."""
    tipo_acao = TipoAcao.ALTERAR_CATEGORIA
    acao_valor = Faker('random_element', elements=[
        'Alimentação', 'Transporte', 'Moradia', 'Lazer'
    ])


class RegraAlterarValorFactory(RegraFactory):
    """Factory para regras de alterar valor (desconto/taxa)."""
    tipo_acao = TipoAcao.ALTERAR_VALOR
    acao_valor = "10"  # 10% de desconto por padrão


class ConfiguracaoFactory(BaseFactory):
    """
    Factory para criar configurações de teste.
    
    Exemplos:
        config = ConfiguracaoFactory.create(
            session=session,
            chave="diaInicioPeriodo",
            valor="15"
        )
    """
    class Meta:
        model = Configuracao
    
    chave = Faker('word', locale='pt_BR')
    valor = Faker('word', locale='pt_BR')
    
    @classmethod
    def create(cls, session: Session = None, **kwargs):
        """Cria e persiste configuração no banco."""
        obj = cls.build(**kwargs)
        if session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
        return obj
