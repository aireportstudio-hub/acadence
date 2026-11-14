import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = os.environ.get("MIGRATION_DATABASE_URL")
if not database_url:
    raise RuntimeError("MIGRATION_DATABASE_URL must be set to run Document migrations")


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="document",
    )
    context.execute("SET ROLE acadence_document_migrator")
    context.execute("SET ROLE acadence_document_owner")
    with context.begin_transaction():
        context.run_migrations()
    context.execute("RESET ROLE")


def run_migrations_online() -> None:
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        connection.exec_driver_sql("SET ROLE acadence_document_migrator")
        connection.exec_driver_sql("SET ROLE acadence_document_owner")
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=None,
            version_table_schema="document",
        )
        try:
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if connection.in_transaction():
                connection.rollback()
            connection.exec_driver_sql("RESET ROLE")
            connection.commit()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
