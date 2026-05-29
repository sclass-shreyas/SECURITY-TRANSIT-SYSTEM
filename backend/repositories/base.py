from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model: type[T]
    identity_column = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    async def get_by_id(self, identifier) -> T | None:
        identity_column = self.__class__.identity_column
        if identity_column is None:
            raise NotImplementedError("identity_column must be set on repository subclasses")
        result = await self.session.execute(select(self.model).where(identity_column == identifier))
        return result.scalar_one_or_none()

    async def list(self, *, limit: int | None = None, order_by=None) -> list[T]:
        stmt = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
