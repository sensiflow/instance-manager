from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class AckDeleteMessage:
    device_id: int

    def to_dict(self):
        return {k: str(v) for k, v in asdict(self).items()}
