import docker
from enum import Enum, auto
from configparser import ConfigParser
from docker_manager.exceptions import IncompatibleConfigVariables
from docker_manager.constants import (
    DOCKERFILE_CPU,
    DOCKERFILE_GPU,
    TAG_CPU,
    TAG_GPU
)
from src.config import (
    HARDWARE_ACCELERATION_SECTION,
    HARDWARE_ACCELERATION_PROCESSING_MODE_KEY,
    HARDWARE_ACCELERATION_CUDA_VERSION_KEY
)
import logging


logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    CPU = auto()
    GPU = auto()


def get_docker_config(cfg: ConfigParser):
    processing_mode = cfg.get(
        HARDWARE_ACCELERATION_SECTION,
        HARDWARE_ACCELERATION_PROCESSING_MODE_KEY
        )
    mode = ProcessingMode[processing_mode]
    if mode == ProcessingMode.CPU:
        return {
            "processing_mode": mode,
        }
    elif mode == ProcessingMode.GPU:
        has_version = cfg.has_option(
            HARDWARE_ACCELERATION_SECTION,
            HARDWARE_ACCELERATION_CUDA_VERSION_KEY
            )
        if not has_version:
            IncompatibleConfigVariables(
                HARDWARE_ACCELERATION_PROCESSING_MODE_KEY,
                HARDWARE_ACCELERATION_CUDA_VERSION_KEY
            )
        cuda_version = cfg.get(
            HARDWARE_ACCELERATION_SECTION,
            HARDWARE_ACCELERATION_CUDA_VERSION_KEY
            )
        return {
            "processing_mode": mode,
            "cuda_version": cuda_version
        }


def build_settings(processing_mode: ProcessingMode):
    if processing_mode == ProcessingMode.CPU:
        return {
            "path": DOCKERFILE_CPU,
            "tag": TAG_CPU
        }
    else:
        return {
            "path": DOCKERFILE_GPU,
            "tag": TAG_GPU
        }


def docker_build_images(processing_mode: ProcessingMode):
    client = docker.from_env()
    build_args = build_settings(processing_mode)
    logger.info(f"Building image with tag {build_args['tag']},"
                " please wait, this may take a while...")
    client.images.build(
        path=".",
        tag=build_args["tag"],
        dockerfile=build_args["path"] + "/Dockerfile"
        )
    logger.info(f"Image built with tag {build_args['tag']}")
