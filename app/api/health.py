from fastapi import APIRouter
from app.models.response import HealthResponse, HealthData

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """Cek status service. Digunakan oleh load balancer dan monitoring."""
    return HealthResponse(code=200, status="success", data=HealthData())
