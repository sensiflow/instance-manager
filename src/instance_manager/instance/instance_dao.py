import datetime
from instance_manager.instance.instance import Instance
from typing import Optional

from src.instance_manager.instance.instance import InstanceStatus


class InstanceDAOFactory:
    """Factory for creating InstanceDAO objects."""

    def create_dao(self, cursor):
        return InstanceDAO(cursor)


class InstanceDAO:
    """CRUD Data Access Object for the Instance entity."""

    def __init__(self, cursor):
        self.cursor = cursor

    async def get_instance(self, instance_id: int) -> Optional[Instance]:
        query = """
        SELECT id, status, created_at, updated_at
        FROM instance
        WHERE id = %s
        """
        # Note the trailing comma to make it a tuple
        await self.cursor.execute(query, (instance_id,))
        row = await self.cursor.fetchone()
        if row is not None:
            instance_id, status, created_at, updated_at = row
            return Instance(
                id=instance_id,
                status=InstanceStatus[status],
                created_at=created_at,
                updated_at=updated_at
            )
        return None

    async def create_instance(self, instance: Instance) -> int:
        query = """
        INSERT INTO instance
        (id, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s) RETURNING id;
        """
        await self.cursor.execute(
            query,
            (
                instance.id,
                instance.status.name,
                instance.created_at,
                instance.updated_at,
            )
        )
        result = await self.cursor.fetchone()
        generated_id = result[0]
        return generated_id

    async def update_instance(self, instance: Instance) -> int:
        query = """
        UPDATE instance SET
        status = %s,
        created_at = %s, updated_at = %s
        WHERE id = %s
        """
        await self.cursor.execute(
            query,
            (
                instance.status.name,
                instance.created_at,
                instance.updated_at,
                instance.id,
            )
        )
        return self.cursor.rowcount

    async def delete_instance(self, instance_id: int) -> int:
        query = """
        DELETE FROM instance
        WHERE id = %s
        """
        await self.cursor.execute(query, (instance_id,))
        return self.cursor.rowcount

    async def get_old_inactive_instances(
            self, min_age_minutes: int = 5) -> list[Instance]:
        query = """
            SELECT id, status, created_at, updated_at
            FROM instance
            WHERE status != 'ACTIVE' AND updated_at < NOW() - %s
            LIMIT 100
        """
        interval = datetime.timedelta(minutes=min_age_minutes)
        await self.cursor.execute(query, (interval,))
        rows = await self.cursor.fetchall()
        instances = []
        for row in rows:
            instance_id, status, created_at, updated_at = row
            instances.append(
                Instance(
                    id=instance_id,
                    status=InstanceStatus[status],
                    created_at=created_at,
                    updated_at=updated_at
                )
            )
        return instances
