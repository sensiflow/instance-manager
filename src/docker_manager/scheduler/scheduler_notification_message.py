from dataclasses import dataclass


@dataclass(frozen=True, repr=True)
class SchedulerNotificationMessage:
    device_ids: []
    action: str
    code: int
    message: str
