import sys
from docker_manager import docker_init
from config import (
    parse_config,
    get_environment_type,
)
from src.config.app import get_app_config
from src.rabbitmq.rabbit_init import consume_control_messages
from instance_manager.instance.instance_dao import InstanceDAOFactory
from instance_manager.instance.instance_service import InstanceService
from docker_manager.docker_api import DockerApi
from psycopg_pool import AsyncConnectionPool
import asyncio
import logging
import docker


logging.basicConfig(level=logging.INFO)


async def main():
    cfg = parse_config(get_environment_type())
    app_cfg = get_app_config(cfg)

    database_cfg = app_cfg["database"]
    database_url = (
        f"postgres://{database_cfg['user']}:{database_cfg['password']}"
        f"@{database_cfg['host']}:{database_cfg['port']}"
    )

    hardware_acceleration_cfg = app_cfg["hardware_acceleration"]
    docker_build_args = docker_init.build_settings(hardware_acceleration_cfg)
    docker_init.build_images(docker_build_args)
    docker.from_env().ping()
    # TODO: Fazer constante para o min_size
    async with AsyncConnectionPool(database_url, min_size=5) as connection_manager:
        instance_service = InstanceService(
            connection_manager,
            InstanceDAOFactory(),
            DockerApi(docker_build_args["tag"])
        )
        await consume_control_messages(
            app_cfg["rabbitmq"],
            instance_service
        )

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
