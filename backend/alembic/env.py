"""Alembic environment.

Connects with the migrations URL resolved by _derive_urls() in src.database
(project-owner role, direct endpoint). The owner role can run DDL freely and
bypasses RLS.
"""
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models so target_metadata is populated.
# MIGRATIONS_URL is the third element of _derive_urls(); importing it here
# also covers Render PR previews where only DATABASE_URL is auto-injected.
from src.database import Base, MIGRATIONS_URL  # noqa: E402
from src import models  # noqa: F401, E402

config.set_main_option("sqlalchemy.url", MIGRATIONS_URL)

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
