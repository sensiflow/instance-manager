from src.image_processor.processed_stream.processed_stream import (
    ProcessedStream)


class ProcessedStreamDAOFactory:
    """Factory for creating InstanceDAO objects."""

    def create_dao(self, cursor):
        return ProcessedStreamDAO(cursor)


class ProcessedStreamDAO:

    def __init__(self, cursor) -> None:
        self.cursor = cursor

    def exists(self, processed_stream_id: int):
        query = """
        SELECT EXISTS(SELECT 1 FROM processedstream WHERE deviceid = %s);
        """
        self.cursor.execute(
            query,
            (
                processed_stream_id,
            )
        )

        result = self.cursor.fetchone()
        exists = result[0]

        return exists

    def create_processed_stream(self, processed_stream: ProcessedStream):
        query = """
        INSERT INTO processedstream (deviceid, processedstreamurl)
        VALUES (%s, %s);
        """
        self.cursor.execute(
            query,
            (
                processed_stream.device_id,
                processed_stream.stream_url
            )
        )

    def update_processed_stream(self, processed_stream: ProcessedStream):
        query = """
        UPDATE processedstream
        SET processedstreamurl = %s WHERE deviceid = %s;
        """
        self.cursor.execute(
            query,
            (
                processed_stream.stream_url,
                processed_stream.device_id
            )
        )
