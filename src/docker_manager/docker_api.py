import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools
import re
import docker
import logging
from docker.errors import APIError, DockerException, NotFound
from src.docker_manager.container_status import ContainerStatus
from src.docker_manager.exceptions import ContainerGoalTimeout, ContainerNotFound


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
        self.api_pool = ThreadPoolExecutor(max_workers=5)
        self.loop = asyncio.get_event_loop()

    async def check_health(self):
        """
        Checks if docker engine is running
        Throws:
            DockerException: Error while fetching server API version
            APIError: If the server returns an error.
        """
        try:
            await self.loop.run_in_executor(
                self.api_pool,
                self.client.ping
            )
        except (DockerException, APIError) as e:
            logger.error("Docker server not responsive")
            raise e

    async def get_container(self, container_name):
        """
        Gets the container with the given name
        Parameters:
            container_name: the name of the container to get
        Returns:
            the container with the given name
        Throws:
            ContainerNotFound - if the container with the given name
                                does not exist
            DockerException: Error while fetching server API version
            APIError: If the server returns an error.
        """
        try:
            logger.info(f"Getting container {container_name}")
            return await self.loop.run_in_executor(
                self.api_pool,
                self.client.containers.get,
                container_name
            )
        except NotFound:
            logger.error(f"Container {container_name} not found")
            raise ContainerNotFound(container_name)
        except (DockerException, APIError) as e:
            logger.error(f"Error getting container {container_name}: {e}")
            raise e

    async def get_containers(self, status: ContainerStatus = None):
        """
        Gets all the containers in the docker engine that match container-{id}
        Parameters:
            status: the status of the containers to get
        Returns:
            a list with the names of all the containers in the docker
            engine
        """
        try:
            logger.info("Getting all containers")
            containers = await self.loop.run_in_executor(
                self.api_pool,
                self.__get_containers,
                True,
            )
            container_name_regex = re.compile(r'^instance-\d+$')
            device_containers = [
                device_container for device_container in containers
                if container_name_regex.match(device_container.name)
            ]

            return [container.name for container in device_containers]
        except Exception as e:
            logger.error(f"Error getting containers: {e}")
            raise e

    def __get_containers(self, all=False):
        return self.client.containers.list(all=all)

    async def stop_container(
        self,
        container_name: str,
        timeout=15
    ):
        """
        Stops the container with the given name
        Parameters:
            container_name: the name of the container to stop
            timeout: the time to wait for the container to stop
        Throws:
            ContainerNotFound - if the container with the given name
                                does not exist
            DockerException: Error while fetching server API version
            APIError: If the server returns an error.
        """
        try:
            container = await self.get_container(container_name)
            await self.loop.run_in_executor(
                self.api_pool,
                functools.partial(
                    container.stop,
                    timeout=timeout
                )
            )
        except (DockerException, APIError) as e:
            logger.error(f"Error stopping container {container_name}")
            raise e

    async def remove_container(
            self,
            container_name: str,
            force=False,
            timeout=15
    ):
        """
        Removes the container with the given name
        Parameters:
            container_name: the name of the container to remove
            force: if true, the container is killed and removed immediately
                    otherwise the method waits for the container to stop
                    and then removes it
            timeout: the time to wait for the container to stop,
                        when this timeout is reached a SIGKILL is sent to the
                        container
        Throws:
            ContainerNotFound - if the container with the given name
                                does not exist
            DockerException: Error while fetching server API version
            APIError: If the server returns an error.
        """
        try:
            container = await self.get_container(container_name)
            await self.loop.run_in_executor(
                self.api_pool,
                self.__wait_container_removal,
                container, container_name, force, timeout
            )
        except (DockerException, APIError) as e:
            logger.error(f"Error removing container {container_name}")
            raise e

    def __wait_container_removal(
            self,
            container,
            container_name,
            force,
            timeout
    ):
        """
        Removes the container with the given name
        Parameters:
            container: the container to remove
            container_name: the name of the container to remove
            force: if true, the container is killed and removed immediately
                otherwise the method waits for the container to stop
                and then removes it
            timeout: the time to wait for the container to stop,
                    when this timeout is reached a SIGKILL is sent to the
                    container
        """
        if container.status != "exited":
            logger.info(f"Stopping container {container_name}")
            container.stop(timeout=timeout)

        if force:
            logger.info(f"Forcefully Removing container {container_name}")
            container.remove(force=True)
        else:
            container.wait()
            logger.info(f"Removing container {container_name}")
            container.remove()

    async def run_container(self, container_name: str, *args: str):
        """
        Runs the container with the given name
        Parameters:
            container_name: the name of the container to run
            args: the arguments to pass to the container.
        Throws:
            DockerException: Error while fetching server API version.
            APIError: If the server returns an error.
        """
        logger.info(f"Creating container {container_name}")
        # run dockerfile with name
        try:
            container = await self.loop.run_in_executor(
                self.api_pool,
                self.__run_container,
                container_name,
                *args
            )

            await self.__wait_goals(container)

        except (DockerException, APIError) as e:
            logger.error("Error starting container")
            raise e

    def __run_container(self, container_name: str, *args):
        return self.client.containers.run(
            name=container_name,
            image=self.processor_image,
            detach=True,
            restart_policy=self.restart_policy,
            network_mode=self.network_mode,
            entrypoint=self.entrypoint,
            command=args
        )

    async def __wait_goals(self, container, timeout_seconds=60):
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

        task = self.loop.run_in_executor(
            self.api_pool,
            goal_reached,
            container
        )
        try:
            await asyncio.wait_for(task, timeout_seconds)
        except asyncio.TimeoutError:
            await self.remove_container(container.name, force=True)
            raise ContainerGoalTimeout(container.name)

    async def pause_container(self, container_name: str):
        """
        Pauses the container with the given name
        Parameters:
            container_name: the name of the container to pause
        Throws:
            ContainerNotFound - if the container with the given name
                                does not exist
            DockerException: Error while fetching server API version
            APIError: If the server returns an error.
        """
        try:
            container = await self.get_container(container_name)
            self.loop.run_in_executor(
                self.api_pool,
                container.pause
            )
        except (DockerException, APIError) as e:
            logger.error(f"Error pausing container {container_name}")
            raise e

    async def unpause_container(self, container_name: str):
        """
        Unpauses the container with the given name
        Parameters:
            container_name: the name of the container to unpause
        Throws:
            ContainerNotFound - if the container with the given name
                                does not exist
            DockerException: Error while fetching server API version
            APIError: If the server returns an error.
        """
        try:
            container = await self.get_container(container_name)
            self.loop.run_in_executor(
                self.api_pool,
                container.unpause
            )
        except (DockerException, APIError) as e:
            logger.error(f"Error unpausing container {container_name}")
            raise e

    async def start_container(self, container_name: str):
        """
        Starts the container with the given name
        Parameters:
            container_name: the name of the container to start
        Throws:
            ContainerNotFound - if the container with the given name
                                does not exist
            DockerException: Error while fetching server API version
            APIError: If the server returns an error.
        """
        try:
            container = await self.get_container(container_name)
            self.loop.run_in_executor(
                self.api_pool,
                container.start
            )

            await self.__wait_goals(container)
        except (DockerException, APIError) as e:
            logger.error(f"Error starting container {container_name}")
            raise e
