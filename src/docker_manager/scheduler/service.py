import asyncio
import logging
from dataclasses import asdict
from datetime import datetime
from enum import Enum, auto

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
from src.docker_manager.scheduler.scheduler_notification import SchedulerNotification
from src.docker_manager.scheduler.scheduler_notification_message import SchedulerNotificationMessage
from src.instance_manager.message import InputMessage
from src.instance_manager.message.output_message import CtlAcknowledgeMessage
from src.rabbitmq.rabbitmq_client import AsyncRabbitMQClient


class SchedulerService:

    def __init__(
            self,
            async_conn_manager: AsyncConnectionPool,
            instance_dao_factory: InstanceDAOFactory,
            docker_api: DockerApi,
            rabbitmq_client: AsyncRabbitMQClient,
            queue_to_push_messages: str
    ):
        self.async_conn_manager = async_conn_manager
        self.instance_dao_factory = instance_dao_factory
        self.docker_api = docker_api
        self.rabbitmq_client = rabbitmq_client
        self.status_queue_name = queue_to_push_messages
        self.instance_ack_exchange_name = "instance_ack_exchange"

    async def check_every_container_consistency(self):
        """
            Checks if every container is running and if it is consistent with the database.
        """

        async with transaction(self.async_conn_manager) as cursor:
            try:
                instance_dao = self.instance_dao_factory.create_dao(cursor)
                instances = await instance_dao.get_all_instances()
                await self.__make_instance_consistent(instances, cursor)

            except Exception as e:
                logging.error("Error while checking every container consistency: %s", e)

    async def __check_instance_status(self, instance, updated_instances, removed_instances, cursor):
        try:
            docker_id = InstanceService.build_instance_name(instance.id)
            container = await self.docker_api.get_container(docker_id)
            if container.status == "exited":
                if instance.status.value != InstanceStatus.INACTIVE.value:
                    await self.__instance_exited(instance.id, cursor)
                    updated_instances.append(instance.id)
        except ContainerNotFound as e:
            logging.info("Container not found, getting instance...")
            await self.__remove_instance(instance.id, cursor)
            removed_instances.append(instance.id)
        except Exception as e:
            logging.error(type(e))
            raise e

    async def __make_instance_consistent(self, instances, cursor):
        """
            Proves if the instance is consistent with the database.
            Parameters:
                instance: The instance to prove consistency.
        """
        updated_instances = []
        removed_instances = []
        coroutines = [self.__check_instance_status(
            instance,
            updated_instances,
            removed_instances,
            cursor
        ) for instance in instances]
        await asyncio.gather(*coroutines)

        logging.info(f"Updated Instances: ${updated_instances}")
        logging.info(f"Removed Instances: ${removed_instances}")

        if len(updated_instances) > 0:
            await self.__send_updated_message(updated_instances)
        if len(removed_instances) > 0:
            await self.__send_removed_message(removed_instances)

    async def __send_updated_message(self, updated_instances):
        message_dto = SchedulerNotificationMessage(
            code=3001,
            device_ids=updated_instances,
            action=SchedulerNotification.UPDATED_INSTANCE.name,
            message=f"Inconsistent instances were found and were updated."
        )

        await self.rabbitmq_client.send_message(
            self.status_queue_name,
            self.instance_ack_exchange_name,
            message=asdict(message_dto)
        )

    async def __send_removed_message(self, removed_instances):
        message_dto = SchedulerNotificationMessage(
            code=3002,
            device_ids=removed_instances,
            action=SchedulerNotification.REMOVED_INSTANCE.name,
            message=f"Inconsistent instances were found and were removed."
        )

        await self.rabbitmq_client.send_message(
            self.status_queue_name,
            self.instance_ack_exchange_name,
            message=asdict(message_dto)
        )

    async def __instance_exited(self, instance_id: int, cursor):
        """
            Updates the instance status in the database.
            Parameters:
                instance_id: The id of the instance to update.
        """
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

    async def __remove_instance(self, instance_id: int, cursor):
        logging.info("Container not found")
        instance_dao = self.instance_dao_factory.create_dao(cursor)
        await instance_dao.delete_instance(instance_id)

        logging.info("Instance deleted")
