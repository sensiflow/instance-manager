from src.config import (
    parse_config,
    get_environment_type,
    DATABASE_SECTION,
    DATABASE_URL_KEY,
    RABBITMQ_SECTION,
    RABBITMQ_HOST_KEY,
    RABBITMQ_PORT_KEY,
    RABBITMQ_USER_KEY,
    RABBITMQ_PASSWORD_KEY
)
from psycopg_pool import ConnectionPool
from src.instance_manager import InstanceService
from instance_manager.instance_dao import InstanceDAOFactory
import asyncio

async def main():
    cfg = parse_config(get_environment_type())
    db_url = cfg.get(DATABASE_SECTION, DATABASE_URL_KEY)

    rabbit_cfg = {
        "host": cfg.get(RABBITMQ_SECTION, RABBITMQ_HOST_KEY),
        "port": cfg.get(RABBITMQ_SECTION, RABBITMQ_PORT_KEY),
        "user": cfg.get(RABBITMQ_SECTION, RABBITMQ_USER_KEY),
        "password": cfg.get(RABBITMQ_SECTION, RABBITMQ_PASSWORD_KEY),
    }

    with ConnectionPool(db_url) as connection_manager:
        
        instance_service = InstanceService(connection_manager, InstanceDAOFactory())



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
