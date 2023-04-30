from docker.errors import APIError
from src.instance_manager.message import Message, Action
from src.instance_manager.instance.instance_service import InstanceService
from src.instance_manager.instance.instance import Instance, InstanceStatus
from datetime import datetime
import logging


async def start_instance(message: Message, service: InstanceService):
    start_time = datetime.now()
    instance_id = f"instance-{message.device_id}"
    instance = Instance(
        id=instance_id,
        device_id=message.device_id,
        status=InstanceStatus.ACTIVE,
        created_at=start_time,
        updated_at=start_time,
        scheduled_for_deletion=False
    )
    logging.info(f"Creating instance {instance}")
    await service.create_instance(instance, message.device_stream_url)


async def stop_instance(message: Message, service: InstanceService):
    pass


async def pause_instance(message: Message, service: InstanceService):
    pass


async def remove_instance(message: Message, service: InstanceService):
    instance_id = f"instance-{message.device_id}"
    try:
        logging.info(f"Removing instance {instance_id}")
        await service.remove_instance(instance_id)
    except APIError as e:
        logging.error(f"Error removing instance {instance_id}, Rescheduling...")
        await service.mark_instance_for_removal(
            instance_id,
            message.device_id,
        )


dispatcher = {
    Action.START: start_instance,
    Action.STOP: stop_instance,
    Action.PAUSE: pause_instance,
    Action.REMOVE: remove_instance
}


async def message_handler(message: Message, service: InstanceService):
    await dispatcher[message.action](message, service)
