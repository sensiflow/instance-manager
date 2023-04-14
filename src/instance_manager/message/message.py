from enum import Enum, auto
from dataclasses import dataclass


class Action(Enum):
    START = auto()
    STOP = auto()
    PAUSE = auto()


@dataclass(frozen=True)
class Message:
    action: Action
    device_id: int
    device_stream_url: str
