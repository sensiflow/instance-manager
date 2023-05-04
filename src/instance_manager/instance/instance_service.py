import asyncio
from concurrent.futures import ThreadPoolExecutor
from database.transaction import transaction
from instance_manager.exception import InstanceNotFound
from instance_manager.instance.instance import Instance, InstanceStatus
from instance_manager.instance.instance_dao import InstanceDAOFactory
from docker_manager.docker_api import DockerApi
from psycopg_pool import ConnectionPool
from docker.errors import NotFound
import logging

logger = logging.getLogger(__name__)


class InstanceService:
    def __init__(
            self,
            conn_manager: ConnectionPool,
            dao_factory: InstanceDAOFactory,
            docker_api: DockerApi
    ):
        self.conn_manager = conn_manager
        self.dao_factory = dao_factory
        self.docker_api = docker_api

    async def get_instance(self, instance_id: int) -> Instance:
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            instance = instance_dao.get_instance(instance_id)
            if instance is None:
                raise InstanceNotFound(instance_id)

            return instance

    async def start_instance(
            self,
            instance: Instance,
            stream_url: str
    ) -> int:
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            instance_id = instance_dao.start_instance(instance)
            instance = instance_dao.get_instance(instance_id)
            if (instance is None):
                return instance.id
            logger.info(f"Created instance {instance_id}")
            await self.docker_api.run_container(self.build_instance_name(instance_id),
                                                "--source",
                                                stream_url)
            return instance_id

    async def update_instance(self, instance: Instance) -> bool:
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            updated_rows = instance_dao.update_instance(instance)

            if updated_rows == 0:
                raise InstanceNotFound(instance.id)
            return updated_rows == 1

    async def remove_instance(self, instance_id: int):
        with transaction(self.conn_manager) as cursor:

            instance_dao = self.dao_factory.create_dao(cursor)
            instance = instance_dao.get_instance(instance_id)

            if instance is None:
                logging.warning(
                    f"Instance {instance_id} not found, ignoring action")
                # success case
                return

            instance_dao.delete_instance(instance_id)

            await self.docker_api.remove_container(self.build_instance_name(instance_id))

    async def mark_instance_for_removal(self, instance_id: int):
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)

            instance = instance_dao.get_instance(instance_id)

            newInstance = Instance(
                id=instance.id,
                status=InstanceStatus[instance.status],
                created_at=instance.created_at,
                updated_at=instance.updated_at,
                scheduled_for_deletion=True
            )
            logger.info(f"Marking instance {instance_id} for removal")

            instance_dao.update_instance(newInstance)

    async def remove_instances(self):
        logger.info("Checking for instances to remove...")
        with transaction(self.conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            instances = instance_dao.get_marked_instances()
            for instance in instances:
                name = self.build_instance_name(instance.id)
                try:
                    await self.docker_api.remove_container(name, force=True)
                    instance_dao.delete_instance(instance.id)
                except NotFound as e:
                    logger.warning(f"Container {name} already removed")
                    instance_dao.delete_instance(instance.id)

    @staticmethod
    def build_instance_name(instance_id: int) -> str:
        return f"instance-{instance_id}"
