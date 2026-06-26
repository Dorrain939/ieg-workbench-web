from fastapi import APIRouter

router = APIRouter(prefix="/config", tags=["platform-config"])


@router.get("/legacy")
def config_legacy():
    return {"legacy": "config_api.py"}
