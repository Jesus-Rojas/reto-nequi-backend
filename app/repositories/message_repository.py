from app.models.message import Message
from sqlalchemy.orm import Session


class MessageRepository:
    """Data-access layer — all database operations for Message entities."""

    def __init__(self, db: Session):
        self._db = db

    def create(self, message: Message) -> Message:
        self._db.add(message)
        self._db.commit()
        self._db.refresh(message)
        return message

    def get_by_message_id(self, message_id: str) -> Message | None:
        return (
            self._db.query(Message)
            .filter(Message.message_id == message_id)
            .first()
        )

    def get_by_session_id(
        self,
        session_id: str,
        sender: str | None = None,
        limit: int = 20,
        offset: int = 0,
        order: str = "asc",
    ) -> tuple[list[Message], int]:
        query = self._db.query(Message).filter(Message.session_id == session_id)
        if sender:
            query = query.filter(Message.sender == sender)
        total = query.count()
        order_col = Message.timestamp.desc() if order == "desc" else Message.timestamp
        messages = (
            query.order_by(order_col).offset(offset).limit(limit).all()
        )
        return messages, total

    def search(
        self,
        keyword: str,
        session_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Message], int]:
        query = self._db.query(Message).filter(
            Message.content.ilike(f"%{keyword}%")
        )
        if session_id:
            query = query.filter(Message.session_id == session_id)
        total = query.count()
        messages = (
            query.order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()
        )
        return messages, total
