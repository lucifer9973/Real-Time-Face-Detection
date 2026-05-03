from app.repositories.roi_repository import ROIRepository
from app.schemas.stream import BoundingBox


def test_roi_storage(db):
    repo = ROIRepository(db)
    boxes = [BoundingBox(x=10, y=20, width=100, height=120)]
    saved = repo.save_many(frame_id=7, session_id="session-1", boxes=boxes)

    assert len(saved) == 1
    assert saved[0].frame_id == 7
    assert saved[0].session_id == "session-1"

    listed = repo.list_recent(limit=10)
    assert len(listed) >= 1
    assert listed[0].width == 100
