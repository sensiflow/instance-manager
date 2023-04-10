from src.instance_manager.instance import Instance
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
        SELECT id, name, description, status, created_at, updated_at
        FROM instance
        WHERE id = %s
        """
        # Note the trailing comma to make it a tuple
        self.cursor.execute(query, (instance_id,))
        row = self.cursor.fetchone()
        if row is not None:
            return Instance(*row)
        return None

    def create_instance(self, instance: Instance) -> int:
        query = """
        INSERT INTO instance
        (name, description, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """
        self.cursor.execute(
            query,
            (
                instance.name,
                instance.description,
                instance.status,
                instance.created_at,
                instance.updated_at,
            ),
        )
        result = self.cursor.fetchone()
        generated_id = result[0]
        return generated_id

    def update_instance(self, instance: Instance) -> int:
        query = """
        UPDATE instance SET
        name = %(name)s, description = %(description)s, status = %(status)s,
        created_at = %(created_at)s, updated_at = %(updated_at)s
        WHERE id = %(id)s
        """
        instance_dict = asdict(instance)

        self.cursor.execute(query, instance_dict)
        return self.cursor.rowcount

    def delete_instance(self, instance_id: int) -> int:
        query = """
        DELETE FROM instance
        WHERE id = %s
        """
        self.cursor.execute(query, (instance_id,))
        return self.cursor.rowcount
