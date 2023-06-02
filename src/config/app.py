from config import (
    DATABASE_SECTION,
    DATABASE_USER_KEY,
    DATABASE_PASSWORD_KEY,
    DATABASE_HOST_KEY,
    DATABASE_PORT_KEY,
    RABBITMQ_SECTION,
    RABBITMQ_HOST_KEY,
    RABBITMQ_PORT_KEY,
    RABBITMQ_USER_KEY,
    RABBITMQ_PASSWORD_KEY,
    RABBITMQ_CONTROLLER_QUEUE_KEY,
    RABBITMQ_ACK_STATUS_QUEUE_KEY,
    RABBITMQ_ACK_DELETE_QUEUE_KEY,
    HARDWARE_ACCELERATION_SECTION,
    HARDWARE_ACCELERATION_PROCESSING_MODE_KEY,
    HARDWARE_ACCELERATION_CUDA_VERSION_KEY
)


def get_app_config(config_parser):
    """
    Get the application config settings from the given ConfigParser instance.
    """
    config = {}

    # Database configuration
    config["database"] = {
        "user": config_parser.get(DATABASE_SECTION, DATABASE_USER_KEY),
        "password": config_parser.get(DATABASE_SECTION, DATABASE_PASSWORD_KEY),
        "host": config_parser.get(DATABASE_SECTION, DATABASE_HOST_KEY),
        "port": config_parser.get(DATABASE_SECTION, DATABASE_PORT_KEY)
    }

    # RabbitMQ configuration
    config["rabbitmq"] = {
        "host": config_parser.get(RABBITMQ_SECTION, RABBITMQ_HOST_KEY),
        "port": config_parser.get(RABBITMQ_SECTION, RABBITMQ_PORT_KEY),
        "user": config_parser.get(RABBITMQ_SECTION, RABBITMQ_USER_KEY),
        "password": config_parser.get(RABBITMQ_SECTION, RABBITMQ_PASSWORD_KEY),
        "controller_queue": config_parser.get(
            RABBITMQ_SECTION,
            RABBITMQ_CONTROLLER_QUEUE_KEY
        ),
        "ack_status_queue": config_parser.get(
            RABBITMQ_SECTION,
            RABBITMQ_ACK_STATUS_QUEUE_KEY
        ),
        "ack_delete_queue": config_parser.get(
            RABBITMQ_SECTION,
            RABBITMQ_ACK_DELETE_QUEUE_KEY
        )
    }

    # Hardware acceleration configuration
    config["hardware_acceleration"] = {
        "processing_mode": config_parser.get(
            HARDWARE_ACCELERATION_SECTION,
            HARDWARE_ACCELERATION_PROCESSING_MODE_KEY
        ),
        "cuda_version": config_parser.get(
            HARDWARE_ACCELERATION_SECTION,
            HARDWARE_ACCELERATION_CUDA_VERSION_KEY,
            fallback=None
        )
    }

    return config


def get_worker_config(config_parser):
    config = {}

    # Database configuration
    config["database"] = {
        "user": config_parser.get(DATABASE_SECTION, DATABASE_USER_KEY),
        "password": config_parser.get(DATABASE_SECTION, DATABASE_PASSWORD_KEY),
        "host": config_parser.get(DATABASE_SECTION, DATABASE_HOST_KEY),
        "port": config_parser.get(DATABASE_SECTION, DATABASE_PORT_KEY)
    }

    return config
