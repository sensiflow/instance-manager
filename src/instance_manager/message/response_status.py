from enum import Enum, auto


class ResponseStatus(Enum):
    Ok = auto()
    BadRequest = auto()
    NotFound = auto()
    InternalError = auto()
    Conflict = auto()
