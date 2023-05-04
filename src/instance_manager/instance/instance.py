from dataclasses import dataclass
from src.instance_manager.exception import DomainLogicError
from datetime import datetime
from enum import Enum, auto


class InstanceStatus(Enum):
    ACTIVE = auto()
    INACTIVE = auto()
    PAUSED = auto()


@dataclass(frozen=True)
class Instance:
    def __post_init__(self):
        if self.updated_at < self.created_at:
            raise DomainLogicError(
                f"Invalid updated_at {self.updated_at}. " +
                "updated_at must be greater than created_at"
            )

    id: int
    status: InstanceStatus
    created_at: datetime
    updated_at: datetime
    scheduled_for_deletion: bool
