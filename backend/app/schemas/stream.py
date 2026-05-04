from pydantic import BaseModel, ConfigDict, Field


class StreamStartRequest(BaseModel):
    source_name: str = Field(default="webcam", min_length=1, max_length=50)


class StreamStartResponse(BaseModel):
    status: str
    session_id: str


class FrameMessage(BaseModel):
    frame_id: int = Field(ge=0)
    session_id: str = Field(min_length=8, max_length=64)
    image_base64: str = Field(min_length=10)


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

    model_config = ConfigDict(from_attributes=True)


class ProcessedFrameResponse(BaseModel):
    frame_id: int
    image_base64: str
    rois: list[BoundingBox]
    message: str | None = None


class UploadedImageResponse(BaseModel):
    image_base64: str
    rois: list[BoundingBox]
    message: str | None = None
