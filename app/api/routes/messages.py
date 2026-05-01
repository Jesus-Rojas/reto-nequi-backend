from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

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

# ── REST endpoints ────────────────────────────────────────────────────────────


@router.post(
    "/api/messages",
    response_model=MessageResponse,
    status_code=201,
    summary="Enviar un mensaje",
    dependencies=[Depends(verify_api_key)],
)
async def create_message(
    payload: MessageCreate,
    service: MessageService = Depends(get_message_service),
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
    response_model=PaginatedMessagesResponse,
    summary="Buscar mensajes por palabra clave",
    dependencies=[Depends(verify_api_key)],
)
def search_messages(
    keyword: str = Query(..., min_length=1, description="Término de búsqueda"),
    session_id: str | None = Query(None, description="Filtrar por sesión"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: MessageService = Depends(get_message_service),
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
    response_model=PaginatedMessagesResponse,
    summary="Obtener mensajes de una sesión",
    dependencies=[Depends(verify_api_key)],
)
def get_session_messages(
    session_id: str,
    sender: str | None = Query(
        None, pattern="^(user|system)$", description="Filtrar por remitente"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Orden de resultados"),
    service: MessageService = Depends(get_message_service),
) -> PaginatedMessagesResponse:
    """Devuelve todos los mensajes de *session_id* con soporte de paginación."""
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
