from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.roi import ROIData
from app.schemas.stream import BoundingBox


class ROIRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_many(
        self, frame_id: int, session_id: str, boxes: list[BoundingBox]
    ) -> list[ROIData]:
        rows = [
            ROIData(
                frame_id=frame_id,
                session_id=session_id,
                x=box.x,
                y=box.y,
                width=box.width,
                height=box.height,
            )
            for box in boxes
        ]
        try:
            self.db.add_all(rows)
            self.db.commit()
            for row in rows:
                self.db.refresh(row)
            return rows
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def list_recent(self, limit: int = 50) -> Sequence[ROIData]:
        stmt = select(ROIData).order_by(desc(ROIData.timestamp)).limit(limit)
        return self.db.execute(stmt).scalars().all()
