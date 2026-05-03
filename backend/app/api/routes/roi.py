from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.roi_repository import ROIRepository
from app.schemas.roi import ROIResponse

router = APIRouter(prefix="/roi", tags=["roi"])


@router.get("", response_model=list[ROIResponse])
def get_roi_data(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[ROIResponse]:
    try:
        rows = ROIRepository(db).list_recent(limit=limit)
        return [ROIResponse.model_validate(row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "DB_FAILURE",
                    "message": "Failed to fetch ROI data.",
                }
            },
        ) from exc
