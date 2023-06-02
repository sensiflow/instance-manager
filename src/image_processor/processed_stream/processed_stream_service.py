import logging
from src.image_processor.processed_stream.processed_stream import (
    ProcessedStream)
from src.database.transaction import transaction_sync
from psycopg_pool import AsyncConnectionPool
from src.image_processor.processed_stream.processed_stream_dao import (
    ProcessedStreamDAOFactory)


class ProcessedStreamService:

    def __init__(self, conn_manager: AsyncConnectionPool,
                 dao_factory: ProcessedStreamDAOFactory,
                 device_id: int) -> None:
        self.conn_manager = conn_manager
        self.logger = logging.getLogger(__name__)
        self.dao_factory = dao_factory
        self.device_id = device_id

    def save_processed_stream(self, stream_url: str):
        self.logger.info(
            "Saving processed stream: %s | device: %s",
            stream_url,
            self.device_id
        )
        with transaction_sync(self.conn_manager) as cursor:

            self.logger.info("Inside transaction")

            processed_dao = self.dao_factory.create_dao(cursor)
            already_exists = processed_dao.exists(self.device_id)

            processed_stream = ProcessedStream(
                device_id=self.device_id,
                stream_url=stream_url,
            )

            if already_exists:
                self.logger.info(
                    "Updating processed stream: %s | device: %s",
                    stream_url,
                    self.device_id
                )
                processed_dao.update_processed_stream(processed_stream)
            else:
                self.logger.info(
                    "Creating processed stream: %s | device: %s",
                    stream_url,
                    self.device_id
                )
                processed_dao.create_processed_stream(processed_stream)
