"""Tests for Firebase notifier."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from firebase_notifier import FirebaseNotifier


@pytest.mark.asyncio
@patch("firebase_notifier.Path.exists", return_value=True)
@patch("firebase_notifier.firebase_admin")
@patch("firebase_notifier.credentials")
@patch("firebase_notifier.messaging")
async def test_low_medium_skipped_when_high_only(
    mock_messaging: MagicMock,
    mock_credentials: MagicMock,
    mock_firebase_admin: MagicMock,
    _: MagicMock,
) -> None:
    mock_firebase_admin._apps = []
    notifier = FirebaseNotifier()
    await notifier.notify(
        {
            "alert_id": "a",
            "alert_type": "loitering",
            "severity": "low",
            "zone": "zone_1",
            "class_name": "person",
            "object_id": 1,
        }
    )
    mock_messaging.send.assert_not_called()


@pytest.mark.asyncio
@patch("firebase_notifier.Path.exists", return_value=True)
@patch("firebase_notifier.firebase_admin")
@patch("firebase_notifier.credentials")
@patch("firebase_notifier.messaging")
async def test_high_severity_triggers_send(
    mock_messaging: MagicMock,
    mock_credentials: MagicMock,
    mock_firebase_admin: MagicMock,
    _: MagicMock,
) -> None:
    mock_firebase_admin._apps = []
    notifier = FirebaseNotifier()
    await notifier.notify(
        {
            "alert_id": "a",
            "alert_type": "restricted_zone",
            "severity": "high",
            "zone": "zone_1",
            "class_name": "person",
            "object_id": 1,
        }
    )
    assert mock_messaging.send.called


@patch("firebase_notifier.Path.exists", return_value=False)
def test_missing_credentials_disables_notifier(_: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    notifier = FirebaseNotifier()
    assert notifier.is_enabled() is False
    assert "Notifications disabled" in caplog.text


@pytest.mark.asyncio
@patch("firebase_notifier.Path.exists", return_value=True)
@patch("firebase_notifier.firebase_admin")
@patch("firebase_notifier.credentials")
@patch("firebase_notifier.messaging")
async def test_send_failure_does_not_raise(
    mock_messaging: MagicMock,
    mock_credentials: MagicMock,
    mock_firebase_admin: MagicMock,
    _: MagicMock,
) -> None:
    mock_firebase_admin._apps = []
    mock_messaging.send.side_effect = RuntimeError("send failed")
    notifier = FirebaseNotifier()
    await notifier.notify(
        {
            "alert_id": "a",
            "alert_type": "restricted_zone",
            "severity": "high",
            "zone": "zone_1",
            "class_name": "person",
            "object_id": 1,
        }
    )
