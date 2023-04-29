
from dataclasses import asdict, dataclass


@dataclass(frozen=True, repr=True)
class AckMessage:
    device_id: int
    state: str
    code: int
    message: str

    def to_dict(self):
        return {k: str(v) for k, v in asdict(self).items()}
