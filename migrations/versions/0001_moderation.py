"""Guild-scoped warns, bans and mutes.

Tables created earlier by ``metadata.create_all`` (no guild, naive datetimes)
are kept as ``<name>_legacy``: their records cannot be attributed to a guild.

Revision ID: 0001
Revises:
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("warns", "bans", "mutes")


def _common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("moderator_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _rename_postgres_objects(table: str, suffix_from: str, suffix_to: str) -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    inspector = sa.inspect(bind)

    def renamed(name: str) -> str:
        return name.removesuffix(suffix_from) + suffix_to

    pk = inspector.get_pk_constraint(table).get("name")
    constraints = [pk] if pk else []
    constraints += [c["name"] for c in inspector.get_unique_constraints(table) if c["name"]]
    for name in constraints:
        op.execute(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{name}" TO "{renamed(name)}"')
    for index in inspector.get_indexes(table):
        name = index["name"]
        if name and name not in constraints:
            op.execute(f'ALTER INDEX "{name}" RENAME TO "{renamed(name)}"')
    if any(column["name"] == "id" for column in inspector.get_columns(table)):
        sequence = bind.scalar(sa.text("SELECT pg_get_serial_sequence(:table, 'id')"), {"table": f'"{table}"'})
        if sequence:
            name = sequence.rpartition(".")[2].strip('"')
            op.execute(f'ALTER SEQUENCE {sequence} RENAME TO "{renamed(name)}"')


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    for table in TABLES:
        if table in existing:
            op.rename_table(table, f"{table}_legacy")
            _rename_postgres_objects(f"{table}_legacy", "", "_legacy")

        extra = [sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False)] if table == "mutes" else []
        op.create_table(
            table,
            *_common_columns(),
            *extra,
            sa.PrimaryKeyConstraint("id", name=f"pk_{table}"),
        )
        op.create_index(f"ix_{table}_guild_id_target_id", table, ["guild_id", "target_id"])


def downgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    for table in TABLES:
        op.drop_index(f"ix_{table}_guild_id_target_id", table_name=table)
        op.drop_table(table)
        if f"{table}_legacy" in existing:
            _rename_postgres_objects(f"{table}_legacy", "_legacy", "")
            op.rename_table(f"{table}_legacy", table)
