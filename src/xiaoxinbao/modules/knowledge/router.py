from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from xiaoxinbao.bootstrap import ServiceContainer, get_container
from xiaoxinbao.modules.knowledge.schemas import KnowledgeHitData, KnowledgeSearchRequest
from xiaoxinbao.modules.shared.responses import ApiResponse

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])
ContainerDep = Annotated[ServiceContainer, Depends(get_container)]


@router.post("/search", response_model=ApiResponse)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    container: ContainerDep,
) -> ApiResponse:
    hits = container.retriever.search(
        query=request.query,
        limit=request.limit,
        strategy=request.strategy,
    )
    data = {
        "query": request.query,
        "strategy": request.strategy or container.settings.retrieval_mode,
        "hits": [KnowledgeHitData(**hit.model_dump()).model_dump() for hit in hits],
    }
    return ApiResponse(data=data)
