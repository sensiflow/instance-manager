import asyncio
import logging
import sys
from psycopg_pool import AsyncConnectionPool

from image_processor.processed_stream.processed_stream_dao import ProcessedStreamDAOFactory
from src.config.app import get_app_config
from src.docker_manager.docker_api import DockerApi
from src.docker_manager.docker_init import ProcessingMode
from src.docker_manager.scheduler.service import SchedulerService
from src.instance_manager.instance.exceptions import InternalError
from src.instance_manager.instance.instance_service import InstanceService
from src.instance_manager.instance.instance_dao import InstanceDAOFactory
from src.config import (
    parse_config,
    get_environment_type,
)
from src.rabbitmq.async_rabbitmq_manager import AsyncRabbitMQManager
from src.rabbitmq.rabbitmq_client import AsyncRabbitMQClient

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(
            self,
            instance_service: InstanceService,
            scheduler_service: SchedulerService,
            docker_api: DockerApi
    ):
        self.instance_service = instance_service
        self.scheduler_service = scheduler_service
        self.docker_api = docker_api
        self.inactive_check_interval = 60
        self.consistency_check_interval = 3

    async def run_instance_service(self):
        while True:
            await self.instance_service.manage_not_active_instances()
            await asyncio.sleep(self.inactive_check_interval)

    async def run_scheduler_service(self):
        while True:
            await self.scheduler_service.check_every_container_consistency()
            await asyncio.sleep(self.consistency_check_interval)

    async def run(self):
            try:
                await self.docker_api.check_health()

                instance_service_task = asyncio.create_task(self.run_instance_service())
                scheduler_service_task = asyncio.create_task(self.run_scheduler_service())
                await asyncio.gather(instance_service_task, scheduler_service_task)
            except InternalError:
                logger.exception(
                    "Internal error occurred while running scheduler")
            finally:
                logger.info("Shutting down scheduler")


async def main():
    logging.basicConfig(level=logging.INFO)
    cfg = parse_config(get_environment_type())
    app_cfg = get_app_config(cfg)

    database_cfg = app_cfg["database"]
    database_url = (
        f"postgres://{database_cfg['user']}:{database_cfg['password']}"
        f"@{database_cfg['host']}:{database_cfg['port']}"
    )

    rabbit_cfg = app_cfg["rabbitmq"]

    rbt_user = rabbit_cfg["user"]
    rbt_pass = rabbit_cfg["password"]
    rbt_host = rabbit_cfg["host"]
    rbt_port = rabbit_cfg["port"]
    rbt_scheduler_notification_queue_name = rabbit_cfg["instance_scheduler_notification"]

    rabbit_url = f"amqp://{rbt_user}:{rbt_pass}@{rbt_host}:{rbt_port}/"
    logger.debug(f"RabbitMQ Built URL: {rabbit_url}")

    async with AsyncConnectionPool(database_url) as connection_manager:
        docker_api = DockerApi(None, ProcessingMode.CPU)

        instance_service = InstanceService(
            connection_manager,
            InstanceDAOFactory(),
            ProcessedStreamDAOFactory(),
            docker_api
        )

        rb_connection_manager = AsyncRabbitMQManager(rabbit_url)
        rabbit_client = AsyncRabbitMQClient(rb_connection_manager)

        scheduler_service = SchedulerService(
            connection_manager,
            InstanceDAOFactory(),
            docker_api,
            rabbit_client,
            rbt_scheduler_notification_queue_name
        )

        scheduler = Scheduler(
            instance_service,
            scheduler_service,
            docker_api
        )
        await scheduler.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
