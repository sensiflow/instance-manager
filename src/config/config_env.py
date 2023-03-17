from configparser import ConfigParser
from enum import Enum, auto
import os
import logging

CONFIG_EXTENSION = ".ini"
CONFIG_FOLDER = "./configs/"
logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Enum for the environment types that are supported by the application."""
    PROD = auto()
    DEV = auto()
    TEST = auto()


def get_environment_type() -> EnvironmentType:
    """Returns the environment type of the application."""
    env = os.getenv("ENVIRONMENT")
    if env == "PROD":
        return EnvironmentType.PROD
    elif env == "DEV":
        return EnvironmentType.DEV
    elif env == "TEST":
        return EnvironmentType.TEST
    else:
        raise ValueError("The environment type is not supported."
                         + "Set the environment variable ENVIRONMENT to:"
                         + "PROD, DEV, TEST")


def parse_config(env_type: EnvironmentType):
    """Parses the config file for the application based on the environment."""
    config = ConfigParser()
    file_name = CONFIG_FOLDER + env_type.name.lower() + CONFIG_EXTENSION

    if not os.path.exists(file_name):
        raise FileNotFoundError(
            "Please provide a config file for the current environment: %s",
            file_name
        )

    logger.info("Parsing config file: %s", file_name)
    config.read(file_name)
    return config
