from src.database.transaction import transaction
from src.instance_manager.exception import InstanceNotFound
from src.instance_manager.instance import Instance
from src.instance_manager.instance_dao import InstanceDAOFactory
from psycopg_pool import ConnectionPool


class InstanceService:
    def __init__(self, conn_manager: ConnectionPool,
                  dao_factory: InstanceDAOFactory):
        self.conn_manager = conn_manager
        self.dao_factory = dao_factory

    def get_instance(self, instance_id: str) -> Instance:
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            instance = instance_dao.get_instance(instance_id)
            if instance is None:
                raise InstanceNotFound(f"Instance with id {instance_id} not found")

            return instance

    def create_instance(self, instance: Instance) -> str:
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            return instance_dao.create_instance(instance)

    def update_instance(self, instance) -> bool:
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            updated_rows = instance_dao.update_instance(instance)

            if updated_rows == 0:
                raise InstanceNotFound(f"Instance with id {instance.id} not found")
            return updated_rows == 1

    def delete_instance(self, instance_id) -> bool:
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            deleted_rows = instance_dao.delete_instance(instance_id)

            if deleted_rows == 0:
                raise InstanceNotFound(f"Instance with id {instance_id} not found")

            return deleted_rows == 1
