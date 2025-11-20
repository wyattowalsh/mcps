import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from sqlmodel import SQLModel

# Import settings and models
from packages.harvester.settings import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url from settings
# Convert async URL to sync URL for Alembic migrations
db_url = settings.db_url

# Convert asyncpg to psycopg2 for sync migrations (PostgreSQL)
if "postgresql+asyncpg" in db_url:
    sync_db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
# Convert aiosqlite to sqlite for sync migrations (SQLite)
elif "sqlite+aiosqlite" in db_url:
    sync_db_url = db_url.replace("sqlite+aiosqlite", "sqlite")
else:
    sync_db_url = db_url

config.set_main_option("sqlalchemy.url", sync_db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Import all models here to ensure they're registered
from packages.harvester.models import *  # noqa: F401, F403

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


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Handles both PostgreSQL and SQLite appropriately.
    """
    from sqlalchemy import engine_from_config

    # Get the configuration section
    configuration = config.get_section(config.config_ini_section, {})

    # Add PostgreSQL-specific settings if using PostgreSQL
    if settings.is_postgresql:
        # Use appropriate pool for PostgreSQL
        poolclass = pool.QueuePool
        # Add pool settings
        configuration.update({
            "pool_size": "5",
            "max_overflow": "10",
            "pool_pre_ping": "True",
        })
    else:
        # Use NullPool for SQLite (single connection)
        poolclass = pool.NullPool

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=poolclass,
    )

    with connectable.connect() as connection:
        # Add PostgreSQL-specific configuration
        if settings.is_postgresql:
            # Set search_path if needed
            # connection.execute(text("SET search_path TO public"))
            pass

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Enable batch mode for SQLite to support ALTER operations
            render_as_batch=settings.is_sqlite,
            # Compare types for better migration detection
            compare_type=True,
            # Compare server defaults
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
