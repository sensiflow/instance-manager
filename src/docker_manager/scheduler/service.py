import asyncio
import logging
from dataclasses import asdict
from datetime import datetime

from psycopg_pool import AsyncConnectionPool

from database.transaction import transaction
from docker_manager.docker_api import DockerApi

from instance_manager.instance.instance import InstanceStatus, Instance
from instance_manager.instance.instance_dao import InstanceDAOFactory
from instance_manager.instance.instance_service import InstanceService
from instance_manager.message import Action
from instance_manager.message.response_status import ResponseStatus
from rabbitmq.message_handler import MessageHandler

from src.docker_manager.exceptions import ContainerNotFound
from src.instance_manager.message import InputMessage
from src.instance_manager.message.output_message import CtlAcknowledgeMessage
from src.rabbitmq.rabbitmq_client import AsyncRabbitMQClient


class SchedulerService:

    def __init__(
            self,
            async_conn_manager: AsyncConnectionPool,
            instance_dao_factory: InstanceDAOFactory,
            docker_api: DockerApi,
            rabbitmq_client:  AsyncRabbitMQClient,
            queue_to_push_messages: str
    ):
        self.async_conn_manager = async_conn_manager
        self.instance_dao_factory = instance_dao_factory
        self.docker_api = docker_api
        self.rabbitmq_client = rabbitmq_client
        self.status_queue_name = queue_to_push_messages
        self.queue = "instance_ack_exchange"

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

    async def __make_instance_consistent(self, instance):
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

        except ContainerNotFound as e:
            logging.info("Container not found, getting instance...")
            await self.__remove_instance(instance.id)
        except Exception as e:
            logging.error(type(e))
            raise e

    async def __instance_exited(self, instance_id: int):
        """
            Updates the instance status in the database.
            Parameters:
                instance_id: The id of the instance to update.
        """
        async with transaction(self.async_conn_manager) as cursor:
            instance_dao = self.instance_dao_factory.create_dao(cursor)
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
            logging.info("Instance updated")
            message_dto = CtlAcknowledgeMessage(
                code=3000,
                device_id=instance_id,
                action= "Update", #n e uma ação sobre um container, TODO
                message=f"Instance with id:{instance_id} was inconsistent and was updated."
            )

            await self.rabbitmq_client.send_message(
                self.status_queue_name,
                self.queue,
                message=asdict(message_dto)
            )

    async def __remove_instance(self, instance_id: int):
        async with transaction(self.async_conn_manager) as cursor:
            logging.info("Container not found")
            instance_dao = self.instance_dao_factory.create_dao(cursor)
            await instance_dao.delete_instance(instance_id)

            logging.info("Instance deleted")
            #TODO codigo e action
            message_dto = CtlAcknowledgeMessage(
                code=3000,
                device_id=instance_id,
                action="Remove",
                message=f"Instance with id: {instance_id} was inconsistent and was removed."
            )

            await self.rabbitmq_client.send_message(
                self.status_queue_name,
                self.queue,
                message=asdict(message_dto)
            )