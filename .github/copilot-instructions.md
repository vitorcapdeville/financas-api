# Instruções para o GitHub Copilot - API de Finanças Pessoais

## Contexto do Projeto

Esta é uma API REST para gerenciamento de finanças pessoais, construída com:
- **FastAPI**: Framework web moderno e rápido
- **SQLModel**: ORM que combina SQLAlchemy e Pydantic
- **PostgreSQL**: Banco de dados relacional
- **Pandas**: Para processamento de arquivos de importação

## Objetivo

Permitir que o usuário:
1. Importe extratos bancários e faturas de cartão de crédito (CSV/Excel)
2. Visualize suas transações financeiras organizadas por mês
3. Categorize e edite transações
4. Adicione transações manualmente
5. Obtenha insights sobre entradas, saídas e gastos por categoria

## Estrutura do Projeto

```
app/
├── main.py              # Aplicação principal FastAPI
├── config.py            # Configurações (DATABASE_URL via pydantic-settings)
├── database.py          # Engine, sessão e create_db_and_tables()
├── models.py            # Modelo Transacao (tabela principal)
├── models_config.py     # Modelo Configuracao (preferências)
└── routers/
    ├── transacoes.py    # CRUD de transações + resumo mensal
    ├── importacao.py    # Importação de extratos/faturas (CSV/Excel)
    └── configuracoes.py # Get/Set de configurações key-value
```

## Arquitetura e Fluxo de Dados

- **Multi-tenant data**: Sistema de `Configuracao` para armazenar preferências do usuário (ex: `diaInicioPeriodo`)
- **Dual filtering**: Endpoints suportam `mes/ano` OU `data_inicio/data_fim` - sempre priorizar período customizado quando ambos fornecidos
- **Database migrations**: Usamos Alembic para gerenciar migrações - NUNCA crie tabelas manualmente ou use `create_all()`
- **CORS setup**: Frontend em `http://localhost:3000` já configurado em `main.py`

## Modelos de Dados

### Transacao (app/models.py)
- **id**: Identificador único
- **data**: Data da transação
- **descricao**: Descrição textual
- **valor**: Valor absoluto (sempre positivo)
- **tipo**: "entrada" ou "saida" (enum TipoTransacao)
- **categoria**: Categoria (opcional, editável)
- **origem**: "manual", "extrato_bancario", "fatura_cartao"
- **observacoes**: Notas adicionais
- **criado_em / atualizado_em**: Timestamps

### Configuracao (app/models_config.py)
- **chave**: Identificador único da configuração (unique, indexed)
- **valor**: Valor em string
- Usado para preferências do usuário (ex: `diaInicioPeriodo`)

## Padrões de Código

### 1. Modelos SQLModel
- Use `SQLModel` com `table=True` para tabelas
- Crie schemas separados: `Create`, `Update`, `Read`
- Use `Field()` para constraints e descrições
- Sempre inclua `Optional[]` onde aplicável

### 2. Routers (Endpoints)
- Agrupe endpoints relacionados em routers
- Use prefixos descritivos (`/transacoes`, `/importacao`)
- Adicione tags para documentação Swagger
- Sempre documente com docstrings
- Use `response_model` para validação de saída
- Use `Depends(get_session)` para sessões de banco

### 3. Tratamento de Erros
- Lance `HTTPException` com códigos apropriados
- 404 para recursos não encontrados
- 400 para dados inválidos
- 500 para erros do servidor
- Sempre forneça mensagens descritivas

### 4. Queries
- Use `select()` do SQLModel para queries
- Aplique filtros com `.where()`
- Use Query parameters para filtros opcionais
- Valide parâmetros de query com `ge`, `le`, etc

### 5. Importação de Dados
- Aceite CSV e Excel (`.csv`, `.xlsx`, `.xls`)
- Use Pandas para processamento
- Normalize nomes de colunas (lowercase, strip)
- Valide colunas obrigatórias antes de processar
- Forneça mensagens de erro claras
- Sempre use transações do banco

### 6. Validações
- Use Pydantic para validação de dados
- Enums para valores fixos (TipoTransacao)
- Constraints em Fields (ge, le, min_length, etc)
- Valide datas e conversões numéricas

## Exemplos de Código

### Criar um novo endpoint
```python
@router.get("/exemplo", response_model=List[ExemploRead])
def listar_exemplos(
    filtro: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Descrição clara do que faz"""
    query = select(Exemplo)
    if filtro:
        query = query.where(Exemplo.campo == filtro)
    return session.exec(query).all()
```

### Adicionar um novo modelo
```python
class NovoModelo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campo: str = Field(description="Descrição")
    criado_em: datetime = Field(default_factory=datetime.now)
```

## CORS

A API permite requisições do frontend Next.js em `http://localhost:3000`. Ajuste conforme necessário.

## Banco de Dados

- Use sempre `session.commit()` após modificações
- Use `session.refresh()` após criar/atualizar
- Sempre feche sessões corretamente (handled by `get_session`)
- **NUNCA use `create_all()` ou `create_db_and_tables()`** - usamos Alembic para migrações

## Migrações de Banco de Dados (Alembic)

**CRÍTICO**: Este projeto usa **Alembic** para gerenciar migrações do banco de dados. Qualquer mudança que afete o schema do banco **DEVE** ser feita através de migrações.

### Por que Alembic?

- Mantém histórico completo de mudanças no schema
- Permite rollback de alterações
- Evita perda de dados em produção
- Permite controle de versão do schema
- Facilita deploy em múltiplos ambientes

### Estrutura de Arquivos

```
alembic/
├── versions/          # Scripts de migração (versionados)
├── env.py            # Configuração do Alembic (conecta com SQLModel)
├── script.py.mako    # Template para novos scripts
└── README           
alembic.ini           # Configurações do Alembic
```

### Workflow de Migrações

#### 1. Criar um Novo Modelo

Ao adicionar um novo modelo SQLModel:

```python
# app/models_novo.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class NovoModelo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True)
    valor: float
    criado_em: datetime = Field(default_factory=datetime.now)
```

**IMPORTANTE**: Importe o modelo em `alembic/env.py` para que seja detectado:

```python
# alembic/env.py
from app.models import Transacao  # noqa: F401
from app.models_config import Configuracao  # noqa: F401
from app.models_novo import NovoModelo  # noqa: F401  <-- ADICIONE AQUI
```

#### 2. Gerar Migração Automática

```bash
# Gera uma nova migração detectando mudanças nos modelos
uv run alembic revision --autogenerate -m "descrição_da_mudança"

# Exemplos:
uv run alembic revision --autogenerate -m "adiciona tabela de orçamentos"
uv run alembic revision --autogenerate -m "adiciona coluna nota_fiscal em transacao"
uv run alembic revision --autogenerate -m "adiciona índice em categoria"
```

O Alembic irá:
- Comparar os modelos SQLModel com o estado atual do banco
- Detectar diferenças (novas tabelas, colunas, índices, etc)
- Gerar um script de migração em `alembic/versions/`
- Incluir timestamp no nome do arquivo para ordenação

#### 3. Revisar o Script Gerado

**SEMPRE revise o script gerado antes de aplicar!**

```python
# alembic/versions/20251227_1045-abc123_adiciona_orcamentos.py
def upgrade() -> None:
    # Operações para aplicar a migração
    op.create_table(
        'orcamento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('categoria', sa.String(), nullable=False),
        sa.Column('valor_maximo', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    # Operações para reverter a migração
    op.drop_table('orcamento')
```

**Verifique**:
- Operações de upgrade estão corretas
- Operações de downgrade revertem corretamente
- Não há perda de dados
- Valores default estão corretos
- Constraints estão adequados

#### 4. Aplicar a Migração

```bash
# Aplica todas as migrações pendentes
uv run alembic upgrade head

# Aplicar uma migração específica
uv run alembic upgrade +1  # Próxima migração
uv run alembic upgrade abc123  # Migração específica por revision
```

#### 5. Reverter Migração (se necessário)

```bash
# Voltar uma migração
uv run alembic downgrade -1

# Voltar para uma versão específica
uv run alembic downgrade abc123

# Voltar todas as migrações
uv run alembic downgrade base
```

### Comandos Úteis

```bash
# Ver histórico de migrações
uv run alembic history

# Ver status atual
uv run alembic current

# Ver SQL que será executado (sem aplicar)
uv run alembic upgrade head --sql

# Criar migração vazia (para mudanças manuais)
uv run alembic revision -m "adiciona dados iniciais"
```

### Casos Especiais

#### Modificar Dados Durante Migração

Para inserir/atualizar dados durante uma migração:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column

def upgrade() -> None:
    # Criar nova tabela
    op.create_table(
        'categoria',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome', sa.String(), nullable=False),
    )
    
    # Inserir dados iniciais
    categorias_table = table('categoria',
        column('nome', sa.String())
    )
    
    op.bulk_insert(categorias_table, [
        {'nome': 'Alimentação'},
        {'nome': 'Transporte'},
        {'nome': 'Moradia'},
    ])
```

#### Adicionar Coluna com Valor Default

```python
def upgrade() -> None:
    # Adiciona coluna com valor padrão para registros existentes
    op.add_column('transacao', 
        sa.Column('status', sa.String(), nullable=False, server_default='ativo')
    )
    
    # Remove server_default após preencher registros existentes
    op.alter_column('transacao', 'status', server_default=None)
```

#### Renomear Coluna (preservando dados)

```python
def upgrade() -> None:
    op.alter_column('transacao', 'descricao', new_column_name='nome')

def downgrade() -> None:
    op.alter_column('transacao', 'nome', new_column_name='descricao')
```

### Regras Importantes

1. **NUNCA edite migrações já aplicadas** - crie uma nova migração
2. **SEMPRE importe novos modelos em `alembic/env.py`**
3. **SEMPRE revise o script antes de aplicar**
4. **Teste migrações em desenvolvimento antes de produção**
5. **Commit migrações junto com mudanças de código**
6. **Nunca delete scripts de migração do histórico**
7. **Use mensagens descritivas** nas migrações

### Workflow Completo: Adicionar Nova Funcionalidade

```bash
# 1. Criar/modificar modelo SQLModel
# 2. Importar em alembic/env.py
# 3. Gerar migração
uv run alembic revision --autogenerate -m "adiciona modelo X"

# 4. Revisar script gerado em alembic/versions/
# 5. Aplicar migração
uv run alembic upgrade head

# 6. Testar aplicação
uv run uvicorn app.main:app --reload

# 7. Commit código + migração
git add app/models_novo.py alembic/env.py alembic/versions/
git commit -m "feat: adiciona modelo X com migração"
```

### Troubleshooting

**Erro: "Target database is not up to date"**
```bash
# Aplique as migrações pendentes
uv run alembic upgrade head
```

**Erro: "Can't locate revision identified by 'abc123'"**
```bash
# Verifique o histórico
uv run alembic history
# Certifique-se de que o arquivo de migração existe
```

**Migração não detecta mudanças**
```bash
# 1. Verifique se o modelo está importado em alembic/env.py
# 2. Verifique se SQLModel.metadata está configurado
# 3. Force a criação manual:
uv run alembic revision -m "descrição"
# Edite manualmente o script gerado
```

**Banco em estado inconsistente**
```bash
# Em DESENVOLVIMENTO, você pode resetar:
uv run alembic downgrade base  # Remove todas as migrações
uv run alembic upgrade head    # Reaplica tudo

# Em PRODUÇÃO, NUNCA faça isso - crie migrações de correção
```

## Testes

Ao criar novos endpoints:
1. Teste manualmente via `/docs`
2. Verifique validações de dados
3. Teste casos de erro (404, 400)
4. Valide os response_models

## Gerenciamento de Ambiente

**IMPORTANTE**: Use UV para gerenciar o ambiente virtual e dependências.

### Instalação do UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup do Projeto
```bash
# Inicializar projeto com UV (se ainda não inicializado)
uv init --no-workspace --app

# Criar ambiente virtual (já feito pelo init, mas pode ser executado separadamente)
uv venv

# Adicionar dependências (UV gerencia automaticamente via pyproject.toml)
uv add fastapi uvicorn sqlmodel psycopg2-binary python-dotenv pydantic pydantic-settings python-multipart pandas openpyxl

# Sincronizar ambiente (instala dependências do pyproject.toml)
uv sync
```

### Configuração de Ambiente (.env)

**CRÍTICO**: Antes de executar, configure o arquivo `.env`:

```bash
# Copie o template
cp .env.example .env
```

O arquivo `.env` deve conter:
```dotenv
DATABASE_URL=postgresql://financas_user:financas_pass@localhost:5432/financas_db
```

**PostgreSQL deve estar rodando** antes de iniciar a aplicação.

**Aplicar Migrações**: Na primeira execução ou após mudanças no schema:
```bash
uv run alembic upgrade head
```

### Adicionar Nova Dependência
```bash
# Use uv add (não uv pip install!)
uv add nome-do-pacote

# UV atualiza automaticamente pyproject.toml e uv.lock
# NÃO use requirements.txt - UV gerencia tudo via pyproject.toml
```

### Executar a Aplicação
```bash
# Use uv run para executar comandos no ambiente
uv run uvicorn app.main:app --reload
```

**VS Code Task**: Existe uma task configurada "Run FastAPI" que pode ser executada via Command Palette (Ctrl+Shift+P → "Tasks: Run Task").

## Verificação Pós-Modificação

**CRÍTICO**: Após QUALQUER modificação no código:

1. **Execute em modo desenvolvimento**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

2. **Verifique no terminal**:
   - Sem erros de sintaxe
   - Sem erros de importação
   - Servidor iniciou corretamente

3. **Teste via /docs**:
   - Acesse http://localhost:8000/docs
   - Teste os endpoints modificados
   - Valide requests e responses

4. **Verifique logs**:
   - Sem erros no console
   - Queries SQL executando corretamente

**Nunca deixe código quebrado sem testar!**

## Boas Práticas

1. **Sempre valide entrada de dados**
2. **Use tipos apropriados** (date, datetime, float, Enum)
3. **Documente todos os endpoints** com docstrings
4. **Normalize dados** antes de salvar (lowercase, strip, etc)
5. **Use transações** para operações múltiplas
6. **Timestamps**: Sempre atualize `atualizado_em`
7. **Mensagens claras**: Erros devem ser informativos
8. **Teste imediatamente**: Execute em dev mode após cada mudança

## Convenções de Nomenclatura

- **Funções**: snake_case (listar_transacoes)
- **Classes**: PascalCase (Transacao, TransacaoCreate)
- **Variáveis**: snake_case
- **Constantes**: UPPER_CASE
- **Endpoints**: kebab-case no path

## Commits

**IMPORTANTE**: Todos os commits devem seguir o padrão **Conventional Commits** (https://www.conventionalcommits.org/en/v1.0.0/)

**CRÍTICO**: Use sempre o **MCP GitKraken** para fazer commits. NUNCA use comandos git diretamente no terminal.

### Como Fazer Commits

Use as ferramentas MCP do GitKraken:
```
1. mcp_gitkraken_git_add_or_commit - para adicionar arquivos e fazer commit
2. mcp_gitkraken_git_push - para enviar para o repositório remoto
```

### Formato
```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé(s) opcional(is)]
```

### Tipos Comuns
- **feat**: Nova funcionalidade
- **fix**: Correção de bug
- **docs**: Mudanças na documentação
- **style**: Mudanças de formatação (sem alteração de código)
- **refactor**: Refatoração de código (sem nova feature ou fix)
- **perf**: Melhorias de performance
- **test**: Adição ou correção de testes
- **chore**: Tarefas de manutenção (build, configs, etc)

### Exemplos
```bash
feat: adiciona endpoint de resumo mensal por categoria
fix: corrige cálculo de período customizado
docs: atualiza README com instruções de configuração
refactor: extrai lógica de validação para função separada
chore: adiciona dependência pandas para processamento de CSV
```

### Commits Breaking Changes
Para mudanças que quebram compatibilidade, adicione `!` após o tipo ou `BREAKING CHANGE:` no rodapé:
```bash
feat!: remove suporte a Python 3.8
# ou
feat: migra para SQLModel 2.0

BREAKING CHANGE: SQLModel 2.0 requer mudanças nos modelos existentes
```

## Próximas Funcionalidades

Ao adicionar novas features, considere:
- Filtros por período customizado
- Exportação de relatórios
- Metas de gastos por categoria
- Alertas de gastos
- Dashboard com gráficos
- Autenticação de usuários
