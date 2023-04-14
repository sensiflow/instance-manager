import asyncio

import docker
import logging
from docker.models.containers import Container


class DockerApi:
    """
    Manage docker engine
    """
    restart_policy = {"Name": "on-failure", "MaximumRetryCount": 5}
    network_mode = "host"
    # TODO: mudar para uma constante o nome do ficheiro
    entrypoint = ["python", "detect.py"]

    def __init__(self, processor_image: str):
        self.client = docker.from_env()
        self.processor_image = processor_image

    def create_container(self, container_name: str, *args: str):
        logging.info(f"Creating container {container_name}")
        # run dockerfile with name
        try:
            self.client.containers.run(
                name=container_name,
                image=self.processor_image,
                detach=True,
                restart_policy=self.restart_policy,
                network_mode=self.network_mode,
                entrypoint=self.entrypoint,
                command=args
            )
        except docker.errors.APIError as e:
            logging.error(f"Error running container: {e}")

