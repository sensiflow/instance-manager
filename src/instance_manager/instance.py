from dataclasses import dataclass
from src.instance_manager.exception import DomainLogicError
from datetime import datetime


@dataclass(frozen=True)
class Instance:
    def __post_init__(self):
        if self.status not in ("ACTIVE", "INACTIVE"):
            raise DomainLogicError(
                f"Invalid status {self.status}. " +
                "Status must be ACTIVE or INACTIVE"
            )

        if self.updated_at < self.created_at:
            raise DomainLogicError(
                f"Invalid updated_at {self.updated_at}. " +
                "updated_at must be greater than created_at"
            )

    id: str
    name: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
