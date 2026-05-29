from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from backend.config import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {"cameras", "zones", "events", "alerts", "clips", "analytics_results"}
EXPECTED_INDEXES = {
    "cameras": {"ix_cameras_camera_name"},
    "zones": {"ix_zones_zone_name"},
    "events": {"ix_events_correlation_id", "ix_events_camera_id", "ix_events_frame_id", "ix_events_timestamp", "ix_events_raw_payload_gin"},
    "alerts": {
        "ix_alerts_event_id",
        "ix_alerts_severity",
        "ix_alerts_status",
        "ix_alerts_created_at",
        "ix_alerts_alert_type",
        "ix_alerts_object_id",
        "ix_alerts_zone",
        "ix_alerts_metadata_gin",
    },
    "clips": {"ix_clips_alert_id"},
    "analytics_results": {
        "ix_analytics_results_event_id",
        "ix_analytics_results_detector_type",
        "ix_analytics_results_metadata_gin",
    },
}


def _database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL migration verification.")
    if not database_url.startswith("postgresql+asyncpg"):
        pytest.fail("PostgreSQL migration verification requires a postgresql+asyncpg DATABASE_URL.")
    return database_url


def _alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _collect_schema(sync_connection):
    inspector = inspect(sync_connection)
    tables = inspector.get_table_names()
    indexes = {table: {index["name"] for index in inspector.get_indexes(table)} for table in tables}
    foreign_keys = {table: inspector.get_foreign_keys(table) for table in tables}
    columns = {
        table: {column["name"]: column["type"].__class__.__name__ for column in inspector.get_columns(table)}
        for table in tables
    }
    return {
        "tables": set(tables),
        "indexes": indexes,
        "foreign_keys": foreign_keys,
        "columns": columns,
    }


async def _schema_snapshot(database_url: str):
    engine = create_async_engine(database_url, future=True, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            return await connection.run_sync(_collect_schema)
    finally:
        await engine.dispose()


def _assert_schema(snapshot) -> None:
    assert EXPECTED_TABLES.issubset(snapshot["tables"])
    assert snapshot["columns"]["events"]["event_id"] == "UUID"
    assert snapshot["columns"]["events"]["raw_payload"] == "JSONB"
    assert snapshot["columns"]["alerts"]["metadata"] == "JSONB"
    assert snapshot["columns"]["cameras"]["metadata"] == "JSONB"
    assert snapshot["columns"]["analytics_results"]["metadata"] == "JSONB"
    assert snapshot["columns"]["zones"]["polygon_points_json"] == "JSONB"

    for table, expected_indexes in EXPECTED_INDEXES.items():
        assert expected_indexes.issubset(snapshot["indexes"][table])

    assert any(
        foreign_key["referred_table"] == "cameras" and foreign_key["constrained_columns"] == ["camera_id"]
        for foreign_key in snapshot["foreign_keys"]["events"]
    )
    assert any(
        foreign_key["referred_table"] == "events" and foreign_key["constrained_columns"] == ["event_id"]
        for foreign_key in snapshot["foreign_keys"]["alerts"]
    )
    assert any(
        foreign_key["referred_table"] == "alerts" and foreign_key["constrained_columns"] == ["alert_id"]
        for foreign_key in snapshot["foreign_keys"]["clips"]
    )
    assert any(
        foreign_key["referred_table"] == "events" and foreign_key["constrained_columns"] == ["event_id"]
        for foreign_key in snapshot["foreign_keys"]["analytics_results"]
    )


@pytest.mark.asyncio
async def test_alembic_upgrade_downgrade_upgrade_chain(monkeypatch) -> None:
    database_url = _database_url()
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    alembic_cfg = _alembic_config(database_url)

    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
    upgraded_snapshot = await _schema_snapshot(database_url)
    _assert_schema(upgraded_snapshot)

    await asyncio.to_thread(command.downgrade, alembic_cfg, "base")
    downgraded_snapshot = await _schema_snapshot(database_url)
    assert EXPECTED_TABLES.isdisjoint(downgraded_snapshot["tables"])

    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
    reupgraded_snapshot = await _schema_snapshot(database_url)
    _assert_schema(reupgraded_snapshot)
