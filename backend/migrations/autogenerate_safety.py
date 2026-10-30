"""Guards for Alembic schema comparison on case-folding MySQL servers."""

from __future__ import annotations

from alembic.util import CommandError
from sqlalchemy.engine import Connection


def reject_case_folded_autogenerate(
    connection: Connection,
    *,
    autogenerate_requested: bool,
) -> None:
    """Stop Alembic before it can report destructive case-only table diffs.

    Alembic compares SQLAlchemy table keys case-sensitively. MySQL with a
    nonzero ``lower_case_table_names`` reflects this project's CamelCase table
    names in a different case, so both ``check`` and ``revision
    --autogenerate`` can falsely propose dropping and recreating all tables.
    """

    if not autogenerate_requested:
        return
    if connection.dialect.name not in {"mysql", "mariadb"}:
        return

    lower_case_mode = int(
        connection.exec_driver_sql(
            "SELECT @@lower_case_table_names"
        ).scalar_one()
    )
    if lower_case_mode == 0:
        return

    raise CommandError(
        "Alembic autogenerate/check is disabled on this server because "
        f"@@lower_case_table_names={lower_case_mode} and the managed schema "
        "intentionally uses CamelCase names. Alembic would misreport the "
        "tables as destructive drop/create operations. Do not generate a "
        "migration from that diff; run "
        "'python backend/migrations/audit_existing.py' instead. Run "
        "'alembic check' only on case-sensitive MySQL "
        "(@@lower_case_table_names=0), such as Linux CI."
    )
