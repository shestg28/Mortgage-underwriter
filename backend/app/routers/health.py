from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health_check():
    return {"status": "ok"}
