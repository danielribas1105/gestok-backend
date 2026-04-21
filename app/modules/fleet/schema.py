from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PositionBase(BaseModel):
    vehicle_id: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class PositionCreate(PositionBase):
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: Optional[datetime] = None


class PositionResponse(PositionBase):
    speed: Optional[float]
    heading: Optional[float]
    timestamp: datetime


class PositionBroadcast(PositionResponse):
    """
    Payload enviado via WebSocket
    """

    event: str = "vehicle.updated"
