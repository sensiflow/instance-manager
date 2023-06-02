from src.image_processor.metric.detection_metric import DetectionMetric


class MetricDAOFactory:
    """Factory for creating InstanceDAO objects."""

    def create_dao(self, cursor):
        return MetricDAO(cursor)


class MetricDAO:

    def __init__(self, cursor) -> None:
        self.cursor = cursor

    def start_metric(self, metric: DetectionMetric):
        query = """
        INSERT INTO METRIC (deviceid, start_time, end_time, peoplecount)
        VALUES (%s, %s, %s, %s);
        """
        self.cursor.execute(
            query,
            (
                metric.deviceid,
                metric.start_time,
                metric.end_time,
                metric.count
            )
        )

    def close_metric(self, metric: DetectionMetric):
        query = """
        UPDATE METRIC SET end_time = %s
        WHERE deviceid = %s and start_time = %s;
        """
        self.cursor.execute(
            query,
            (
                metric.end_time,
                metric.deviceid,
                metric.start_time,
            )
        )

    def get_latest_unfinished_metric(self, device_id: int):
        query = """
        SELECT deviceid, start_time, end_time, peoplecount
        FROM METRIC WHERE deviceid = %s AND end_time IS NULL
        ORDER BY start_time DESC LIMIT 1;
        """
        self.cursor.execute(
            query,
            (
                device_id,
            )
        )

        result = self.cursor.fetchone()
        if result is None:
            return None

        return DetectionMetric(*result)
