from dataclasses import dataclass


@dataclass(frozen=True, repr=True)
class CtlAcknowledgeMessage:
    device_id: int
    action: str
    code: int
    message: str
