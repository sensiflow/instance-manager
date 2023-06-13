import logging
import time
from src.image_processor.metric.metrics_service import DetectionMetricsService

"""
Wrapper functions to inject dependencies into the callback functions
"""

logger = logging.getLogger(__name__)


def get_on_metric_received_callback(metrics_service: DetectionMetricsService):
    def on_metric_received(detections):
        try:
            logger.info("Received metric: %s", detections)
            people_count = detections.get("person", 0)
            metrics_service.save_metric(count=people_count)
        except Exception as e:
            logger.error("Error saving metric: %s", e)

    return ThrottledCallback(on_metric_received, 1)


def get_on_stream_started_callback(processed_stream_service, stream_url):
    def on_stream_started():
        try:
            logger.info("Stream started: %s", stream_url)
            processed_stream_service.save_processed_stream(stream_url)
        except Exception as e:
            logger.error("Error saving processed stream: %s" % e)
    return on_stream_started


class ThrottledCallback:
    def __init__(self, callback, interval_seconds):
        self.callback = callback
        self.interval_seconds = interval_seconds
        self.last_called = None

    def __call__(self, *args, **kwargs):
        current_time = time.time()
        if current_time - self.last_executed >= self.interval:
            self.callback(*args, **kwargs)
            self.last_executed = current_time
