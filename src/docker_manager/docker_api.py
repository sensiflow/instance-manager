import docker
import logging
import time


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
        
    async def wait_goals(self, container, timeout_seconds=60):
        """
        Scans container logs for goal messages returns when the final goal is reached
        """
        logger.info("Waiting for container to reach goal")
        start_time = time.time()
        current_time = start_time
        async for line in container.logs(stream=True):
            if b"[GOAL]" in line:
                logger.info("Container: GOAL REACHED")
                break
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                break




        




