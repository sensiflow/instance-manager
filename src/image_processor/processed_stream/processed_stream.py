from dataclasses import dataclass


@dataclass
class ProcessedStream:
    device_id: int
    stream_url: str
