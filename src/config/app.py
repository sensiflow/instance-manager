from config.constants import MEDIA_SERVER_RTSPS_PORT_KEY, MEDIA_SERVER_SECURE_KEY, MEDIA_SERVER_RTSP_PORT_KEY
from src.config import (
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
    RABBITMQ_SCHEDULER_NOTIFICATION_KEY,
    HARDWARE_ACCELERATION_SECTION,
    HARDWARE_ACCELERATION_PROCESSING_MODE_KEY,
    HARDWARE_ACCELERATION_CUDA_VERSION_KEY,
    MEDIA_SERVER_SECTION,
    MEDIA_SERVER_DESTINATION_HOST_KEY,
    MEDIA_SERVER_WRITE_USER_KEY,
    MEDIA_SERVER_WRITE_PASSWORD_KEY,
)
from src.config.constants import RABBITMQ_SCHEDULER_NOTIFICATION_KEY


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
        "instance_scheduler_notification": config_parser.get(
            RABBITMQ_SECTION,
            RABBITMQ_SCHEDULER_NOTIFICATION_KEY
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

    config["MEDIA_SERVER"] = {
        "destination_host" : config_parser.get(MEDIA_SERVER_SECTION,MEDIA_SERVER_DESTINATION_HOST_KEY),
        "write_user" : config_parser.get(MEDIA_SERVER_SECTION,MEDIA_SERVER_WRITE_USER_KEY),
        "write_password" : config_parser.get(MEDIA_SERVER_SECTION,MEDIA_SERVER_WRITE_PASSWORD_KEY),
        "secure" : config_parser.get(MEDIA_SERVER_SECTION,MEDIA_SERVER_SECURE_KEY,fallback=False),
        "rtsps_port" : config_parser.get(MEDIA_SERVER_SECTION,MEDIA_SERVER_RTSPS_PORT_KEY,fallback=8322),
        "rtsp_port" : config_parser.get(MEDIA_SERVER_SECTION,MEDIA_SERVER_RTSP_PORT_KEY, fallback=8554),
    }

    return config
