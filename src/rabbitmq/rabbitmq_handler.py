import aio_pika
import logging
import json

from instance_manager.instance.instance_service import InstanceService
from src.instance_manager.message import Message, Action
from src.instance_manager.message.message_handler import message_handler

logging.basicConfig(level=logging.DEBUG)


async def process_message(
            channel, message, instance_service: InstanceService
        ) -> None:
    """
    Callback function for processing received messages from RabbitMQ.
    """
    message_body = message.body.decode()
    message_dict = json.loads(message_body)

    messageDTO = Message(
        action=Action[message_dict["action"]],
        device_id=message_dict["device_id"]
    )

    logging.info(f"Received message: {messageDTO}")

    await message_handler(messageDTO, instance_service)

    return


async def start_rabbitmq_consumer(
            consumer_info, instance_service: InstanceService
        ) -> None:
    """
    Start RabbitMQ consumer.
    """

    logging.info("Starting RabbitMQ consumer...")
    logging.debug(f"Connection info: {consumer_info}")

    rbt_user = consumer_info["user"]
    rbt_pass = consumer_info["password"]
    rbt_host = consumer_info["host"]
    rbt_port = consumer_info["port"]

    rabbit_url = f"amqp://{rbt_user}:{rbt_pass}@{rbt_host}:{rbt_port}/"

    logging.debug(f"RabbitMQ Built URL: {rabbit_url}")

    connection = await aio_pika.connect_robust(rabbit_url)

    async with connection:
        # Creating channel
        channel = await connection.channel()

        await channel.set_qos(prefetch_count=4)  # 4 messages in advance

        queue_name = consumer_info["queue"]

        # Declaring queue
        queue = await channel.declare_queue(queue_name, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await process_message(channel, message, instance_service)
