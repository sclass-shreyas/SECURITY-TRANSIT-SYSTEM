from __future__ import annotations

import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app import create_app
from backend.config import Settings
from backend.models import AnalyticsResult, Alert, Camera, Clip, Event, Zone


@dataclass
class InMemoryStore:
    cameras: list[Camera] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)
    zones: list[Zone] = field(default_factory=list)
    clips: list[Clip] = field(default_factory=list)
    analytics_results: list[AnalyticsResult] = field(default_factory=list)
    clip_seq: int = 1
    zone_seq: int = 1


class FakeResult:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def scalars(self) -> "FakeResult":
        return self

    def all(self) -> list[Any]:
        return list(self._items)

    def scalar_one_or_none(self) -> Any | None:
        return self._items[0] if self._items else None

    def scalar_one(self) -> Any:
        if len(self._items) != 1:
            raise ValueError("Expected exactly one scalar result")
        return self._items[0]


class FakeTransaction:
    def __init__(self, session: "FakeAsyncSession") -> None:
        self.session = session

    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            await self.session.commit()
        else:
            await self.session.rollback()


class FakeAsyncSession:
    def __init__(self, store: InMemoryStore, settings: Settings) -> None:
        self.store = store
        self.info: dict[str, Any] = {"settings": settings}
        self._pending: list[Any] = []

    async def __aenter__(self) -> "FakeAsyncSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self._pending.clear()

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self)

    def add(self, obj: Any) -> None:
        self._pending.append(obj)

    async def flush(self) -> None:
        for obj in self._pending:
            self._assign_identity(obj)

    async def commit(self) -> None:
        await self.flush()
        for obj in self._pending:
            self._persist(obj)
        self._pending.clear()

    async def rollback(self) -> None:
        self._pending.clear()

    async def refresh(self, _obj: Any) -> None:
        return None

    async def delete(self, obj: Any) -> None:
        self._remove(obj)

    async def execute(self, query: Any) -> FakeResult:
        if str(query).strip().lower().startswith("select 1"):
            return FakeResult([1])

        entity = self._selected_entity(query)
        items = self._items_for_entity(entity)

        for criterion in getattr(query, "_where_criteria", ()):
            items = [item for item in items if self._matches(item, criterion)]

        order_by = getattr(query, "_order_by_clauses", ())
        if order_by:
            for clause in reversed(order_by):
                key = getattr(clause.element, "key", None)
                reverse = getattr(clause.modifier, "__name__", "") == "desc_op"
                if key:
                    items.sort(key=lambda item: getattr(item, key), reverse=reverse)

        limit_clause = getattr(query, "_limit_clause", None)
        if limit_clause is not None and getattr(limit_clause, "value", None) is not None:
            items = items[: int(limit_clause.value)]

        return FakeResult(items)

    async def scalar(self, query: Any) -> int:
        if str(query).strip().lower().startswith("select 1"):
            return 1

        entity = self._selected_entity(query)
        items = self._items_for_entity(entity)

        for criterion in getattr(query, "_where_criteria", ()):
            items = [item for item in items if self._matches(item, criterion)]

        return len(items)

    def _selected_entity(self, query: Any) -> Any:
        descriptions = getattr(query, "column_descriptions", [])
        if not descriptions:
            return None
        return descriptions[0].get("entity")

    def _items_for_entity(self, entity: Any) -> list[Any]:
        if entity is None:
            return []
        entity_name = entity.__name__
        if entity_name == "Camera":
            return list(self.store.cameras)
        if entity_name == "Event":
            return list(self.store.events)
        if entity_name == "Alert":
            return list(self.store.alerts)
        if entity_name == "Zone":
            return list(self.store.zones)
        if entity_name == "Clip":
            return list(self.store.clips)
        if entity_name == "AnalyticsResult":
            return list(self.store.analytics_results)
        return []

    def _persist(self, obj: Any) -> None:
        entity_name = obj.__class__.__name__
        if entity_name == "Camera":
            self._upsert(self.store.cameras, obj, "camera_id")
        elif entity_name == "Event":
            self._upsert(self.store.events, obj, "event_id")
        elif entity_name == "Alert":
            self._upsert(self.store.alerts, obj, "alert_id")
        elif entity_name == "Zone":
            self._upsert(self.store.zones, obj, "id")
        elif entity_name == "Clip":
            self._upsert(self.store.clips, obj, "id")
        elif entity_name == "AnalyticsResult":
            self._upsert(self.store.analytics_results, obj, "result_id")

    def _assign_identity(self, obj: Any) -> None:
        entity_name = obj.__class__.__name__
        if entity_name == "Zone" and getattr(obj, "id", None) is None:
            obj.id = self.store.zone_seq
            self.store.zone_seq += 1
        elif entity_name == "Clip" and getattr(obj, "id", None) is None:
            obj.id = self.store.clip_seq
            self.store.clip_seq += 1

    def _remove(self, obj: Any) -> None:
        entity_name = obj.__class__.__name__
        if entity_name == "Camera":
            self.store.cameras = [item for item in self.store.cameras if item.camera_id != obj.camera_id]
        elif entity_name == "Event":
            self.store.events = [item for item in self.store.events if item.event_id != obj.event_id]
        elif entity_name == "Alert":
            self.store.alerts = [item for item in self.store.alerts if item.alert_id != obj.alert_id]
        elif entity_name == "Zone":
            self.store.zones = [item for item in self.store.zones if item.id != obj.id]
        elif entity_name == "Clip":
            self.store.clips = [item for item in self.store.clips if item.id != obj.id]
        elif entity_name == "AnalyticsResult":
            self.store.analytics_results = [item for item in self.store.analytics_results if item.result_id != obj.result_id]

    def _upsert(self, bucket: list[Any], obj: Any, key: str) -> None:
        for index, existing in enumerate(bucket):
            if getattr(existing, key) == getattr(obj, key):
                bucket[index] = obj
                return
        bucket.append(obj)

    def _matches(self, obj: Any, criterion: Any) -> bool:
        left = getattr(criterion, "left", None)
        right = getattr(criterion, "right", None)
        operator_fn = getattr(criterion, "operator", None)
        key = getattr(left, "key", None)
        value = getattr(right, "value", None)

        if key is None:
            return True

        current = getattr(obj, key)
        if isinstance(current, UUID) and isinstance(value, str):
            try:
                value = UUID(value)
            except ValueError:
                return False
        if operator_fn is operator.eq:
            return current == value
        if operator_fn is operator.ge:
            return current >= value
        if operator_fn is operator.gt:
            return current > value
        if operator_fn is operator.le:
            return current <= value
        if operator_fn is operator.lt:
            return current < value
        return True


class FakeSessionFactory:
    def __init__(self, store: InMemoryStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings

    def __call__(self) -> FakeAsyncSession:
        return FakeAsyncSession(self.store, self.settings)


@pytest.fixture()
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture()
def app(tmp_path: Path, store: InMemoryStore):
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/smart_transit",
        CLIPS_BASE_DIR=str(tmp_path / "clips"),
    )
    application = create_app(settings)
    application.state.settings = settings
    application.state.sessionmaker = FakeSessionFactory(store, settings)
    application.state.ready = True
    return application


@pytest_asyncio.fixture()
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client
