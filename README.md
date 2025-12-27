# API de Finanças Pessoais

Este é o backend da aplicação de finanças pessoais, construído com FastAPI, SQLModel e PostgreSQL.

## Configuração

1. Instale o UV (se ainda não tiver):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Crie um ambiente virtual:
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
```

3. Adicione as dependências do projeto:
```bash
# UV gerencia dependências via pyproject.toml, não requirements.txt
uv add fastapi uvicorn sqlmodel psycopg2-binary python-dotenv pydantic pydantic-settings python-multipart pandas openpyxl alembic

# Ou sincronize se já existir pyproject.toml
uv sync
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o .env com suas configurações
```

4. Inicie o banco de dados PostgreSQL (veja docker-compose.yml na raiz do workspace)

5. Aplique as migrações do banco de dados:
```bash
uv run alembic upgrade head
```

6. Execute a aplicação:
```bash
uv run uvicorn app.main:app --reload
```

## Estrutura

- `app/main.py`: Aplicação principal FastAPI
- `app/models.py`: Modelos SQLModel (Transacao)
- `app/models_config.py`: Modelo de Configuração
- `app/database.py`: Configuração do banco de dados
- `app/config.py`: Configurações da aplicação
- `app/routers/`: Endpoints da API
  - `transacoes.py`: CRUD de transações
  - `importacao.py`: Importação de extratos e faturas
  - `configuracoes.py`: Configurações do usuário
- `alembic/`: Migrações do banco de dados
  - `versions/`: Scripts de migração
  - `env.py`: Configuração do Alembic

## Endpoints Principais

- `GET /transacoes`: Lista todas as transações (com filtros)
- `POST /transacoes`: Cria uma nova transação
- `PATCH /transacoes/{id}`: Atualiza uma transação
- `DELETE /transacoes/{id}`: Deleta uma transação
- `GET /transacoes/resumo/mensal`: Resumo mensal
- `POST /importacao/extrato`: Importa extrato bancário
- `POST /importacao/fatura`: Importa fatura de cartão

## Documentação

Acesse `/docs` para documentação interativa Swagger.

## Desenvolvimento

### Workflow Recomendado

1. Faça suas modificações no código
2. Execute a aplicação em modo desenvolvimento:
   ```bash
   uv run uvicorn app.main:app --reload
   ```
3. Verifique se não há erros no terminal
4. Teste via `/docs` (http://localhost:8000/docs)
5. Valide o comportamento esperado

### Adicionar Dependências

```bash
# Use comandos nativos do UV
uv add nome-do-pacote

# UV atualiza automaticamente pyproject.toml e uv.lock
# NÃO use requirements.txt
```

**IMPORTANTE**: Sempre teste após modificações!

## Migrações de Banco de Dados (Alembic)

Este projeto usa **Alembic** para gerenciar migrações do banco de dados. **NUNCA** use `create_all()` ou modifique o schema diretamente.

### Comandos Principais

```bash
# Criar uma nova migração (detecta mudanças automaticamente)
uv run alembic revision --autogenerate -m "descrição da mudança"

# Aplicar todas as migrações pendentes
uv run alembic upgrade head

# Ver status atual
uv run alembic current

# Ver histórico de migrações
uv run alembic history

# Reverter última migração
uv run alembic downgrade -1

# Reverter todas as migrações
uv run alembic downgrade base
```

### Workflow: Adicionar Novo Modelo

1. Crie o novo modelo em `app/models_*.py`
2. Importe o modelo em `alembic/env.py`:
   ```python
   from app.models_novo import NovoModelo  # noqa: F401
   ```
3. Gere a migração:
   ```bash
   uv run alembic revision --autogenerate -m "adiciona modelo NovoModelo"
   ```
4. **Revise o script gerado** em `alembic/versions/`
5. Aplique a migração:
   ```bash
   uv run alembic upgrade head
   ```
6. Teste a aplicação

### Regras Importantes

- ✅ **SEMPRE** use migrações para mudanças no schema
- ✅ **SEMPRE** revise scripts gerados antes de aplicar
- ✅ **SEMPRE** importe novos modelos em `alembic/env.py`
- ❌ **NUNCA** edite migrações já aplicadas
- ❌ **NUNCA** delete scripts de migração do histórico
- ❌ **NUNCA** use `create_all()` ou `drop_all()`
