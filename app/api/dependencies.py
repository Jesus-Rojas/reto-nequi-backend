from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.exceptions import UnauthorizedException
from app.database import get_db
from app.repositories.message_repository import MessageRepository
from app.services.content_filter import ContentFilterService
from app.services.message_service import MessageService


def get_message_repository(db: Session = Depends(get_db)) -> MessageRepository:
    return MessageRepository(db)


def get_content_filter() -> ContentFilterService:
    return ContentFilterService()


def get_message_service(
    repository: MessageRepository = Depends(get_message_repository),
    content_filter: ContentFilterService = Depends(get_content_filter),
) -> MessageService:
    return MessageService(repository=repository, content_filter=content_filter)


def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise UnauthorizedException()
