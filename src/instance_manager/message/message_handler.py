from src.instance_manager.message import Message, Action
from src.instance_manager.instance.instance_service import InstanceService
from src.instance_manager.instance.instance import Instance, InstanceStatus
from datetime import datetime
import logging


async def start_instance(device_id: int, service: InstanceService):
    start_time = datetime.now()
    instance_id = f"instance-{device_id}"
    instance = Instance(
        id=instance_id,
        status=InstanceStatus.ACTIVE,
        created_at=start_time,
        updated_at=start_time
    )
    logging.info(f"Creating instance {instance}")
    service.create_instance(instance)


async def stop_instance(device_id: int, service: InstanceService):
    pass


async def pause_instance(device_id: int, service: InstanceService):
    pass


dispatcher = {
    Action.START: start_instance,
    Action.STOP: stop_instance,
    Action.PAUSE: pause_instance,
}


async def message_handler(message: Message, service: InstanceService):
    await dispatcher[message.action](message.device_id, service)
