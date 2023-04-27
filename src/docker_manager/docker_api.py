import asyncio
from concurrent.futures import ThreadPoolExecutor
import docker
import logging

from src.docker_manager.exceptions import GoalTimeout


logger = logging.getLogger(__name__)


class DockerApi:
    """
    Manage docker engine
    """
    restart_policy = {"Name": "on-failure", "MaximumRetryCount": 1}
    network_mode = "host"
    # TODO: mudar para uma constante o nome do ficheiro
    entrypoint = ["python", "transmit.py", "--weights", "yolov5s.pt"]

    def __init__(self, processor_image: str):
        self.client = docker.from_env()
        self.processor_image = processor_image
        self.log_pool = ThreadPoolExecutor()

    async def run_container(self, container_name: str, *args: str):
        logger.info(f"Creating container {container_name}")
        # run dockerfile with name
        try:
            container = self.client.containers.run(
                name=container_name,
                image=self.processor_image,
                detach=True,
                restart_policy=self.restart_policy,
                network_mode=self.network_mode,
                entrypoint=self.entrypoint,
                command=args
            )

            await self.wait_goals(container)

        except docker.errors.APIError as e:
            logger.error(f"Error starting container: {e}")
            raise e

    async def wait_goals(self, container, timeout_seconds=10):
        """
         Scans container logs for goal messages
         returns when the final goal is reached
        """
        logger.info(f"Waiting for goals in container {container.name}")

        def remove_container(container):
            container.stop()
            container.remove()

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(self.log_pool, goal_reached, container)
        try:
            await asyncio.wait_for(task, timeout_seconds)
        except asyncio.TimeoutError:
            logger.info(f"Timeout reached for container {container.name}")
            remove_container(container)
            raise GoalTimeout(container.name)


def goal_reached(container):
    for line in container.logs(stream=True):
        logger.info(line.decode("utf-8"))
        if b"[GOAL]" in line:
            logger.info("Final goal reached")
            return True
