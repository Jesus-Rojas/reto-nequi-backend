from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import DuplicateMessageException
from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate
from app.services.content_filter import ContentFilterService
from app.services.message_service import MessageService


def _make_service(
    existing_message: Message | None = None,
    forbidden_words: list[str] | None = None,
) -> tuple[MessageService, MagicMock]:
    repo = MagicMock(spec=MessageRepository)
    repo.get_by_message_id.return_value = existing_message
    content_filter = ContentFilterService(forbidden_words=forbidden_words or [])
    svc = MessageService(repository=repo, content_filter=content_filter)
    return svc, repo


def _valid_payload(**overrides) -> MessageCreate:
    data = {
        "message_id": "msg-001",
        "session_id": "session-xyz",
        "content": "Hola mundo",
        "timestamp": datetime(2024, 1, 15, 10, 0, 0),
        "sender": "user",
    }
    data.update(overrides)
    return MessageCreate(**data)


def _stub_message(payload: MessageCreate) -> Message:
    msg = Message(
        message_id=payload.message_id,
        session_id=payload.session_id,
        content=payload.content,
        timestamp=payload.timestamp,
        sender=payload.sender,
        word_count=2,
        character_count=10,
        processed_at=datetime(2024, 1, 15, 10, 0, 1),
        is_filtered=False,
        created_at=datetime(2024, 1, 15, 10, 0, 1),
    )
    return msg


class TestProcessAndStore:
    def test_happy_path_returns_message_data(self):
        payload = _valid_payload()
        svc, repo = _make_service()
        stub = _stub_message(payload)
        repo.create.return_value = stub

        result = svc.process_and_store(payload)

        repo.create.assert_called_once()
        assert result.message_id == payload.message_id
        assert result.session_id == payload.session_id

    def test_raises_duplicate_when_message_id_exists(self):
        payload = _valid_payload()
        existing = _stub_message(payload)
        svc, repo = _make_service(existing_message=existing)

        with pytest.raises(DuplicateMessageException) as exc_info:
            svc.process_and_store(payload)

        assert exc_info.value.code == "DUPLICATE_MESSAGE"
        repo.create.assert_not_called()

    def test_filters_inappropriate_content(self):
        payload = _valid_payload(content="Este mensaje contiene banana inapropiado")
        svc, repo = _make_service(forbidden_words=["banana"])

        stub = _stub_message(payload)
        stub.content = "Este mensaje contiene ****** inapropiado"
        stub.is_filtered = True
        repo.create.return_value = stub

        result = svc.process_and_store(payload)

        created_message: Message = repo.create.call_args[0][0]
        assert "banana" not in created_message.content.lower()
        assert created_message.is_filtered is True
        assert result.metadata.is_filtered is True

    def test_metadata_word_count_is_correct(self):
        payload = _valid_payload(content="uno dos tres")
        svc, repo = _make_service()
        stub = _stub_message(payload)
        stub.word_count = 3
        stub.character_count = 13
        repo.create.return_value = stub

        result = svc.process_and_store(payload)

        created: Message = repo.create.call_args[0][0]
        assert created.word_count == 3
        assert result.metadata.word_count == 3

    def test_metadata_character_count_is_correct(self):
        payload = _valid_payload(content="hola")
        svc, repo = _make_service()
        stub = _stub_message(payload)
        stub.character_count = 4
        repo.create.return_value = stub

        result = svc.process_and_store(payload)

        created: Message = repo.create.call_args[0][0]
        assert created.character_count == 4


class TestGetSessionMessages:
    def test_returns_mapped_schemas(self):
        payload = _valid_payload()
        stub = _stub_message(payload)
        svc, repo = _make_service()
        repo.get_by_session_id.return_value = ([stub], 1)

        results, total = svc.get_session_messages("session-xyz", None, 20, 0)

        assert total == 1
        assert len(results) == 1
        assert results[0].session_id == "session-xyz"

    def test_passes_sender_filter_to_repo(self):
        svc, repo = _make_service()
        repo.get_by_session_id.return_value = ([], 0)

        svc.get_session_messages("sess", "user", 10, 5)

        repo.get_by_session_id.assert_called_once_with(
            session_id="sess", sender="user", limit=10, offset=5
        )


class TestSearchMessages:
    def test_passes_keyword_and_session_to_repo(self):
        svc, repo = _make_service()
        repo.search.return_value = ([], 0)

        svc.search_messages("hola", "sess-1", 10, 0)

        repo.search.assert_called_once_with(
            keyword="hola", session_id="sess-1", limit=10, offset=0
        )

    def test_returns_empty_list_when_no_results(self):
        svc, repo = _make_service()
        repo.search.return_value = ([], 0)

        results, total = svc.search_messages("nada", None, 20, 0)

        assert results == []
        assert total == 0
