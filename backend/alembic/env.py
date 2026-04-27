"""Alembic environment.

Connects with DATABASE_URL_MIGRATIONS (project-owner role, direct endpoint).
The owner role can run DDL freely and bypasses RLS.
"""
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

migrations_url = os.getenv("DATABASE_URL_MIGRATIONS")
if not migrations_url:
    raise RuntimeError("DATABASE_URL_MIGRATIONS is not set")
config.set_main_option("sqlalchemy.url", migrations_url)

# Import models so target_metadata is populated.
from src.database import Base  # noqa: E402
from src import models  # noqa: F401, E402

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Offline mode is not supported in this project")
else:
    run_migrations_online()
