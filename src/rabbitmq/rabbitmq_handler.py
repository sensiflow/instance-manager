import aio_pika
import logging

logger = logging.Logger(__name__)


async def process_message(channel, message) -> None:
    """
    Callback function for processing received messages from RabbitMQ.
    """
    # Your message processing logic here

    logger.info(f"Received message: {message} from channel: {channel}")

    return 


async def start_rabbitmq_consumer(consumer_info) -> None:
    """
    Start RabbitMQ consumer.
    """

    logger.info("Starting RabbitMQ consumer...")
    logger.debug(f"Connection info: {consumer_info}")

    rbt_user = consumer_info["user"]
    rbt_pass = consumer_info["password"]
    rbt_host = consumer_info["host"]
    rbt_port = consumer_info["port"]

    rabbit_url = f"amqp://{rbt_user}:{rbt_pass}@{rbt_host}:{rbt_port}/"

    logger.debug(f"RabbitMQ Built URL: {rabbit_url}")

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
                    await process_message(channel, message)
