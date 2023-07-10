import asyncio
import logging
from src.instance_manager.instance.instance_service import InstanceService
from src.rabbitmq.async_rabbitmq_manager import AsyncRabbitMQManager
from src.rabbitmq.message_handler import MessageHandler
from src.rabbitmq.rabbitmq_client import AsyncRabbitMQClient
import uuid

logger = logging.getLogger(__name__)


async def consume_control_messages(
        consumer_info, instance_service: InstanceService
) -> None:
    logger.info("Starting RabbitMQ consumer...")
    logger.debug(f"Connection info: {consumer_info}")

    rbt_user = consumer_info["user"]
    rbt_pass = consumer_info["password"]
    rbt_host = consumer_info["host"]
    rbt_port = consumer_info["port"]
    rbt_controller_queue_name = consumer_info["controller_queue"]
    rbt_ack_status_queue_name = consumer_info["ack_status_queue"]

    rabbit_url = f"amqp://{rbt_user}:{rbt_pass}@{rbt_host}:{rbt_port}/"
    logger.debug(f"RabbitMQ Built URL: {rabbit_url}")

    connection_manager = AsyncRabbitMQManager(rabbit_url)
    rabbit_client = AsyncRabbitMQClient(connection_manager)
    message_handler = MessageHandler(
        rbt_ack_status_queue_name,
        rbt_controller_queue_name,
        rabbit_client,
        instance_service,
    )

    receive_queue_name = str(uuid.uuid4())
    queue_name = await rabbit_client.register_queue(
        queue_name= receive_queue_name,
        exchange_name=f"{rbt_controller_queue_name}_exchange",
    )
    logger.info("Created dedicated queue...")

    await asyncio.gather(
        rabbit_client.start_consumer(
            ctl_queue_name=rbt_controller_queue_name,
            async_message_handler=message_handler.process_unique_messages
        ),
        rabbit_client.start_consumer(
            ctl_queue_name=queue_name,
            async_message_handler=message_handler.process_shared_messages
     )
    )
