from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """Dialect-aware UUID type that stores UUIDs on PostgreSQL and text elsewhere."""

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: UUID | str | None, dialect) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: str | UUID | None, dialect) -> UUID | None:
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        return UUID(str(value))


class JSONBType(TypeDecorator):
    """Dialect-aware JSON type with PostgreSQL JSONB and SQLite text fallback."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGJSONB(astext_type=Text()))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def process_result_value(self, value: Any, dialect) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)
