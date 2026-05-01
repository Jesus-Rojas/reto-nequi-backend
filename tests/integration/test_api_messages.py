"""Integration tests for /api/messages endpoints."""
import copy

import pytest

from tests.conftest import TEST_API_KEY, VALID_PAYLOAD


# ── POST /api/messages ────────────────────────────────────────────────────────


class TestCreateMessage:
    def test_creates_message_successfully(self, client):
        resp = client.post("/api/messages", json=VALID_PAYLOAD)
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert data["message_id"] == VALID_PAYLOAD["message_id"]
        assert data["session_id"] == VALID_PAYLOAD["session_id"]
        assert data["sender"] == VALID_PAYLOAD["sender"]
        assert "metadata" in data
        assert data["metadata"]["word_count"] > 0
        assert data["metadata"]["character_count"] > 0
        assert "processed_at" in data["metadata"]

    def test_duplicate_message_id_returns_409(self, client):
        client.post("/api/messages", json=VALID_PAYLOAD)
        resp = client.post("/api/messages", json=VALID_PAYLOAD)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "DUPLICATE_MESSAGE"

    def test_invalid_sender_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "message_id": "msg-002", "sender": "bot"}
        resp = client.post("/api/messages", json=payload)
        assert resp.status_code == 422

    def test_missing_required_field_returns_422(self, client):
        payload = copy.copy(VALID_PAYLOAD)
        del payload["content"]
        resp = client.post("/api/messages", json=payload)
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_empty_content_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "message_id": "msg-003", "content": ""}
        resp = client.post("/api/messages", json=payload)
        assert resp.status_code == 422

    def test_invalid_timestamp_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "message_id": "msg-004", "timestamp": "not-a-date"}
        resp = client.post("/api/messages", json=payload)
        assert resp.status_code == 422

    def test_inappropriate_content_is_filtered(self, client):
        payload = {
            **VALID_PAYLOAD,
            "message_id": "msg-filter-001",
            "content": "Este mensaje tiene spam y basura",
        }
        resp = client.post("/api/messages", json=payload)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "spam" not in data["content"].lower()
        assert data["metadata"]["is_filtered"] is True

    def test_user_sender_is_accepted(self, client):
        payload = {**VALID_PAYLOAD, "message_id": "msg-user-001", "sender": "user"}
        resp = client.post("/api/messages", json=payload)
        assert resp.status_code == 201
        assert resp.json()["data"]["sender"] == "user"


# ── GET /api/messages/{session_id} ────────────────────────────────────────────


class TestGetSessionMessages:
    def _create(self, client, message_id: str, session_id: str, sender: str = "user"):
        payload = {
            "message_id": message_id,
            "session_id": session_id,
            "content": f"Contenido del mensaje {message_id}",
            "timestamp": "2024-01-15T10:00:00Z",
            "sender": sender,
        }
        client.post("/api/messages", json=payload)

    def test_returns_messages_for_session(self, client):
        self._create(client, "msg-s1-001", "session-s1")
        self._create(client, "msg-s1-002", "session-s1")
        resp = client.get("/api/messages/session-s1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["pagination"]["total"] == 2
        assert len(body["data"]) == 2

    def test_empty_session_returns_empty_list(self, client):
        resp = client.get("/api/messages/session-nonexistent")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 0
        assert resp.json()["data"] == []

    def test_filter_by_sender(self, client):
        self._create(client, "msg-s2-001", "session-s2", sender="user")
        self._create(client, "msg-s2-002", "session-s2", sender="system")
        resp = client.get("/api/messages/session-s2?sender=user")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(m["sender"] == "user" for m in data)
        assert len(data) == 1

    def test_pagination_limit(self, client):
        for i in range(5):
            self._create(client, f"msg-s3-{i:03}", "session-s3")
        resp = client.get("/api/messages/session-s3?limit=2&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["pagination"]["total"] == 5
        assert body["pagination"]["has_more"] is True

    def test_pagination_offset(self, client):
        for i in range(3):
            self._create(client, f"msg-s4-{i:03}", "session-s4")
        resp = client.get("/api/messages/session-s4?limit=10&offset=2")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_invalid_sender_filter_returns_422(self, client):
        resp = client.get("/api/messages/session-x?sender=robot")
        assert resp.status_code == 422

    def test_messages_isolated_between_sessions(self, client):
        self._create(client, "msg-iso-001", "session-A")
        self._create(client, "msg-iso-002", "session-B")
        resp = client.get("/api/messages/session-A")
        assert resp.json()["pagination"]["total"] == 1


# ── GET /api/messages/search ──────────────────────────────────────────────────


class TestSearchMessages:
    def _create(self, client, message_id: str, session_id: str, content: str):
        payload = {
            "message_id": message_id,
            "session_id": session_id,
            "content": content,
            "timestamp": "2024-01-15T10:00:00Z",
            "sender": "user",
        }
        client.post("/api/messages", json=payload)

    def test_search_returns_matching_messages(self, client):
        self._create(client, "msg-sr-001", "sess-sr", "El pago fue exitoso")
        self._create(client, "msg-sr-002", "sess-sr", "Hola mundo")
        resp = client.get("/api/messages/search?keyword=pago")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 1

    def test_search_case_insensitive(self, client):
        self._create(client, "msg-sr-003", "sess-sr2", "Transferencia realizada")
        resp = client.get("/api/messages/search?keyword=TRANSFERENCIA")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] >= 1

    def test_search_with_session_filter(self, client):
        self._create(client, "msg-sr-004", "sess-a", "nequi app")
        self._create(client, "msg-sr-005", "sess-b", "nequi pago")
        resp = client.get("/api/messages/search?keyword=nequi&session_id=sess-a")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 1

    def test_search_no_results_returns_empty(self, client):
        resp = client.get("/api/messages/search?keyword=zzznoresults999")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_empty_keyword_returns_422(self, client):
        resp = client.get("/api/messages/search?keyword=")
        assert resp.status_code == 422


# ── Authentication ────────────────────────────────────────────────────────────


class TestAuthentication:
    def test_missing_api_key_returns_401(self, authed_client):
        resp = authed_client.post("/api/messages", json=VALID_PAYLOAD)
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    def test_wrong_api_key_returns_401(self, authed_client):
        resp = authed_client.post(
            "/api/messages",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_correct_api_key_is_accepted(self, authed_client):
        resp = authed_client.post(
            "/api/messages",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert resp.status_code == 201


# ── Health check ──────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_check_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
