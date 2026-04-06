from __future__ import annotations

from fastapi import APIRouter

from xiaoxinbao.modules.shared.responses import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse)
def health() -> ApiResponse:
    return ApiResponse(data={"status": "ok"})
