import asyncio
from src.instance_manager.transaction import transaction
from instance_manager.instance.instance import Instance, InstanceStatus
from instance_manager.instance.instance_dao import InstanceDAOFactory
from docker_manager.docker_api import DockerApi
from docker.errors import APIError, DockerException
from psycopg_pool import AsyncConnectionPool
import logging
from src.instance_manager.instance.exceptions import InstanceAlreadyExists, InstanceNotFound, InternalError
from src.docker_manager.exceptions import ContainerNotFound
from datetime import datetime

logger = logging.getLogger(__name__)


class InstanceService:
    def __init__(
            self,
            async_conn_manager: AsyncConnectionPool,
            dao_factory: InstanceDAOFactory,
            docker_api: DockerApi
    ):
        self.async_conn_manager = async_conn_manager
        self.dao_factory = dao_factory
        self.docker_api = docker_api

    async def start_instance(
            self,
            instance: Instance,
            stream_url: str
    ) -> int:
        """
            Creates an instance in the database and starts a docker container.
            Parameters:
                instance: The instance to create.
                stream_url: The url of the stream to process in the container.
            Returns:
                The id of the created instance.
            Throws:
                InstanceAlreadyExists: If the instance was already created.
                InternalError
        """
        async with transaction(self.async_conn_manager) as cursor:
            try:
                instance_dao = self.dao_factory.create_dao(cursor)
                stored_instance = await instance_dao.get_instance(instance.id)
                
                if stored_instance is None:
                    instance_id = await self.__create_instance(
                        instance_dao,
                        instance,
                        stream_url
                    )
                else:
                    instance_id = await self.__start_instance(
                        instance_dao,
                        stored_instance
                    )
                return instance_id
            except (DockerException, APIError) as e:
                raise InternalError(e)
               
    async def __create_instance(
            self,
            instance_dao,
            instance,
            stream_url
    ):
        """
            Creates an instance in the database and a docker container.
        """
        instance_id = await instance_dao.create_instance(instance)

        logger.info(f"Created instance {instance_id}")
        
        await self.docker_api.run_container(
            self.build_instance_name(instance_id),
            "--source",
            stream_url
        )
        return instance_id

    async def __start_instance(
            self,
            instance_dao,
            stored_instance
    ):
        """
        Starts an instance in the database and starts/resumes a docker container.
        """
        if stored_instance.status.value == InstanceStatus.ACTIVE.value:
            raise InstanceAlreadyExists(stored_instance.id)

        instance = Instance(
            id=stored_instance.id,
            status=InstanceStatus.ACTIVE,
            created_at=stored_instance.created_at,
            updated_at=datetime.now()
        )

        if stored_instance.status.value == InstanceStatus.INACTIVE.value:
            logger.info(f"Starting instance {instance.id}")
            await instance_dao.update_instance(instance)
            await self.docker_api.start_container(
                self.build_instance_name(instance.id)
            )

        elif stored_instance.status.value == InstanceStatus.PAUSED.value:
            logger.info(f"Resuming instance {instance.id}")
            await instance_dao.update_instance(instance)
            await self.docker_api.unpause_container(
                self.build_instance_name(instance.id)
            )
        return stored_instance.id
            
    async def remove_instance(self, instance_id: int):
        """
            Removes an instance from the database and docker.
            Parameters:
                instance_id: The id of the instance to remove.
            Throws:
                InstanceNotFound: If the instance does not exist.
                InternalError
        """
        async with transaction(self.async_conn_manager) as cursor:
            try:
                instance_dao = self.dao_factory.create_dao(cursor)
                instance = await instance_dao.get_instance(instance_id)

                if instance is None:
                    logging.warning(
                        f"Instance {instance_id} not found, ignoring action")
                    raise InstanceNotFound(instance_id)
            
                await instance_dao.delete_instance(instance_id)

                await self.docker_api.remove_container(
                    self.build_instance_name(instance_id),
                    force=True
                )
            except ContainerNotFound:
                raise InstanceNotFound(instance_id)
            except (DockerException, APIError) as e:
                raise InternalError(e)
    
    async def stop_instance(self, instance_id: int):
        """
            Updates the instance status in the database
            and stops the docker container.
            Parameters:
                instance_id: The id of the instance to stop.
            Throws:
                InstanceNotFound: If the instance does not exist.
                InternalError
        """
        async with transaction(self.async_conn_manager) as cursor:
            try:
                instance_dao = self.dao_factory.create_dao(cursor)
                stored_instance = await instance_dao.get_instance(instance_id)
                if stored_instance.status.value == InstanceStatus.INACTIVE.value:
                    return

                instance = Instance(
                    id=stored_instance.id,
                    status=InstanceStatus.INACTIVE,
                    created_at=stored_instance.created_at,
                    updated_at=datetime.now()
                )
                await instance_dao.update_instance(instance)

                await self.docker_api.stop_container(
                    self.build_instance_name(instance_id)
                )
            except ContainerNotFound:
                raise InstanceNotFound(instance_id)
            except (DockerException, APIError) as e:
                raise InternalError(e)
  
    async def pause_instance(self, instance_id: int):
        """
            Updates the instance status in the database
            and pauses the docker container.
            Parameters:
                instance_id: The id of the instance to pause.
            Throws:
                InstanceNotFound: If the instance does not exist.
                InternalError
        """
        async with transaction(self.async_conn_manager) as cursor:
            try:
                instance_dao = self.dao_factory.create_dao(cursor)
                stored_instance = await instance_dao.get_instance(instance_id)
                if stored_instance.status.value == InstanceStatus.PAUSED.value:
                    return

                instance = Instance(
                    id=stored_instance.id,
                    status=InstanceStatus.PAUSED,
                    created_at=stored_instance.created_at,
                    updated_at=datetime.now()
                )
                await instance_dao.update_instance(instance)

                await self.docker_api.pause_container(
                    self.build_instance_name(instance_id)
                )
            except ContainerNotFound:
                raise InstanceNotFound(instance_id)
            except (DockerException, APIError) as e:
                raise InternalError(e)

    async def manage_not_active_instances(self):
        """
            Manages inactive instances.
            
        """
        async with transaction(self.async_conn_manager) as cursor:
            try:
                instance_dao = self.dao_factory.create_dao(cursor)
                instances = await instance_dao.get_not_active_instances()

                async def stop_container(instance):
                    instance_name = self.build_instance_name(instance.id)
                    self.docker_api.stop_container(instance_name)
                    instance_dao.update_instance(
                        Instance(
                            id=instance.id,
                            status=InstanceStatus.INACTIVE,
                            created_at=instance.created_at,
                            updated_at=datetime.now()
                        )
                    )

                async def remove_container(instance):
                    instance_name = self.build_instance_name(instance.id)
                    self.docker_api.remove_container(instance_name, force=True)
                    instance_dao.delete_instance(instance.id)

                paused_instances = [
                    stop_container(instance) for instance in instances
                    if instance.status.value == InstanceStatus.PAUSED.value
                ]

                stopped_instances = [
                    remove_container(instance) for instance in instances
                    if instance.status.value == InstanceStatus.INACTIVE.value
                ]

                stop_task = asyncio.gather(*paused_instances)
                remove_task = asyncio.gather(*stopped_instances)

                await asyncio.gather(stop_task, remove_task)
            except (DockerException, APIError) as e:
                raise InternalError(e)

    @staticmethod
    def build_instance_name(instance_id: int) -> str:
        return f"instance-{instance_id}"
    
    @staticmethod
    def get_instance_id_from_name(instance_name: str) -> int:
        return int(instance_name.split("-")[1])
