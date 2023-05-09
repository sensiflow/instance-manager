import asyncio
from concurrent.futures import ThreadPoolExecutor
import docker
import logging
from docker.errors import APIError

from docker_manager.docker_init import ProcessingMode
from src.docker_manager.exceptions import ContainerGoalTimeout

logger = logging.getLogger(__name__)


class DockerApi:
    """
    Manage docker engine
    TODO: Run client.containers methods in an executor
          to avoid blocking the event loop
    """
    restart_policy = {"Name": "on-failure", "MaximumRetryCount": 1}
    network_mode = "host"
    # TODO: mudar para uma constante o nome do ficheiro
    entrypoint = ["python", "transmit.py", "--weights", "yolov5s.pt"]
    # TODO: add --class 0 to entrypoint for only people detection
    def __init__(self, processor_image: str, processing_mode: ProcessingMode):
        self.client = docker.from_env()
        self.processor_image = processor_image
        self.api_pool = ThreadPoolExecutor(max_workers=5)
        self.processing_mode = processing_mode

    def is_healthy(self):
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def stop_container(self, container_name: str):
        logger.info(f"Stopping container {container_name}")
        self.client.containers.get(container_name).stop(timeout=15)

    async def remove_container(self, container_name: str, force=False, timeout=2):
        """

        Parameters:
            container_name: the name of the container to remove
            Force: if true, the container is killed and removed immediately
            otherwise the method waits for the container to stop 
            and then removes it
            timeout: the time to wait for the container to stop,
             when this timeout is reached a SIGKILL is sent to the container
        """
        container = self.client.containers.get(container_name)

        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(
                self.api_pool,
                self.wait_container_removal,
                container, container_name, force, timeout
            )
        except Exception as e:
            logger.error(f"Error removing container {container_name}: {e}")

    def wait_container_removal(self, container, container_name, force, timeout):
        if container.status != "exited":
            logger.info(f"Stopping container {container_name}")
            container.stop(timeout=timeout)

        if force:
            logger.info(f"Forcefully Removing container {container_name}")
            container.remove(force=True)
        else:
            # container.wait is synchronous
            container.wait()
            logger.info(f"Removing container {container_name}")
            container.remove()

    async def run_container(self, container_name: str, *extra_args: str):
        logger.info(f"Creating container {container_name}")

        # TODO: call in executor, run in blocking

        if self.processing_mode == ProcessingMode.CPU:
            args = ["--device", "cpu"]
        else:
            args = ["--device", "0"]

        docker_args = args + list(extra_args)

        try:
            container = self.client.containers.run(
                name=container_name,
                image=self.processor_image,
                detach=True,
                restart_policy=self.restart_policy,
                network_mode=self.network_mode,
                entrypoint=self.entrypoint,
                command=docker_args
            )

            await self.wait_goals(container)

        except APIError as e:
            logger.error(f"Error starting container: {e}")
            raise e

    async def wait_goals(self, container, timeout_seconds=60):
        """
         Scans container logs for goal messages
         returns when the final goal is reached

         Parameters:
            container: the name of the container to scan
            timeout_seconds: the maximum time to wait for the final goal

         Throws:
            GoalTimeout: if the timeout is reached
            before the final goal is reached
        """
        logger.info(f"Waiting for goals in container {container.name}")

        def goal_reached(container):
            for line in container.logs(stream=True):
                logger.info(line.decode("utf-8"))

                if b"[ERROR" in line:
                    decodedLine = line.decode("utf-8")
                    logger.error(decodedLine.split("]")[1])
                    raise Exception(decodedLine.split("]")[1])

                if b"[SUCCESS 4]" in line:
                    logger.info("Started Streaming")
                    return True

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(self.api_pool, goal_reached, container)
        try:
            await asyncio.wait_for(task, timeout_seconds)
        except asyncio.TimeoutError:
            await self.remove_container(container.name, force=True)
            raise ContainerGoalTimeout(container.name)

    def get_container(self, container_name):
        return self.client.containers.get(container_name)

    def get_containers(self):
        containers = self.client.containers.list()
        return [container.name for container in containers]
