"""Firebase push notification integration for high-severity alerts."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import config

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception:  # pragma: no cover
    firebase_admin = None  # type: ignore[assignment]
    credentials = None  # type: ignore[assignment]
    messaging = None  # type: ignore[assignment]


class FirebaseNotifier:
    """Send push notifications to Firebase Cloud Messaging."""

    def __init__(self) -> None:
        """Initialize Firebase SDK with service-account credentials."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._enabled = False

        if firebase_admin is None or credentials is None or messaging is None:
            self.logger.warning("firebase-admin is not installed. Notifications disabled.")
            return

        credentials_path = Path(__file__).resolve().parent / config.FIREBASE_CREDENTIALS_FILE
        if not credentials_path.exists():
            self.logger.warning(
                "Firebase credentials file not found at %s. Notifications disabled.",
                credentials_path,
            )
            return

        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(str(credentials_path))
                firebase_admin.initialize_app(cred)
            self._enabled = True
        except FileNotFoundError:
            self.logger.warning("Firebase credentials missing. Notifications disabled.")
            self._enabled = False
        except Exception as exc:  # pragma: no cover
            self.logger.warning("Failed to initialize Firebase: %s", exc)
            self._enabled = False

    def is_enabled(self) -> bool:
        """Return whether Firebase notifications are enabled."""
        return self._enabled

    async def notify(self, alert: dict[str, Any]) -> None:
        """Send alert notification to Firebase if policy and state allow.

        Args:
            alert: Finalized alert payload.
        """
        if not self._enabled or messaging is None:
            return

        severity = str(alert.get("severity", "")).lower()
        if config.FIREBASE_HIGH_SEVERITY_ONLY and severity != "high":
            return

        title = f"[{severity.upper()}] {str(alert.get('alert_type', '')).replace('_', ' ').title()}"
        body = (
            f"Zone: {alert.get('zone', '')} | "
            f"Object: {alert.get('class_name', 'unknown')} #{int(alert.get('object_id', -1))}"
        )
        data = {
            "alert_id": str(alert.get("alert_id", "")),
            "alert_type": str(alert.get("alert_type", "")),
        }

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            topic="smart-transit-alerts",
            data=data,
        )

        try:
            response = await asyncio.to_thread(messaging.send, message)
            self.logger.info("Firebase notification sent: %s", response)
        except Exception as exc:
            self.logger.warning("Firebase notification failed: %s", exc)
