from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Inbound ──────────────────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    message_id: str = Field(..., min_length=1, max_length=255)
    session_id: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=10_000)
    timestamp: datetime
    sender: Literal["user", "system"]


# ── Outbound ─────────────────────────────────────────────────────────────────

class MessageMetadata(BaseModel):
    word_count: int
    character_count: int
    processed_at: datetime
    is_filtered: bool = False


class MessageData(BaseModel):
    message_id: str
    session_id: str
    content: str
    timestamp: datetime
    sender: str
    metadata: MessageMetadata

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    status: str = "success"
    data: MessageData


class PaginationInfo(BaseModel):
    total: int
    limit: int
    offset: int
    has_more: bool


class PaginatedMessagesResponse(BaseModel):
    status: str = "success"
    data: list[MessageData]
    pagination: PaginationInfo


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: str | None = None


class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail
