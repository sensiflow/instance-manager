import aio_pika
import logging
import json

from aio_pika import IncomingMessage
from aio_pika.pool import Pool
from instance_manager.instance.instance_service import InstanceService
from instance_manager.message import Message, Action
from instance_manager.message.message_handler import message_handler


logger = logging.getLogger(__name__)


async def process_message(
            channel, message: IncomingMessage, instance_service: InstanceService
        ) -> None:
    """
    Callback function for processing received messages from RabbitMQ.
    """
    message_body = message.body.decode()
    message_dict = json.loads(message_body)

    message_dto = Message(
        action=Action[message_dict["action"]],
        device_id=message_dict["device_id"],
        device_stream_url=message_dict.get("device_stream_url")
    )

    logger.info(f"Received message: {message_dto}")

    try:
        await message_handler(message_dto, instance_service)
    except Exception as e:
        logger.error(f"Error while handling message: {e}")
        raise e

    return




async def start_rabbitmq_consumer_pool(
            consumer_info, instance_service: InstanceService, event_loop
        ) -> None:
    """
    Start RabbitMQ consumer.
    """

    logger.info("Starting RabbitMQ consumer...")
    logger.debug(f"Connection info: {consumer_info}")

    rbt_user = consumer_info["user"]
    rbt_pass = consumer_info["password"]
    rbt_host = consumer_info["host"]
    rbt_port = consumer_info["port"]
    rbt_queue_name = consumer_info["queue"]

    rabbit_url = f"amqp://{rbt_user}:{rbt_pass}@{rbt_host}:{rbt_port}/"
    logger.debug(f"RabbitMQ Built URL: {rabbit_url}")

    async def get_connection():
        return await aio_pika.connect_robust(rabbit_url)
    
    connection_pool = Pool(get_connection, max_size=2, loop=event_loop)

    async def get_channel() -> aio_pika.Channel:
        async with connection_pool.acquire() as connection:
            return await connection.channel()

    channel_pool = Pool(get_channel, max_size=10, loop=event_loop)

    async def consume() -> None:
        async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
            await channel.set_qos(10)

            queue = await channel.declare_queue(
                rbt_queue_name, durable=True, auto_delete=False,
            )

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        await process_message(channel, message, instance_service)
    
    async with connection_pool, channel_pool:
        task = event_loop.create_task(consume())
        await task
    
   

    
        
