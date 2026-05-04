from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from starlette import status

from app.api.dependencies import get_message_service, verify_api_key
from app.api.websocket_manager import manager
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    PaginatedMessagesResponse,
    PaginationInfo,
)
from app.services.message_service import MessageService

router = APIRouter()

# ── Dependency aliases ────────────────────────────────────────────────────────

ServiceDep = Annotated[MessageService, Depends(get_message_service)]
ApiKeyDep = Annotated[None, Depends(verify_api_key)]

# ── REST endpoints ────────────────────────────────────────────────────────────


@router.post(
    "/api/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Enviar un mensaje",
)
async def create_message(
    payload: MessageCreate,
    service: ServiceDep,
    _: ApiKeyDep,
) -> MessageResponse:
    """Valida, procesa y almacena un mensaje. Notifica a clientes WebSocket."""
    data = service.process_and_store(payload)
    await manager.broadcast_to_session(
        payload.session_id,
        {"event": "new_message", "data": data.model_dump(mode="json")},
    )
    return MessageResponse(status="success", data=data)


# NOTE: This route MUST be defined before /{session_id} so that the literal
# path "/api/messages/search" is not swallowed by the parameterised route.
@router.get(
    "/api/messages/search",
    summary="Buscar mensajes por palabra clave",
)
def search_messages(
    service: ServiceDep,
    _: ApiKeyDep,
    keyword: Annotated[str, Query(min_length=1, description="Término de búsqueda")],
    session_id: Annotated[str | None, Query(description="Filtrar por sesión")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedMessagesResponse:
    """Busca mensajes que contengan *keyword* en su contenido."""
    messages, total = service.search_messages(
        keyword=keyword,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    return PaginatedMessagesResponse(
        status="success",
        data=messages,
        pagination=PaginationInfo(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.get(
    "/api/messages/{session_id}",
    summary="Obtener mensajes de una sesión",
)
def get_session_messages(
    session_id: str,
    service: ServiceDep,
    _: ApiKeyDep,
    sender: Annotated[str | None, Query(pattern="^(user|system)$", description="Filtrar por remitente")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    order: Annotated[str, Query(pattern="^(asc|desc)$", description="Orden de resultados")] = "asc",
) -> PaginatedMessagesResponse:
    messages, total = service.get_session_messages(
        session_id=session_id,
        sender=sender,
        limit=limit,
        offset=offset,
        order=order,
    )
    return PaginatedMessagesResponse(
        status="success",
        data=messages,
        pagination=PaginationInfo(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


# ── WebSocket endpoint ────────────────────────────────────────────────────────


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str) -> None:
    """Canal en tiempo real para recibir nuevos mensajes de una sesión."""
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Absorb keep-alive pings from the client; ignore content
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
