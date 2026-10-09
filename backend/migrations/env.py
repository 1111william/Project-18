from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, URL
from sqlalchemy.pool import NullPool


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.app.config import settings  # noqa: E402
from backend.app.database import Base  # noqa: E402
import backend.app.models  # noqa: E402,F401
from backend.migrations.autogenerate_safety import (  # noqa: E402
    reject_case_folded_autogenerate,
)


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str | URL:
    return settings.database_url


def _render_url(url: str | URL) -> str:
    if isinstance(url, URL):
        return url.render_as_string(hide_password=False)
    return str(url)


def _autogenerate_requested() -> bool:
    """Detect both ``check`` and ``revision --autogenerate`` invocations."""

    revision_context = context.get_context().opts.get("revision_context")
    command_args = getattr(revision_context, "command_args", {})
    if command_args.get("autogenerate"):
        return True

    command_options = getattr(config, "cmd_opts", None)
    return bool(getattr(command_options, "autogenerate", False))


def _configure_connection(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    reject_case_folded_autogenerate(
        connection,
        autogenerate_requested=_autogenerate_requested(),
    )


def run_migrations_offline() -> None:
    context.configure(
        url=_render_url(_database_url()),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        _configure_connection(supplied_connection)
        with context.begin_transaction():
            context.run_migrations()
        return

    engine = create_engine(
        _database_url(),
        connect_args=settings.database_connect_args,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
    with engine.connect() as connection:
        _configure_connection(connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
