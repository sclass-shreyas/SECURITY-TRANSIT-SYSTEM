"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.String(length=64), primary_key=True),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("class_name", sa.String(length=100), nullable=False),
        sa.Column("zone", sa.String(length=100), nullable=False),
        sa.Column("clip_path", sa.String(length=500), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_object_id", "alerts", ["object_id"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_timestamp", "alerts", ["timestamp"])
    op.create_index("ix_alerts_zone", "alerts", ["zone"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("frame_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_events_frame_id", "events", ["frame_id"])
    op.create_index("ix_events_timestamp", "events", ["timestamp"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=120), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("zone_name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("polygon_points_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_zones_zone_name", "zones", ["zone_name"], unique=True)

    op.create_table(
        "clips",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("alert_id", sa.String(length=64), sa.ForeignKey("alerts.alert_id")),
        sa.Column("clip_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_clips_alert_id", "clips", ["alert_id"])


def downgrade() -> None:
    op.drop_index("ix_clips_alert_id", table_name="clips")
    op.drop_table("clips")
    op.drop_index("ix_zones_zone_name", table_name="zones")
    op.drop_table("zones")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_events_timestamp", table_name="events")
    op.drop_index("ix_events_frame_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_alerts_zone", table_name="alerts")
    op.drop_index("ix_alerts_timestamp", table_name="alerts")
    op.drop_index("ix_alerts_severity", table_name="alerts")
    op.drop_index("ix_alerts_object_id", table_name="alerts")
    op.drop_index("ix_alerts_alert_type", table_name="alerts")
    op.drop_table("alerts")
