from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

#Internal models 
class UplinkMessage(BaseModel):
    device_id: str 
    fport: int
    decoded: Optional[Dict[str, Any]] = None
    seq: Optional[int] = None 
    raw_b64: Optional[str] = None 
    received_at: datetime


class SensorReading(BaseModel):
    device_id: str
    sensor_name: str
    value: float
    unit: str
    measured_at: datetime

class SensorStats(BaseModel):
    device_id: str
    sensor_name: str
    min: float
    max: float
    avg: float
    count: int
    start: datetime
    end: datetime


class DownlinkCommand(BaseModel):
    device_id: str
    command: str 
    params: Dict[str, Any]
    requested_at: datetime

# API input models 

class IntervalRequest(BaseModel):
    interval_minutes: int





