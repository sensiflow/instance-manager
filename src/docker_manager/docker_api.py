import docker
import logging


class DockerApi:
    """
    Manage docker engine
    """
    def __init__(self, processor_image: str):
        self.client = docker.from_env()
        self.processor_image = processor_image

    def create_container(self, container_name: str):
        logging.info(f"Creating container {container_name}")
        # run dockerfile with name
        self.client.run(
            name=container_name,
            image=self.processor_image,
            detach=True,
            auto_remove=True
        )
