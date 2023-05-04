from instance_manager.instance.instance import Instance
from typing import Optional
from dataclasses import asdict


class InstanceDAOFactory:
    """Factory for creating InstanceDAO objects."""

    def create_dao(self, cursor):
        return InstanceDAO(cursor)


class InstanceDAO:
    """CRUD Data Access Object for the Instance entity."""

    def __init__(self, cursor):
        self.cursor = cursor

    def get_instance(self, instance_id: int) -> Optional[Instance]:
        query = """
        SELECT id, status, created_at, updated_at, scheduled_for_deletion
        FROM instance
        WHERE id = %s
        """
        # Note the trailing comma to make it a tuple
        self.cursor.execute(query, (instance_id,))
        row = self.cursor.fetchone()
        if row is not None:
            return Instance(*row)
        return None

    def start_instance(self, instance: Instance) -> int:
        query = """
        INSERT INTO instance
        (id, status, created_at, updated_at, scheduled_for_deletion)
        VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """
        self.cursor.execute(
            query,
            (
                instance.id,
                instance.status.name,
                instance.created_at,
                instance.updated_at,
                instance.scheduled_for_deletion,
            )
        )
        result = self.cursor.fetchone()
        generated_id = result[0]
        return generated_id

    def update_instance(self, instance: Instance) -> int:
        query = """
        UPDATE instance SET
        status = %s,
        created_at = %s, updated_at = %s, scheduled_for_deletion = %s
        WHERE id = %s
        """
        self.cursor.execute(
            query,
            (
                instance.status.name,
                instance.created_at,
                instance.updated_at,
                instance.scheduled_for_deletion,
                instance.id,
            )
        )
        return self.cursor.rowcount

    def delete_instance(self, instance_id: int) -> int:
        query = """
        DELETE FROM instance
        WHERE id = %s
        """
        self.cursor.execute(query, (instance_id,))
        return self.cursor.rowcount

    def get_marked_instances(self):
        query = """
        SELECT id, status, created_at, updated_at, scheduled_for_deletion
        FROM instance
        WHERE scheduled_for_deletion = TRUE
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return [Instance(*row) for row in rows]
