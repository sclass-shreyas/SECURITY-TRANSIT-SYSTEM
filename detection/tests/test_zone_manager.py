"""Tests for zone and dwell-time management."""

from __future__ import annotations

import json
from pathlib import Path

from zone_manager import ZoneManager


def _zones_payload(zone_name: str = "test_zone") -> dict:
    return {
        "zones": [
            {
                "id": "zone_001",
                "name": zone_name,
                "polygon": [[100, 100], [200, 100], [200, 200], [100, 200]],
                "restricted": False,
            }
        ]
    }


def test_point_inside_polygon_returns_correct_zone(tmp_path: Path) -> None:
    """Object centroid inside polygon should map to zone ID."""
    zones_file = tmp_path / "zones.json"
    zones_file.write_text(json.dumps(_zones_payload()), encoding="utf-8")

    zm = ZoneManager(str(zones_file))
    zones = zm.get_zones_for_object([120, 120, 180, 180])

    assert zones == ["zone_001"]


def test_point_outside_polygons_returns_empty_list(tmp_path: Path) -> None:
    """Object centroid outside all polygons should return empty zones list."""
    zones_file = tmp_path / "zones.json"
    zones_file.write_text(json.dumps(_zones_payload()), encoding="utf-8")

    zm = ZoneManager(str(zones_file))
    zones = zm.get_zones_for_object([300, 300, 350, 350])

    assert zones == []


def test_dwell_time_increases_over_time(tmp_path: Path) -> None:
    """Dwell time should monotonically increase while object stays in zone."""
    zones_file = tmp_path / "zones.json"
    zones_file.write_text(json.dumps(_zones_payload()), encoding="utf-8")

    zm = ZoneManager(str(zones_file))
    first = zm.update_dwell(1, ["zone_001"], 10.0)
    second = zm.update_dwell(1, ["zone_001"], 15.5)

    assert first["zone_001"] == 0.0
    assert second["zone_001"] == 5.5


def test_dwell_resets_when_object_leaves_zone(tmp_path: Path) -> None:
    """Dwell record should reset after object leaves and re-enters."""
    zones_file = tmp_path / "zones.json"
    zones_file.write_text(json.dumps(_zones_payload()), encoding="utf-8")

    zm = ZoneManager(str(zones_file))
    zm.update_dwell(1, ["zone_001"], 10.0)
    zm.update_dwell(1, [], 12.0)
    reentered = zm.update_dwell(1, ["zone_001"], 20.0)

    assert reentered["zone_001"] == 0.0


def test_reload_zones_rereads_file(tmp_path: Path) -> None:
    """reload_zones should refresh updated zone definitions from disk."""
    zones_file = tmp_path / "zones.json"
    zones_file.write_text(json.dumps(_zones_payload("old_name")), encoding="utf-8")

    zm = ZoneManager(str(zones_file))
    assert zm.zones["zone_001"]["name"] == "old_name"

    zones_file.write_text(json.dumps(_zones_payload("new_name")), encoding="utf-8")
    zm.reload_zones()

    assert zm.zones["zone_001"]["name"] == "new_name"


def test_clear_inactive_objects_removes_stale_dwell_state(tmp_path: Path) -> None:
    """Dwell state should be cleared once an object is no longer active."""
    zones_file = tmp_path / "zones.json"
    zones_file.write_text(json.dumps(_zones_payload()), encoding="utf-8")

    zm = ZoneManager(str(zones_file))
    zm.update_dwell(1, ["zone_001"], 10.0)
    zm.clear_inactive_objects(set())
    reentered = zm.update_dwell(1, ["zone_001"], 20.0)

    assert reentered["zone_001"] == 0.0
