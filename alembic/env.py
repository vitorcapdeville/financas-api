from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Importar configurações do projeto
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.infrastructure.config import get_settings
from app.infrastructure.database.engine import get_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Configurar a URL do banco de dados a partir das configurações
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Importar todos os modelos SQLModel da nova estrutura (Clean Architecture)
from sqlmodel import SQLModel
from app.infrastructure.database.models.transacao_model import TransacaoModel  # noqa: F401
from app.infrastructure.database.models.configuracao_model import ConfiguracaoModel  # noqa: F401
from app.infrastructure.database.models.tag_model import TagModel, TransacaoTagModel  # noqa: F401
from app.infrastructure.database.models.regra_model import RegraModel, RegraTagModel  # noqa: F401

target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Usar o engine já configurado no projeto
    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,  # Detecta mudanças de tipo
            compare_server_default=True  # Detecta mudanças em valores default
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
