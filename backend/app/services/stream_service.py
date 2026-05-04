from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.repositories.roi_repository import ROIRepository
from app.schemas.stream import FrameMessage, ProcessedFrameResponse, UploadedImageResponse
from app.services.face_detection import FaceDetectionError, FaceDetectorService


class StreamServiceError(Exception):
    pass


class StreamService:
    def __init__(self, settings: Settings, detector: FaceDetectorService):
        self.settings = settings
        self.detector = detector

    @staticmethod
    def start_stream() -> str:
        return str(uuid4())

    def process_frame(
        self, payload: FrameMessage, db: Session
    ) -> ProcessedFrameResponse:
        try:
            processed_b64, boxes = self.detector.detect_and_draw(
                payload.image_base64, self.settings.max_frame_bytes
            )
            if boxes:
                ROIRepository(db).save_many(
                    frame_id=payload.frame_id,
                    session_id=payload.session_id,
                    boxes=boxes,
                )
            return ProcessedFrameResponse(
                frame_id=payload.frame_id,
                image_base64=processed_b64,
                rois=boxes,
                message=None if boxes else "No face detected in this frame.",
            )
        except FaceDetectionError as exc:
            raise StreamServiceError(str(exc)) from exc
        except SQLAlchemyError as exc:
            raise StreamServiceError("Database operation failed.") from exc

    def process_uploaded_image(self, image_base64: str) -> UploadedImageResponse:
        try:
            processed_b64, boxes = self.detector.detect_and_draw(
                image_base64, self.settings.max_frame_bytes
            )
            return UploadedImageResponse(
                image_base64=processed_b64,
                rois=boxes,
                message=None if boxes else "No face detected in this image.",
            )
        except FaceDetectionError as exc:
            raise StreamServiceError(str(exc)) from exc
