from src.instance_manager.message import InputMessage, Action
from src.instance_manager.instance.instance_service import InstanceService
from src.instance_manager.instance.instance import Instance, InstanceStatus
from datetime import datetime
import logging


async def create_instance(message: InputMessage, service: InstanceService):
    """
        Creates an instance in the database and starts a docker container.
        Parameters:
            message: The message that was received from the queue.
            service: The instance service.
        Throws:
            InstanceAlreadyExists: If the instance was already created.
            InternalError
    """
    start_time = datetime.utcnow()
    instance = Instance(
        id=message.device_id,
        status=InstanceStatus.ACTIVE,
        created_at=start_time,
        updated_at=start_time
    )
    logging.info(f"Creating instance {instance}")
    await service.start_instance(instance, message.device_stream_url)


async def stop_instance(message: InputMessage, service: InstanceService):
    """
        Updates the instance status in the database
        and stops the docker container.
        Parameters:
            message: The message that was received from the queue.
            service: The instance service.
        Throws:
            InstanceNotFound: If the instance does not exist.
            InternalError
    """
    logging.info(f"Stopping instance {message.device_id}")
    await service.stop_instance(message.device_id)


async def pause_instance(message: InputMessage, service: InstanceService):
    """
        Updates the instance status in the database
        and pauses the docker container.
        Parameters:
            message: The message that was received from the queue.
            service: The instance service.
        Throws:
            InstanceNotFound: If the instance does not exist.
            InternalError
    """
    logging.info(f"Pausing instance {message.device_id}")
    await service.pause_instance(message.device_id)


async def remove_instance(message: InputMessage, service: InstanceService):
    """
        Remove instance from the database and docker.
        Parameters:
            message: The message that was received from the queue.
            service: The instance service.
        Throws:
            InstanceNotFound: If the instance does not exist.
            InternalError
    """
    logging.info(f"Removing instance {message.device_id}")
    await service.remove_instance(message.device_id)

dispatcher = {
    Action.START: create_instance,
    Action.STOP: stop_instance,
    Action.PAUSE: pause_instance,
    Action.REMOVE: remove_instance
}


async def message_dispatcher(message: InputMessage, service: InstanceService):
    await dispatcher[message.action](message, service)
