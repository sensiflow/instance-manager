import sys

from image_processor.processed_stream.processed_stream_dao import ProcessedStreamDAOFactory
from src.docker_manager import docker_init
from src.config import (
    parse_config,
    get_environment_type,
)
from src.docker_manager.docker_init import ProcessingMode
from src.config.app import get_app_config
from src.rabbitmq.rabbit_init import consume_control_messages
from src.instance_manager.instance.instance_dao import InstanceDAOFactory
from src.instance_manager.instance.instance_service import InstanceService
from src.docker_manager.docker_api import DockerApi
from psycopg_pool import AsyncConnectionPool
import asyncio
import logging
import docker
import requests
import os

logging.basicConfig(level=logging.INFO)

yolov5ModelURL = "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt"

async def main():
    envType = get_environment_type()
    cfg = parse_config(envType)
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
    hardware_accel_mode = hardware_acceleration_cfg["processing_mode"]
    docker_processing_mode = ProcessingMode[hardware_accel_mode]
    # TODO: Fazer constante para o min_size

    # if no file at /docker/models/yolov5s.pt download it
    logging.info("Checking if yolov5s.pt exists")
    if not os.path.isfile('./docker/models/yolov5s.pt'):
        logging.info("Downloading yolov5s.pt")
        r = requests.get(yolov5ModelURL, allow_redirects=True)
        open('./docker/models/yolov5s.pt', 'wb').write(r.content)
        logging.info("Downloaded yolov5s.pt")


    async with AsyncConnectionPool(database_url, min_size=5) as conn_manager:
        instance_service = InstanceService(
            conn_manager,
            InstanceDAOFactory(),
            ProcessedStreamDAOFactory(),
            DockerApi(
                docker_build_args["tag"],
                docker_processing_mode
            )
        )
        await consume_control_messages(
            app_cfg["rabbitmq"],
            instance_service
        )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
