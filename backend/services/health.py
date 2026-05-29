from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database.session import ping_database


async def database_is_ready(sessionmaker: async_sessionmaker[AsyncSession]) -> bool:
    try:
        return await ping_database(sessionmaker)
    except Exception:
        return False
