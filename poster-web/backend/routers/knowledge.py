from fastapi import APIRouter

router = APIRouter(prefix="/knowledge", tags=["platform-knowledge"])


@router.get("/legacy")
def knowledge_legacy():
    return {"legacy": "kb_api.py"}
