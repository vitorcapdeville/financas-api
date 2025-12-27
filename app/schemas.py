"""
Schemas compostos que combinam modelos de diferentes arquivos
"""
from typing import List
from app.models import TransacaoRead as TransacaoReadBase
from app.models_tags import TagRead


class TransacaoReadWithTags(TransacaoReadBase):
    """Schema de leitura de transação incluindo tags associadas"""
    tags: List[TagRead] = []
