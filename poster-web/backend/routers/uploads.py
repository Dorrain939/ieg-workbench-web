from fastapi import APIRouter

from backend.services.upload_service import UploadService

router = APIRouter(prefix="/uploads", tags=["platform-uploads"])


@router.get("/root")
def upload_root():
    return {"root": str(UploadService().root)}
