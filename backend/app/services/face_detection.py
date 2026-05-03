import base64
import binascii
import io

import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw

from app.schemas.stream import BoundingBox


class FaceDetectionError(Exception):
    pass


class FaceDetectorService:
    def __init__(self):
        self._detector = mp.solutions.face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )

    def detect_and_draw(
        self, image_b64: str, max_frame_bytes: int
    ) -> tuple[str, list[BoundingBox]]:
        image_bytes = self._decode_base64(image_b64)
        if len(image_bytes) > max_frame_bytes:
            raise FaceDetectionError("Frame payload exceeds allowed size.")

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:  # noqa: BLE001
            raise FaceDetectionError("Invalid image payload.") from exc

        image_np = np.array(image)
        results = self._detector.process(image_np)

        boxes: list[BoundingBox] = []
        if results.detections:
            draw = ImageDraw.Draw(image)
            img_w, img_h = image.size
            for detection in results.detections:
                rel_box = detection.location_data.relative_bounding_box
                x = max(0, int(rel_box.xmin * img_w))
                y = max(0, int(rel_box.ymin * img_h))
                width = int(rel_box.width * img_w)
                height = int(rel_box.height * img_h)
                box = BoundingBox(x=x, y=y, width=width, height=height)
                boxes.append(box)
                draw.rectangle([x, y, x + width, y + height], outline="red", width=3)

        return self._encode_base64(image), boxes

    @staticmethod
    def _decode_base64(data: str) -> bytes:
        if "," in data:
            data = data.split(",", 1)[1]
        try:
            return base64.b64decode(data, validate=True)
        except binascii.Error as exc:
            raise FaceDetectionError("Frame is not valid base64.") from exc

    @staticmethod
    def _encode_base64(image: Image.Image) -> str:
        buff = io.BytesIO()
        image.save(buff, format="JPEG")
        return base64.b64encode(buff.getvalue()).decode("utf-8")
