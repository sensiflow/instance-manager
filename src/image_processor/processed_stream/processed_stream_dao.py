from src.image_processor.processed_stream.processed_stream import (
    ProcessedStream)


class ProcessedStreamDAOFactory:
    """Factory for creating InstanceDAO objects."""

    def create_dao(self, cursor):
        return ProcessedStreamDAO(cursor)


class ProcessedStreamDAO:

    def __init__(self, cursor) -> None:
        self.cursor = cursor

    def update_processed_stream(self, processed_stream: ProcessedStream):
        query = """
        update device set processedStreamUrl = %s where id = %s
        """
        self.cursor.execute(
            query,
            (
                processed_stream.stream_url,
                processed_stream.device_id
            )
        )

    async def delete_processed_stream(self, device_id: int):
        query = """
        update device set processedStreamUrl = null where id = %s
        """
        await self.cursor.execute(query, (device_id,))