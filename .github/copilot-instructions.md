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
- **Database initialization**: Ao criar novo modelo, SEMPRE importá-lo em `database.py` no `create_db_and_tables()` para que seja criado
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
- As tabelas são criadas automaticamente no startup

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
