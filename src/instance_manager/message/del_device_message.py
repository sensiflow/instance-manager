from dataclasses import dataclass

from src.instance_manager.message.ctl_message import Action


@dataclass(frozen=True)
class Message:
    action: Action
    device_id: int
    device_stream_url: str
