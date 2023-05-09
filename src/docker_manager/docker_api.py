import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools
import docker
import logging
from docker.errors import APIError, DockerException, NotFound
from src.docker_manager.exceptions import ContainerGoalTimeout, ContainerNotFound
from docker_manager.docker_init import ProcessingMode

logger = logging.getLogger(__name__)


class DockerApi:
    """
        Manage docker engine
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
        self.loop = asyncio.get_event_loop()
        self.processing_mode = processing_mode

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

    async def run_container(self, container_name: str, *extra_args: str):
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
            if self.processing_mode == ProcessingMode.CPU:
                args = ["--device", "cpu"]
            else:
                args = ["--device", "0"]

            docker_args = args + list(extra_args)

            container = await self.loop.run_in_executor(
                self.api_pool,
                self.__run_container,
                container_name,
                *docker_args
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

                if b"[ERROR" in line:
                    decodedLine = line.decode("utf-8")
                    logger.error(decodedLine.split("]")[1])
                    raise Exception(decodedLine.split("]")[1])

                if b"[SUCCESS 4]" in line:
                    logger.info("Started Streaming")
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
            await self.loop.run_in_executor(
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
            await self.loop.run_in_executor(
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
            await self.loop.run_in_executor(
                self.api_pool,
                container.start
            )

            await self.__wait_goals(container)
        except (DockerException, APIError) as e:
            logger.error(f"Error starting container {container_name}")
            raise e
