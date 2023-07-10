from enum import Enum, auto


class SchedulerNotification(Enum):
    UPDATED_INSTANCE = auto()
    REMOVED_INSTANCE = auto()