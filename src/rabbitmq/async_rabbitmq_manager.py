import asyncio
import aio_pika
from aio_pika.pool import Pool


class AsyncRabbitMQManager:
    def __init__(
            self, rabbit_url,
            connection_pool_size=1,
            channel_pool_size=5
            ):
        self.event_loop = asyncio.get_event_loop()
        self.connection_pool = Pool(
            self.get_connection,
            max_size=connection_pool_size,
            loop=self.event_loop
        )
        self.channel_pool = Pool(
            self.get_channel,
            max_size=channel_pool_size,
            loop=self.event_loop
        )
        self.rabbit_url = rabbit_url

    async def get_connection(self):
        """
            Gets a connection from the connection pool
        """
        return await aio_pika.connect_robust(self.rabbit_url)

    async def get_channel(self) -> aio_pika.Channel:
        """
            Gets a channel from the channel pool
        """
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()
