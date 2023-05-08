import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import functools
import json
import logging
import aio_pika
from aio_pika.pool import Pool

logger = logging.getLogger(__name__)


class AsyncRabbitMQClient:
    def __init__(self, mq_manager, pool_workers=5):
        self.mq_manager = mq_manager
        self.consumer_pool = ThreadPoolExecutor(max_workers=pool_workers)
        self.loop = asyncio.get_event_loop()

    async def __consume(
            self,
            ctl_queue_name,
            async_message_handler
            ) -> None:
        """
            Consumes messages from the RabbitMQ queue.
            This method is called by the start_consumer method.
            The acknowledge is called manually after the message is processed.
            Parameters:
                ctl_queue_name (str): The name of the queue to consume from.
                async_message_handler (function): The function to call when a
                    message is received.
        """
        async with self.mq_manager.channel_pool.acquire() as channel:
            await channel.set_qos(10)  # quality of service for the channel

            queue = await channel.get_queue(ctl_queue_name, ensure=True)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    self.loop.run_in_executor(
                        self.consumer_pool,
                        functools.partial(
                            self.loop.create_task,
                            async_message_handler(message)
                        )
                    )

    async def start_consumer(
            self,
            ctl_queue_name,
            async_message_handler
            ):
        """
            Starts the RabbitMQ consumer.
            Parameters:
                ctl_queue_name (str): The name of the queue to consume from.
                async_message_handler (function): The function to call when a
                    message is received.
        """
        async with self.mq_manager.connection_pool, self.mq_manager.channel_pool:
            task = self.mq_manager.event_loop.create_task(
                self.__consume(ctl_queue_name, async_message_handler)
            )
            await task

    async def send_message(self, routing_key, exchange_name, message):
        """
            Sends a message to the RabbitMQ queue.
            Parameters:
                queue_name (str): The name of the queue to send the message to.
                message (dict): The message to send as a dictionary.
        """
        logger.info(f"Sending message {message} to {routing_key}...")
        async with self.mq_manager.channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange(
                exchange_name, durable=True
            )

            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key
            )
