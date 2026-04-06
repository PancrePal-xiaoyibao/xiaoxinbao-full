from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

from xiaoxinbao.bootstrap import ServiceContainer, get_container
from xiaoxinbao.modules.shared.responses import ApiResponse

router = APIRouter(prefix="/api/v1/wechat", tags=["wechat"])
PayloadBody = Annotated[dict[str, Any], Body(...)]
ContainerDep = Annotated[ServiceContainer, Depends(get_container)]


@router.post("/gewechat/callback", response_model=ApiResponse)
async def gewechat_callback(
    payload: PayloadBody,
    container: ContainerDep,
) -> ApiResponse:
    result = await container.wechat_service.handle_callback(payload)
    return ApiResponse(data=result.model_dump())
