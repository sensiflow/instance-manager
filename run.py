from docker_manager import docker_init
from src.config import (
    parse_config,
    get_environment_type,
    DATABASE_SECTION,
    DATABASE_URL_KEY,
    RABBITMQ_SECTION,
    RABBITMQ_HOST_KEY,
    RABBITMQ_PORT_KEY,
    RABBITMQ_USER_KEY,
    RABBITMQ_PASSWORD_KEY,
    RABBITMQ_QUEUE_KEY
)

from src.rabbitmq.rabbitmq_handler import start_rabbitmq_consumer
from instance_manager.instance.instance_dao import InstanceDAOFactory
from instance_manager.instance.instance_service import InstanceService
from src.docker_manager.docker_api import DockerApi
from psycopg_pool import ConnectionPool
import asyncio


async def main():
    cfg = parse_config(get_environment_type())
    db_url = cfg.get(DATABASE_SECTION, DATABASE_URL_KEY)

    rabbit_cfg = {
        "host": cfg.get(RABBITMQ_SECTION, RABBITMQ_HOST_KEY),
        "port": cfg.get(RABBITMQ_SECTION, RABBITMQ_PORT_KEY),
        "user": cfg.get(RABBITMQ_SECTION, RABBITMQ_USER_KEY),
        "password": cfg.get(RABBITMQ_SECTION, RABBITMQ_PASSWORD_KEY),
        "queue": cfg.get(RABBITMQ_SECTION, RABBITMQ_QUEUE_KEY),
    }

    docker_cfg = docker_init.get_docker_config(cfg)
    processing_mode = docker_cfg["processing_mode"]
    docker_init.docker_build_images(processing_mode)

    with ConnectionPool(db_url) as connection_manager:
        instance_service = InstanceService(
            connection_manager,
            InstanceDAOFactory(),
            DockerApi()
        )
        await start_rabbitmq_consumer(rabbit_cfg, instance_service)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
