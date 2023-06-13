import asyncio
import logging
from datetime import datetime

from docker.errors import DockerException, APIError
from psycopg_pool import AsyncConnectionPool

from database.transaction import transaction
from docker_manager.docker_api import DockerApi
from docker_manager.exceptions import ContainerNotFound
from instance_manager.instance.instance import InstanceStatus, Instance
from instance_manager.instance.instance_dao import InstanceDAOFactory
from instance_manager.instance.instance_service import InstanceService
from instance_manager.message import Action
from instance_manager.message.response_status import ResponseStatus
from rabbitmq.message_handler import MessageHandler


class SchedulerService:

    def __init__(
            self,
            async_conn_manager: AsyncConnectionPool,
            instance_dao_factory: InstanceDAOFactory,
            docker_api: DockerApi,
            messageHandler: MessageHandler
    ):
        self.async_conn_manager = async_conn_manager
        self.instance_dao_factory = instance_dao_factory
        self.docker_api = docker_api
        self.messageHandler = messageHandler


    async def check_every_container_consistency(self):
        """
            Checks if every container is running and if it is consistent with the database.
        """

        async with transaction(self.async_conn_manager) as cursor:
            try:
                instance_dao = self.instance_dao_factory.create_dao(cursor)
                instances = await instance_dao.get_all_instances()

                await asyncio.gather(
                    *[
                        self.__make_instance_consistent(instance) for instance in instances
                    ]
                )

            except Exception as e:
                logging.error("Error while checking every container consistency: %s", e)
                raise e

    async def __make_instance_consistent(self,instance):
        """
            Proves if the instance is consistent with the database.
            Parameters:
                instance: The instance to prove consistency.
        """
        docker_id = InstanceService.build_instance_name(instance.id)

        try:
            container = await self.docker_api.get_container(docker_id)

            if container.status == "exited":
                if instance.status.value != InstanceStatus.INACTIVE.value:
                    await self.__instance_exited(instance.id)

        except Exception as e:
            logging.error("Error while checking instance consistency: %s", e)
            raise e


    async def __instance_exited(self, instance_id: int):
        """
            Updates the instance status in the database.
            Parameters:
                instance_id: The id of the instance to update.
        """
        async with transaction(self.async_conn_manager) as cursor:
            instance_dao = self.dao_factory.create_dao(cursor)
            instance = await instance_dao.get_instance(instance_id)
            if instance.status.value != InstanceStatus.INACTIVE.value:
                await instance_dao.update_instance(
                    Instance(
                        id=instance_id,
                        status=InstanceStatus.INACTIVE,
                        created_at=instance.created_at,
                        updated_at=datetime.utcnow()
                    )
                )
            await self.messageHandler.send(
                f"{instance_id} was inconsistent and was set to inactive.",
                ResponseStatus.InconsistentContainerState,
                instance_id,
                action=Action.UPDATE
            )
        #TEST
