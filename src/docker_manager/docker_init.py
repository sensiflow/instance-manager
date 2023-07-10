import docker
from enum import Enum, auto
from src.docker_manager.exceptions import IncompatibleConfigVariables
from src.docker_manager.constants import (
    DOCKERFILE_CPU,
    DOCKERFILE_GPU,
    TAG_CPU,
    TAG_GPU
)
from src.config import (
    HARDWARE_ACCELERATION_PROCESSING_MODE_KEY,
    HARDWARE_ACCELERATION_CUDA_VERSION_KEY
)
import logging

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    CPU = auto()
    GPU = auto()


def validate_worker_config(hardware_acceleration_cfg: dict):
    processing_mode_value = hardware_acceleration_cfg["processing_mode"]
    mode = ProcessingMode[processing_mode_value]
    if mode == ProcessingMode.CPU:
        return {
            "processing_mode": mode,
        }
    elif mode == ProcessingMode.GPU:
        cuda_version = hardware_acceleration_cfg["cuda_version"]
        if cuda_version is None:
            IncompatibleConfigVariables(
                HARDWARE_ACCELERATION_PROCESSING_MODE_KEY,
                HARDWARE_ACCELERATION_CUDA_VERSION_KEY
            )
        return {
            "processing_mode": mode,
            "cuda_version": cuda_version
        }


def build_settings(hardware_acceleration_cfg: dict):
    valid_cfg = validate_worker_config(hardware_acceleration_cfg)
    if valid_cfg["processing_mode"] == ProcessingMode.CPU:
        return {
            "path": DOCKERFILE_CPU,
            "tag": TAG_CPU
        }
    else:
        return {
            "path": DOCKERFILE_GPU,
            "tag": TAG_GPU,
            "cuda_version": valid_cfg["cuda_version"]
        }


def build_images(build_args: dict):
    client = docker.from_env()
    logger.info(f"Building image with tag {build_args['tag']},"
                " please wait, this may take a while...")

    client.images.build(
        path=".",
        tag=build_args["tag"],
        rm=True,
        dockerfile=build_args["path"] + "/Dockerfile",
        buildargs={
            "CUDA_VERSION": build_args.get("cuda_version", None)
        }
    )
    logger.info(f"Image built with tag {build_args['tag']}")
