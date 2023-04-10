from contextlib import contextmanager


@contextmanager
def transaction(connection_manager):
    """Context manager that simulates a transaction."""
    with connection_manager.connection() as conn:
        with conn.cursor() as cursor:
            yield cursor
