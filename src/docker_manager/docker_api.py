import asyncio
from concurrent.futures import ThreadPoolExecutor
import docker
import logging
from docker.errors import APIError
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

    def __init__(self, processor_image: str):
        self.client = docker.from_env()
        self.processor_image = processor_image
        self.api_pool = ThreadPoolExecutor()

    def stop_container(self, container_name: str):
        logging.info(f"Stopping container {container_name}")
        self.client.containers.get(container_name).stop(timeout=15)

    async def remove_container(self, container_name: str, force=False, timeout=15):
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
        logging.info(f"Stopping container {container_name}")

        if container.status != "exited":
            container.stop(timeout=timeout)

        if force:
            logging.info(f"Forcefully Removing container {container_name}")
            container.remove(force=True)
        else:
            await container.wait()
            logging.info(f"Removing container {container_name}")
            container.remove()

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
                if b"[GOAL]" in line:
                    logger.info("Final goal reached")
                    return True

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(self.api_pool, goal_reached, container)
        try:
            await asyncio.wait_for(task, timeout_seconds)
        except asyncio.TimeoutError:
            await self.remove_container(container.name, force=True)
            raise ContainerGoalTimeout(container.name)
