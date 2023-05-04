import asyncio
import logging
from src.docker_manager.docker_api import DockerApi
from src.instance_manager.instance.instance_service import InstanceService
from config import (
    parse_config,
    get_environment_type,
    DATABASE_SECTION,
    DATABASE_URL_KEY,
)
from instance_manager.instance.instance_dao import InstanceDAOFactory
from instance_manager.instance.instance_service import InstanceService
from psycopg_pool import ConnectionPool


logger = logging.getLogger(__name__)


class InstanceDeletionScheduler:
    def __init__(self, instance_service: InstanceService, docker_api: DockerApi):
        self.instance_service = instance_service
        self.docker_api = docker_api
        self.scheduler_interval = 60

    async def run(self):
        while True:
            try:
                logger.info("Scheduler Iteration...")
                if self.docker_api.is_healthy():
                    logger.info("Removing instances...")
                    await self.instance_service.remove_instances()
            except Exception as e:
                logger.error(f"Error while removing instances: {e}")
            finally:
                logger.info("Next deletion scheduled after 60 seconds...")
                await asyncio.sleep(self.scheduler_interval)


async def main():
    logging.basicConfig(level=logging.INFO)
    cfg = parse_config(get_environment_type())
    db_url = cfg.get(DATABASE_SECTION, DATABASE_URL_KEY)

    with ConnectionPool(db_url) as connection_manager:
        instance_service = InstanceService(
            connection_manager,
            InstanceDAOFactory(),
            DockerApi(None)
        )
        scheduler = InstanceDeletionScheduler(
            instance_service, DockerApi(None)
        )
        await scheduler.run()


if __name__ == "__main__":
    asyncio.run(main())
