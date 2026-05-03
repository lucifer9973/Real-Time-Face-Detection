from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.roi import router as roi_router
from app.api.routes.stream import router as stream_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models.roi import ROIData  # noqa: F401

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    print("🚀 Face Detection Service started on port 8000")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(stream_router)
app.include_router(roi_router)
