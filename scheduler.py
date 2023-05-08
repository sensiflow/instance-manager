import asyncio
import logging
from src.config.app import get_app_config
from src.docker_manager.docker_api import DockerApi
from src.instance_manager.instance.exceptions import InternalError
from src.instance_manager.instance.instance_service import InstanceService
from config import (
    parse_config,
    get_environment_type,
)
from instance_manager.instance.instance_dao import InstanceDAOFactory
from instance_manager.instance.instance_service import InstanceService
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(
            self,
            instance_service: InstanceService,
            docker_api: DockerApi
            ):
        self.instance_service = instance_service
        self.docker_api = docker_api
        self.scheduler_interval = 60

    async def run(self):
        while True:
            try:
                await self.docker_api.check_health()
                await self.instance_service.manage_not_active_instances()
            except InternalError:
                logger.exception()
            finally:
                logger.info("Next iteration scheduled to run after 60 seconds")
                await asyncio.sleep(self.scheduler_interval)


async def main():
    logging.basicConfig(level=logging.INFO)
    cfg = parse_config(get_environment_type())
    app_cfg = get_app_config(cfg)
    
    database_cfg = app_cfg["database"]
    database_url = (
        f"postgres://{database_cfg['user']}:{database_cfg['password']}"
        f"@{database_cfg['host']}:{database_cfg['port']}"
    )

    with ConnectionPool(database_url) as connection_manager:
        instance_service = InstanceService(
            connection_manager,
            InstanceDAOFactory(),
            DockerApi(None)
        )
        scheduler = Scheduler(
            instance_service, DockerApi(None)
        )
        await scheduler.run()


if __name__ == "__main__":
    asyncio.run(main())
