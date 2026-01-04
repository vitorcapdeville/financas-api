# 🔧 Gaps de Implementação Revelados pelos Testes de Regressão

## Visão Geral

8 testes de regressão estão falhando porque documentam **features esperadas mas não implementadas**. Este documento serve como roadmap para implementação futura.

**Status**: 8 gaps identificados  
**Prioridade**: Média (sistema funciona sem essas features)  
**Estimativa Total**: 6-8 horas de desenvolvimento

---

## Gap 1: CASCADE DELETE TransacaoTag

### 📋 Descrição

Ao deletar uma transação, os registros associados na tabela `transacao_tag` deveriam ser deletados automaticamente (CASCADE DELETE), mas atualmente causam erro.

### ❌ Comportamento Atual

```python
session.delete(transacao)
session.commit()

# Resultado: AssertionError
# "Dependency rule on column 'transacao.id' tried to blank-out primary key column 
# 'transacaotag.transacao_id' on instance '<TransacaoTag at 0x...>'"
```

### ✅ Comportamento Esperado

```python
session.delete(transacao)
session.commit()

# Resultado: Transação deletada
# Registros de transacao_tag deletados automaticamente
# Tag original permanece (apenas associação removida)
```

### 🔨 Solução

**Arquivo**: `app/models.py` ou `app/models_tags.py`

```python
# Em Transacao model
class Transacao(SQLModel, table=True):
    # ... outros campos ...
    
    tags: list["Tag"] = Relationship(
        back_populates="transacoes",
        link_model=TransacaoTag,
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}  # ← ADICIONAR
    )
```

**Alternativa (se não funcionar no Relationship)**:

```python
from sqlalchemy import ForeignKey, Column, Integer
from sqlalchemy.orm import relationship

# Em TransacaoTag (se for SQLAlchemy puro)
class TransacaoTag(Base):
    __tablename__ = "transacaotag"
    
    transacao_id = Column(Integer, ForeignKey("transacao.id", ondelete="CASCADE"), ...)
    tag_id = Column(Integer, ForeignKey("tag.id", ondelete="CASCADE"), ...)
```

**Teste Validador**: `tests/regression/test_regressao.py::TestCascadesDeletion::test_deletar_transacao_remove_associacoes_tags`

**Prioridade**: 🔴 **ALTA** (causa erros ao deletar transações)  
**Estimativa**: 30 minutos  
**Complexidade**: Baixa

---

## Gap 2: Importação Fatura com data_fatura

### 📋 Descrição

Ao importar fatura CSV/Excel, o campo `data_fatura` deveria ser aceito como coluna opcional, mas atualmente retorna 422.

### ❌ Comportamento Atual

```python
# CSV com data_fatura
csv_content = "data,descricao,valor,categoria,data_fatura\n"
csv_content += "2025-12-10,Compra Cartão,100.0,Outros,2025-12-25\n"

response = client.post("/importacao/fatura", files={"file": ("fatura.csv", csv_file, "text/csv")})

# Resultado: 422 Unprocessable Entity
```

### ✅ Comportamento Esperado

```python
response = client.post("/importacao/fatura", files={"file": ("fatura.csv", csv_file, "text/csv")})

# Resultado: 200 OK
# Transação criada com data_fatura preenchida
```

### 🔨 Solução

**Arquivo**: `app/routers/importacao.py`

```python
@router.post("/fatura")
async def importar_fatura(file: UploadFile, session: Session = Depends(get_session)):
    # ... código existente ...
    
    # Adicionar data_fatura como coluna opcional
    if 'data_fatura' in df_normalizado.columns:
        df['data_fatura'] = pd.to_datetime(df_normalizado['data_fatura'])
    elif 'mes_fatura' in df_normalizado.columns and 'ano_fatura' in df_normalizado.columns:
        # Lógica existente de mes_fatura/ano_fatura
        ...
    
    for _, row in df.iterrows():
        transacao = Transacao(
            # ... campos existentes ...
            data_fatura=row.get('data_fatura', None)  # ← ADICIONAR
        )
        session.add(transacao)
```

**Teste Validador**: `tests/regression/test_regressao.py::TestCriterioDataTransacao::test_importar_fatura_com_data_transacao_e_fatura`

**Prioridade**: 🟡 **MÉDIA** (workaround: usar mes_fatura/ano_fatura)  
**Estimativa**: 20 minutos  
**Complexidade**: Baixa

---

## Gap 3: Restaurar Valor Original - Limpar Campo

### 📋 Descrição

Após restaurar o valor original de uma transação, o campo `valor_original` deveria ser setado como `None`, mas atualmente mantém o valor antigo.

### ❌ Comportamento Atual

```python
# Transação com valor=50, valor_original=100
response = client.post(f"/transacoes/{id}/restaurar-valor")

# Resultado: {"valor": 100.0, "valor_original": 100.0}  ❌
```

### ✅ Comportamento Esperado

```python
response = client.post(f"/transacoes/{id}/restaurar-valor")

# Resultado: {"valor": 100.0, "valor_original": null}  ✅
```

### 🔨 Solução

**Arquivo**: `app/routers/transacoes.py`

```python
@router.post("/{transacao_id}/restaurar-valor")
def restaurar_valor_original(transacao_id: int, session: Session = Depends(get_session)):
    transacao = session.get(Transacao, transacao_id)
    
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    if transacao.valor_original is None:
        raise HTTPException(status_code=400, detail="Transação não possui valor original")
    
    # Restaurar valor
    transacao.valor = transacao.valor_original
    transacao.valor_original = None  # ← ADICIONAR ESTA LINHA
    
    session.add(transacao)
    session.commit()
    session.refresh(transacao)
    
    return transacao
```

**Teste Validador**: `tests/regression/test_regressao.py::TestValorOriginal::test_restaurar_valor_original`

**Prioridade**: 🟡 **MÉDIA** (não impede uso, mas comportamento inconsistente)  
**Estimativa**: 5 minutos  
**Complexidade**: Trivial

---

## Gap 4-5: Tags Case-Insensitive

### 📋 Descrição

Nomes de tags deveriam ser únicos de forma case-insensitive (ex: "Urgente" e "urgente" são duplicatas), mas atualmente o sistema permite criar/renomear duplicatas.

### ❌ Comportamento Atual

```python
# Criar primeira tag
client.post("/tags/", json={"nome": "Urgente", "cor": "#FF0000"})  # 201 OK

# Criar duplicata (case diferente)
client.post("/tags/", json={"nome": "urgente", "cor": "#00FF00"})  # 201 OK ❌

# Resultado: Duas tags com nomes "duplicados"
```

```python
# Renomear para duplicata
tag1 = Tag(nome="Tag1")
tag2 = Tag(nome="Tag2")

client.patch(f"/tags/{tag2.id}", json={"nome": "tag1"})  # 200 OK ❌

# Resultado: Duas tags com nome "tag1"
```

### ✅ Comportamento Esperado

```python
client.post("/tags/", json={"nome": "urgente", "cor": "#00FF00"})  # 400 Bad Request ✅

client.patch(f"/tags/{tag2.id}", json={"nome": "tag1"})  # 400 Bad Request ✅
```

### 🔨 Solução (Opção 1 - Database Constraint)

**Arquivo**: Criar migração Alembic

```bash
uv run alembic revision -m "adiciona unique constraint case insensitive em tag.nome"
```

```python
# alembic/versions/XXXXX_unique_tag_nome.py

def upgrade():
    # PostgreSQL
    op.create_index(
        'idx_tag_nome_lower_unique',
        'tag',
        [sa.text('LOWER(nome)')],
        unique=True
    )

def downgrade():
    op.drop_index('idx_tag_nome_lower_unique', 'tag')
```

**Arquivo**: `app/models_tags.py`

```python
from sqlalchemy import Index

class Tag(SQLModel, table=True):
    __table_args__ = (
        Index('idx_tag_nome_lower_unique', func.lower('nome'), unique=True),
    )
```

### 🔨 Solução (Opção 2 - Validação Endpoint)

**Arquivo**: `app/routers/tags.py`

```python
@router.post("/")
def criar_tag(tag: TagCreate, session: Session = Depends(get_session)):
    # Verificar duplicata case-insensitive
    tag_existente = session.exec(
        select(Tag).where(func.lower(Tag.nome) == tag.nome.lower())
    ).first()
    
    if tag_existente:
        raise HTTPException(
            status_code=400,
            detail=f"Tag com nome '{tag.nome}' já existe (case-insensitive)"
        )
    
    # ... resto do código ...

@router.patch("/{tag_id}")
def atualizar_tag(tag_id: int, tag: TagUpdate, session: Session = Depends(get_session)):
    tag_db = session.get(Tag, tag_id)
    
    if tag.nome:
        # Verificar duplicata case-insensitive (exceto a própria tag)
        tag_existente = session.exec(
            select(Tag).where(
                func.lower(Tag.nome) == tag.nome.lower(),
                Tag.id != tag_id
            )
        ).first()
        
        if tag_existente:
            raise HTTPException(
                status_code=400,
                detail=f"Tag com nome '{tag.nome}' já existe (case-insensitive)"
            )
    
    # ... resto do código ...
```

**Teste Validador**: 
- `tests/regression/test_regressao.py::TestTagsCaseInsensitive::test_criar_tag_nome_duplicado_case_insensitive`
- `tests/regression/test_regressao.py::TestTagsCaseInsensitive::test_atualizar_tag_nome_duplicado_case_insensitive`

**Prioridade**: 🟡 **MÉDIA** (UX issue, não quebra funcionalidade)  
**Estimativa**: 1 hora (incluindo migração)  
**Complexidade**: Média

---

## Gap 6: Resumo Mensal Sem Parâmetros

### 📋 Descrição

Ao chamar `/transacoes/resumo/mensal` sem parâmetros, deveria usar mês/ano atual como padrão, mas atualmente retorna 400.

### ❌ Comportamento Atual

```python
response = client.get("/transacoes/resumo/mensal")

# Resultado: 400 Bad Request
# "mes e ano são obrigatórios"
```

### ✅ Comportamento Esperado

```python
response = client.get("/transacoes/resumo/mensal")

# Resultado: 200 OK
# Resumo do mês/ano atual
```

### 🔨 Solução

**Arquivo**: `app/routers/transacoes.py`

```python
from datetime import datetime

@router.get("/resumo/mensal")
def resumo_mensal(
    mes: Optional[int] = None,  # ← Tornar opcional
    ano: Optional[int] = None,  # ← Tornar opcional
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    session: Session = Depends(get_session)
):
    # Usar mês/ano atual se não fornecidos
    if mes is None:
        mes = datetime.now().month
    if ano is None:
        ano = datetime.now().year
    
    # ... resto do código ...
```

**Teste Validador**: `tests/regression/test_regressao.py::TestResumoMensal::test_resumo_sem_parametros_usa_mes_atual`

**Prioridade**: 🟢 **BAIXA** (convenção, não afeta funcionalidade)  
**Estimativa**: 5 minutos  
**Complexidade**: Trivial

---

## Gap 7-8: Tag Rotina - Auto-Criação

### 📋 Descrição

Ao importar extrato bancário ou fatura, uma tag no formato `rotina_YYYYMM` deveria ser criada automaticamente e associada às transações importadas.

### ❌ Comportamento Atual

```python
csv_content = "data,descricao,valor,categoria\n"
csv_content += "2025-12-15,Compra,100.0,Outros\n"

response = client.post("/importacao/extrato", files={"file": ("extrato.csv", csv_file, "text/csv")})

# Resultado: 422 Unprocessable Entity
# (sistema tenta associar tag "rotina_202512" que não existe)
```

### ✅ Comportamento Esperado

```python
response = client.post("/importacao/extrato", files={"file": ("extrato.csv", csv_file, "text/csv")})

# Resultado: 200 OK
# Tag "rotina_202512" criada automaticamente
# Transações importadas associadas à tag
```

### 🔨 Solução

**Arquivo**: `app/routers/importacao.py`

```python
from app.models_tags import Tag

@router.post("/extrato")
async def importar_extrato(file: UploadFile, session: Session = Depends(get_session)):
    # ... código existente de processamento ...
    
    # Criar tag de rotina
    mes_ano = datetime.now().strftime("%Y%m")
    tag_nome = f"rotina_{mes_ano}"
    
    # Buscar ou criar tag
    tag_rotina = session.exec(select(Tag).where(Tag.nome == tag_nome)).first()
    if not tag_rotina:
        tag_rotina = Tag(nome=tag_nome, cor="#808080")  # Cinza
        session.add(tag_rotina)
        session.commit()
        session.refresh(tag_rotina)
    
    # Associar tag às transações importadas
    for transacao in transacoes_importadas:
        transacao_tag = TransacaoTag(
            transacao_id=transacao.id,
            tag_id=tag_rotina.id
        )
        session.add(transacao_tag)
    
    session.commit()
    
    return {
        "transacoes_importadas": len(transacoes_importadas),
        "tag_rotina": tag_nome
    }

@router.post("/fatura")
async def importar_fatura(file: UploadFile, session: Session = Depends(get_session)):
    # ... mesmo código acima para criar/associar tag_rotina ...
```

**Teste Validador**: 
- `tests/regression/test_regressao.py::TestImportacaoTagRotina::test_importar_extrato_cria_tag_rotina`
- `tests/regression/test_regressao.py::TestImportacaoTagRotina::test_importar_fatura_cria_tag_rotina`

**Prioridade**: 🟢 **BAIXA** (feature nice-to-have)  
**Estimativa**: 30 minutos  
**Complexidade**: Baixa

---

## 📊 Resumo de Prioridades

| Gap | Descrição | Prioridade | Estimativa | Complexidade |
|-----|-----------|------------|------------|--------------|
| 1 | CASCADE DELETE TransacaoTag | 🔴 ALTA | 30 min | Baixa |
| 3 | Restaurar valor limpa campo | 🟡 MÉDIA | 5 min | Trivial |
| 2 | Importar fatura com data_fatura | 🟡 MÉDIA | 20 min | Baixa |
| 4-5 | Tags case-insensitive | 🟡 MÉDIA | 1h | Média |
| 6 | Resumo mensal sem params | 🟢 BAIXA | 5 min | Trivial |
| 7-8 | Tag rotina auto-criação | 🟢 BAIXA | 30 min | Baixa |

**Total**: 2h 30min (gaps triviais) + 1h 30min (gaps médios) = **4 horas**

---

## 🚀 Plano de Implementação Sugerido

### Fase 1 - Quick Wins (15 minutos)

Resolver gaps triviais primeiro:

1. Gap 3: Restaurar valor limpa campo (5 min)
2. Gap 6: Resumo mensal sem params (5 min)

**Benefício**: 2 testes passando com mínimo esforço.

---

### Fase 2 - Bugs Críticos (30 minutos)

Resolver gap que causa erros:

3. Gap 1: CASCADE DELETE TransacaoTag (30 min)

**Benefício**: Sistema não quebra ao deletar transações.

---

### Fase 3 - Features Adicionais (2h 30min)

Implementar features nice-to-have:

4. Gap 2: Importar fatura com data_fatura (20 min)
5. Gap 7-8: Tag rotina auto-criação (30 min)
6. Gap 4-5: Tags case-insensitive (1h)

**Benefício**: UX melhorada, sistema mais robusto.

---

## ✅ Validação

Após implementar cada gap, executar teste específico:

```bash
# Gap 1
uv run pytest tests/regression/test_regressao.py::TestCascadesDeletion::test_deletar_transacao_remove_associacoes_tags

# Gap 2
uv run pytest tests/regression/test_regressao.py::TestCriterioDataTransacao::test_importar_fatura_com_data_transacao_e_fatura

# Gap 3
uv run pytest tests/regression/test_regressao.py::TestValorOriginal::test_restaurar_valor_original

# Gap 4-5
uv run pytest tests/regression/test_regressao.py::TestTagsCaseInsensitive

# Gap 6
uv run pytest tests/regression/test_regressao.py::TestResumoMensal::test_resumo_sem_parametros_usa_mes_atual

# Gap 7-8
uv run pytest tests/regression/test_regressao.py::TestImportacaoTagRotina

# Todos os testes de regressão
uv run pytest tests/regression/

# Suite completa
uv run pytest
```

Quando todos os 8 gaps forem resolvidos, os testes de regressão devem estar **21/21 passando (100%)**.

---

**Última Atualização**: 28 de dezembro de 2024  
**Status**: Aguardando implementação  
**Autor**: GitHub Copilot
