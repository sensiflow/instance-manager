from datetime import datetime
import logging
from src.image_processor.metric.detection_metric import DetectionMetric
from src.database.transaction import transaction_sync
from psycopg_pool import AsyncConnectionPool, ConnectionPool
from src.image_processor.metric.metric_dao import MetricDAOFactory


class DetectionMetricsService:

    def __init__(self, conn_manager: ConnectionPool,
                 dao_factory: MetricDAOFactory, device_id: int) -> None:
        self.conn_manager = conn_manager
        self.logger = logging.getLogger(__name__)
        self.dao_factory = dao_factory
        self.device_id = device_id
        pass

    def save_metric(self, count: int):
        self.logger.info("Saving metric: %s | device: %s",
                         count, self.device_id)
        with transaction_sync(self.conn_manager) as cursor:
            metrics_dao = self.dao_factory.create_dao(cursor)
            latest_metric = metrics_dao.get_latest_unfinished_metric(
                self.device_id)
            is_new_metric = latest_metric is not None \
                and latest_metric.count != count

            def _new_metric():
                new_metric = DetectionMetric(
                    deviceid=self.device_id,
                    count=count,
                    start_time=datetime.utcnow(),
                    end_time=None,
                )
                metrics_dao.start_metric(new_metric)
                return

            if latest_metric is None:
                _new_metric()
                return

            updated_previous_metric = DetectionMetric(
                deviceid=self.device_id,
                count=latest_metric.count,
                start_time=latest_metric.start_time,
                end_time=datetime.utcnow() if is_new_metric else None,
            )

            metrics_dao.close_metric(updated_previous_metric)
            if is_new_metric:
                _new_metric()
