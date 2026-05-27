"""Tests for alert processing engine."""

from __future__ import annotations

import uuid
from collections import deque
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

import config
from alert_engine import AlertEngine


def _raw(alert_type: str, object_id: int, metadata: dict) -> dict:
    return {
        "alert_type": alert_type,
        "object_id": object_id,
        "class_name": "person",
        "zone": "zone_1",
        "metadata": {"dwell_seconds": 0.0, "person_count": 0, "confidence": 0.0, "frame_id": 1, **metadata},
    }


@pytest.mark.asyncio
async def test_alert_id_is_uuid4() -> None:
    engine = AlertEngine()
    engine._save_clip = lambda alert_id, frames: "clips/a.avi"
    out = await engine.process([_raw("loitering", 1, {"dwell_seconds": 50.0})], {"frame_id": 1}, np.zeros((10, 10, 3), dtype=np.uint8))
    uuid.UUID(out[0]["alert_id"], version=4)


def test_severity_scoring_rules() -> None:
    engine = AlertEngine()
    assert engine._score_severity(_raw("loitering", 1, {"dwell_seconds": 10.0})) == "low"
    assert engine._score_severity(_raw("loitering", 1, {"dwell_seconds": 25.0})) == "medium"
    assert engine._score_severity(_raw("loitering", 1, {"dwell_seconds": 50.0})) == "high"
    assert engine._score_severity(_raw("crowd_surge", 1, {"person_count": 6})) == "low"
    assert engine._score_severity(_raw("crowd_surge", 1, {"person_count": 9})) == "medium"
    assert engine._score_severity(_raw("crowd_surge", 1, {"person_count": 12})) == "high"
    assert engine._score_severity(_raw("unattended_object", 1, {})) == "high"
    assert engine._score_severity(_raw("theft_gesture", 1, {"confidence": 0.5})) == "low"
    assert engine._score_severity(_raw("theft_gesture", 1, {"confidence": 0.7})) == "medium"
    assert engine._score_severity(_raw("theft_gesture", 1, {"confidence": 0.9})) == "high"
    assert engine._score_severity(_raw("restricted_zone", 1, {})) == "high"


@pytest.mark.asyncio
async def test_dedup_suppresses_within_window() -> None:
    engine = AlertEngine()
    engine._save_clip = lambda alert_id, frames: "clips/a.avi"
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    raw = _raw("restricted_zone", 2, {})
    first = await engine.process([raw], {"frame_id": 1}, frame)
    second = await engine.process([raw], {"frame_id": 2}, frame)
    assert len(first) == 1
    assert second == []


@pytest.mark.asyncio
async def test_dedup_allows_after_window() -> None:
    engine = AlertEngine()
    engine._save_clip = lambda alert_id, frames: "clips/a.avi"
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    raw = _raw("restricted_zone", 2, {})

    with patch("alert_engine.time.time", side_effect=[0.0, config.DEDUP_WINDOW_SECONDS + 1.0]):
        first = await engine.process([raw], {"frame_id": 1}, frame)
        second = await engine.process([raw], {"frame_id": 2}, frame)

    assert len(first) == 1
    assert len(second) == 1


@pytest.mark.asyncio
async def test_clip_path_set_after_processing() -> None:
    engine = AlertEngine()
    engine._save_clip = lambda alert_id, frames: "clips/clip.avi"
    out = await engine.process([_raw("unattended_object", 1, {})], {"frame_id": 1}, np.zeros((10, 10, 3), dtype=np.uint8))
    assert out[0]["clip_path"] == "clips/clip.avi"


def test_frame_buffer_updates() -> None:
    engine = AlertEngine()
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    engine.update_frame_buffer(frame)
    assert len(engine._frame_buffer) == 1
