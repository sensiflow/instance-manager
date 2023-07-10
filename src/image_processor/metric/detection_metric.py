from dataclasses import dataclass
from datetime import datetime


@dataclass
class DetectionMetric:
    deviceid: int
    start_time: datetime
    end_time: datetime
    count: int
