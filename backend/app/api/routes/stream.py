from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from time import monotonic

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.schemas.stream import FrameMessage, StreamStartRequest, StreamStartResponse
from app.services.face_detection import FaceDetectorService
from app.services.stream_service import StreamService, StreamServiceError

router = APIRouter(prefix="/stream", tags=["stream"])


def get_stream_service(
    settings: Settings = Depends(get_settings),
) -> StreamService:
    return StreamService(settings=settings, detector=FaceDetectorService())


@router.post("/start", response_model=StreamStartResponse, status_code=status.HTTP_201_CREATED)
def start_stream(
    _: StreamStartRequest,
    service: StreamService = Depends(get_stream_service),
) -> StreamStartResponse:
    session_id = service.start_stream()
    return StreamStartResponse(status="started", session_id=session_id)


@router.websocket("")
async def stream_socket(
    websocket: WebSocket,
    settings: Settings = Depends(get_settings),
):
    await websocket.accept()
    service = StreamService(settings=settings, detector=FaceDetectorService())
    db: Session = SessionLocal()
    min_interval = 1.0 / max(1, settings.max_ws_fps)
    last_processed_at = 0.0
    try:
        while True:
            payload = await websocket.receive_json()
            try:
                now = monotonic()
                if now - last_processed_at < min_interval:
                    await websocket.send_json(
                        {
                            "error": {
                                "code": "RATE_LIMITED",
                                "message": "Frame dropped due to FPS limit.",
                            }
                        }
                    )
                    continue
                frame = FrameMessage.model_validate(payload)
                processed = service.process_frame(frame, db)
                await websocket.send_json(processed.model_dump())
                last_processed_at = now
            except ValidationError as exc:
                await websocket.send_json(
                    {
                        "error": {
                            "code": "INVALID_FRAME",
                            "message": "Invalid frame payload.",
                        },
                        "details": exc.errors(),
                    }
                )
            except StreamServiceError as exc:
                await websocket.send_json(
                    {
                        "error": {
                            "code": "FRAME_PROCESSING_ERROR",
                            "message": str(exc),
                        }
                    }
                )
    except WebSocketDisconnect:
        return
    finally:
        db.close()
