from dataclasses import dataclass, asdict

@dataclass
class TelemetryRecord:
    timestamp: str
    temperature: float = None
    pressure: float = None
    imu: dict = None
    status: dict = None

    def to_dict(self):
        return asdict(self)