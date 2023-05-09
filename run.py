from docker_manager import docker_init
from docker_manager.docker_init import build_settings
from config import (
    parse_config,
    get_environment_type,
    DATABASE_SECTION,
    DATABASE_URL_KEY,
    RABBITMQ_SECTION,
    RABBITMQ_HOST_KEY,
    RABBITMQ_PORT_KEY,
    RABBITMQ_USER_KEY,
    RABBITMQ_PASSWORD_KEY,
    RABBITMQ_CONTROLLER_QUEUE_KEY,
    RABBITMQ_ACK_STATUS_QUEUE_KEY,
    RABBITMQ_ACK_DELETE_QUEUE_KEY
)
from src.rabbitmq.rabbitmq_handler import start_rabbitmq_consumer_pool
from instance_manager.instance.instance_dao import InstanceDAOFactory
from instance_manager.instance.instance_service import InstanceService
from docker_manager.docker_api import DockerApi
from psycopg_pool import ConnectionPool
import asyncio
import logging


logging.basicConfig(level=logging.INFO)


async def main():

    loop = asyncio.get_event_loop()

    cfg = parse_config(get_environment_type())
    db_url = cfg.get(DATABASE_SECTION, DATABASE_URL_KEY)

    rabbit_cfg = {
        "host": cfg.get(RABBITMQ_SECTION, RABBITMQ_HOST_KEY),
        "port": cfg.get(RABBITMQ_SECTION, RABBITMQ_PORT_KEY),
        "user": cfg.get(RABBITMQ_SECTION, RABBITMQ_USER_KEY),
        "password": cfg.get(RABBITMQ_SECTION, RABBITMQ_PASSWORD_KEY),
        "controller_queue": cfg.get(
            RABBITMQ_SECTION,
            RABBITMQ_CONTROLLER_QUEUE_KEY
            ),
        "ack_status_queue": cfg.get(RABBITMQ_SECTION, RABBITMQ_ACK_STATUS_QUEUE_KEY),
        "ack_delete_queue": cfg.get(RABBITMQ_SECTION, RABBITMQ_ACK_DELETE_QUEUE_KEY),
    }

    docker_cfg = docker_init.get_docker_config(cfg)
    processing_mode = docker_cfg["processing_mode"]
    cuda_version = docker_cfg.get("cuda_version", None)
    docker_init.docker_build_images(processing_mode, cuda_version)
    processor_image_tag = build_settings(processing_mode)['tag']

    with ConnectionPool(db_url) as connection_manager:
        instance_service = InstanceService(
            connection_manager,
            InstanceDAOFactory(),
            DockerApi(processor_image_tag, processing_mode)
        )
        await start_rabbitmq_consumer_pool(
            rabbit_cfg,
            instance_service,
            event_loop=loop
        )

if __name__ == "__main__":
    asyncio.run(main())
