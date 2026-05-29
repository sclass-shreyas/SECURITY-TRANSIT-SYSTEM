"""initial production schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


uuid_type = postgresql.UUID(as_uuid=True)
jsonb_type = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "cameras",
        sa.Column("camera_id", uuid_type, primary_key=True),
        sa.Column("camera_name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", jsonb_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_cameras_camera_name", "cameras", ["camera_name"], unique=True)

    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("zone_name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("polygon_points_json", jsonb_type, nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.create_index("ix_zones_zone_name", "zones", ["zone_name"], unique=True)

    op.create_table(
        "events",
        sa.Column("event_id", uuid_type, primary_key=True),
        sa.Column("correlation_id", uuid_type, nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column("camera_id", uuid_type, sa.ForeignKey("cameras.camera_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("frame_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", jsonb_type, nullable=False),
    )
    op.create_index("ix_events_correlation_id", "events", ["correlation_id"])
    op.create_index("ix_events_camera_id", "events", ["camera_id"])
    op.create_index("ix_events_frame_id", "events", ["frame_id"])
    op.create_index("ix_events_timestamp", "events", ["timestamp"])
    op.create_index("ix_events_raw_payload_gin", "events", ["raw_payload"], postgresql_using="gin")

    op.create_table(
        "alerts",
        sa.Column("alert_id", uuid_type, primary_key=True),
        sa.Column("event_id", uuid_type, sa.ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("object_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("class_name", sa.String(length=100), nullable=False),
        sa.Column("zone", sa.String(length=100), nullable=False),
        sa.Column("clip_path", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("metadata", jsonb_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_alerts_event_id", "alerts", ["event_id"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_object_id", "alerts", ["object_id"])
    op.create_index("ix_alerts_zone", "alerts", ["zone"])
    op.create_index("ix_alerts_metadata_gin", "alerts", ["metadata"], postgresql_using="gin")

    op.create_table(
        "clips",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("alert_id", uuid_type, sa.ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False),
        sa.Column("clip_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_clips_alert_id", "clips", ["alert_id"])

    op.create_table(
        "analytics_results",
        sa.Column("result_id", uuid_type, primary_key=True),
        sa.Column("event_id", uuid_type, sa.ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False),
        sa.Column("detector_type", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("metadata", jsonb_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_analytics_results_event_id", "analytics_results", ["event_id"])
    op.create_index("ix_analytics_results_detector_type", "analytics_results", ["detector_type"])
    op.create_index("ix_analytics_results_metadata_gin", "analytics_results", ["metadata"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_analytics_results_metadata_gin", table_name="analytics_results")
    op.drop_index("ix_analytics_results_detector_type", table_name="analytics_results")
    op.drop_index("ix_analytics_results_event_id", table_name="analytics_results")
    op.drop_table("analytics_results")

    op.drop_index("ix_clips_alert_id", table_name="clips")
    op.drop_table("clips")

    op.drop_index("ix_alerts_metadata_gin", table_name="alerts")
    op.drop_index("ix_alerts_zone", table_name="alerts")
    op.drop_index("ix_alerts_object_id", table_name="alerts")
    op.drop_index("ix_alerts_alert_type", table_name="alerts")
    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_severity", table_name="alerts")
    op.drop_index("ix_alerts_event_id", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("ix_events_raw_payload_gin", table_name="events")
    op.drop_index("ix_events_timestamp", table_name="events")
    op.drop_index("ix_events_frame_id", table_name="events")
    op.drop_index("ix_events_camera_id", table_name="events")
    op.drop_index("ix_events_correlation_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_zones_zone_name", table_name="zones")
    op.drop_table("zones")

    op.drop_index("ix_cameras_camera_name", table_name="cameras")
    op.drop_table("cameras")
