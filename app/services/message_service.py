from datetime import datetime, timezone

from app.core.exceptions import DuplicateMessageException
from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate, MessageData, MessageMetadata
from app.services.content_filter import ContentFilterService


class MessageService:
    """Orchestrates validation, content filtering, persistence and retrieval."""

    def __init__(
        self,
        repository: MessageRepository,
        content_filter: ContentFilterService,
    ):
        self._repository = repository
        self._content_filter = content_filter

    # ── Commands ──────────────────────────────────────────────────────────────

    def process_and_store(self, payload: MessageCreate) -> MessageData:
        if self._repository.get_by_message_id(payload.message_id):
            raise DuplicateMessageException(payload.message_id)

        filtered_content, was_filtered = self._content_filter.filter_content(
            payload.content
        )
        processed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        message = Message(
            message_id=payload.message_id,
            session_id=payload.session_id,
            content=filtered_content,
            timestamp=payload.timestamp.replace(tzinfo=None),
            sender=payload.sender,
            word_count=len(filtered_content.split()),
            character_count=len(filtered_content),
            processed_at=processed_at,
            is_filtered=was_filtered,
        )
        saved = self._repository.create(message)
        return self._to_schema(saved)

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_session_messages(
        self,
        session_id: str,
        sender: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[MessageData], int]:
        messages, total = self._repository.get_by_session_id(
            session_id=session_id,
            sender=sender,
            limit=limit,
            offset=offset,
        )
        return [self._to_schema(m) for m in messages], total

    def search_messages(
        self,
        keyword: str,
        session_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[MessageData], int]:
        messages, total = self._repository.search(
            keyword=keyword,
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
        return [self._to_schema(m) for m in messages], total

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _to_schema(message: Message) -> MessageData:
        fallback_dt = message.processed_at or message.created_at
        return MessageData(
            message_id=message.message_id,
            session_id=message.session_id,
            content=message.content,
            timestamp=message.timestamp,
            sender=message.sender,
            metadata=MessageMetadata(
                word_count=message.word_count or 0,
                character_count=message.character_count or 0,
                processed_at=fallback_dt,
                is_filtered=message.is_filtered,
            ),
        )
