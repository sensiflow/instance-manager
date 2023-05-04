from configparser import ConfigParser
import os
import logging

CONFIG_EXTENSION = ".ini"
CONFIG_FOLDER = "./configs/"
logger = logging.getLogger(__name__)


def get_environment_type() -> str:
    """Returns the environment type of the application."""
    env = os.getenv("ENVIRONMENT")

    if env is None:
        raise EnvironmentError(
            "Please provide an environment variable: ENVIRONMENT")

    return env.lower()


def parse_config(env_type: str):
    """Parses the config file for the application based on the environment."""
    config = ConfigParser()
    file_name = CONFIG_FOLDER + env_type.lower() + CONFIG_EXTENSION

    if not os.path.exists(file_name):
        raise FileNotFoundError(
            "There's no config file for the current environment: {}"
            .format(file_name)
        )

    logger.info("Parsing config file: %s", file_name)
    config.read(file_name)
    return config
