from contextlib import asynccontextmanager
import psycopg
from src.instance_manager.instance.exceptions import InternalError


@asynccontextmanager
async def transaction(connection_manager):
    """Context manager that simulates a transaction."""
    try:
        async with connection_manager.connection() as conn:
            async with conn.cursor() as cursor:
                yield cursor
    except psycopg.Error as e:
        raise InternalError(e)
