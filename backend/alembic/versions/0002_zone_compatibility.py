"""add compatibility columns to zones

Revision ID: 0002_zone_compatibility
Revises: 0001_initial
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_zone_compatibility"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("zones", sa.Column("zone_id", sa.String(length=64), nullable=True))
    op.add_column("zones", sa.Column("name", sa.String(length=128), nullable=True))
    op.add_column(
        "zones",
        sa.Column("restricted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "zones",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.execute("UPDATE zones SET zone_id = zone_name, name = zone_name WHERE zone_id IS NULL")

    op.alter_column("zones", "zone_id", nullable=False)
    op.alter_column("zones", "name", nullable=False)
    op.create_index("ix_zones_zone_id", "zones", ["zone_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_zones_zone_id", table_name="zones")
    op.drop_column("zones", "created_at")
    op.drop_column("zones", "restricted")
    op.drop_column("zones", "name")
    op.drop_column("zones", "zone_id")
