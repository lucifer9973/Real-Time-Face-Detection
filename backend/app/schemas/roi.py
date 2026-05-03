from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ROIResponse(BaseModel):
    id: int
    timestamp: datetime
    x: int
    y: int
    width: int
    height: int
    frame_id: int
    session_id: str

    model_config = ConfigDict(from_attributes=True)
