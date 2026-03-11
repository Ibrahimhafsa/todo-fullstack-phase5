"""Integration tests for chat endpoint (Spec-4, US1)."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.models.conversation import Conversation, Message
from app.models.task import Task


@pytest.fixture
def client():
    """Provide test client."""
    return TestClient(app)


@pytest.fixture
def authenticated_user(db_session: Session):
    """Create test user and return JWT token."""
    # Note: In real tests, use actual Better Auth JWT
    # For MVP: mock user_id = "test-user-1"
    return {
        "user_id": "test-user-1",
        "token": "Bearer mock-jwt-token-for-testing",
    }


class TestChatEndpoint:
    """Tests for POST /api/{user_id}/chat."""

    def test_send_message_creates_conversation(
        self,
        client: TestClient,
        authenticated_user: dict,
    ):
        """Test: Sending first message creates conversation."""
        # Send message without conversation_id
        response = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": "Create a task called 'Buy groceries'"},
            headers={"Authorization": authenticated_user["token"]},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert "conversation_id" in data
        assert data["role"] == "assistant"
        assert data["content"] is not None
        assert "timestamp" in data

    def test_send_message_stores_user_message(
        self,
        client: TestClient,
        authenticated_user: dict,
        db_session: Session,
    ):
        """Test: User message is stored in database."""
        # Send message
        response = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": "List my tasks"},
            headers={"Authorization": authenticated_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        conversation_id = data["conversation_id"]

        # Verify user message stored
        messages = db_session.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == "user",
        ).all()

        assert len(messages) == 1
        assert messages[0].content == "List my tasks"
        assert messages[0].user_id == authenticated_user["user_id"]

    def test_send_message_stores_assistant_response(
        self,
        client: TestClient,
        authenticated_user: dict,
        db_session: Session,
    ):
        """Test: Assistant response is stored in database."""
        # Send message
        response = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": "Hello"},
            headers={"Authorization": authenticated_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        conversation_id = data["conversation_id"]

        # Verify assistant response stored
        messages = db_session.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == "assistant",
        ).all()

        assert len(messages) == 1
        assert messages[0].content is not None
        assert messages[0].user_id == authenticated_user["user_id"]

    def test_empty_message_returns_400(
        self,
        client: TestClient,
        authenticated_user: dict,
    ):
        """Test: Empty message rejected."""
        response = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": ""},
            headers={"Authorization": authenticated_user["token"]},
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_missing_jwt_returns_401(
        self,
        client: TestClient,
        authenticated_user: dict,
    ):
        """Test: Missing JWT returns 401."""
        response = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": "Hello"},
            # No Authorization header
        )

        assert response.status_code == 401

    def test_rate_limiting(
        self,
        client: TestClient,
        authenticated_user: dict,
    ):
        """Test: Rate limiting enforced (max 20 requests/minute)."""
        # Send 20 successful requests
        for i in range(20):
            response = client.post(
                f"/api/{authenticated_user['user_id']}/chat",
                json={"message": f"Message {i}"},
                headers={"Authorization": authenticated_user["token"]},
            )
            assert response.status_code == 200

        # 21st request should be rate limited
        response = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": "This should be rate limited"},
            headers={"Authorization": authenticated_user["token"]},
        )

        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()


class TestConversationCRUD:
    """Tests for conversation list, get, delete."""

    def test_list_conversations(
        self,
        client: TestClient,
        authenticated_user: dict,
        db_session: Session,
    ):
        """Test: List conversations returns all user's conversations."""
        # Create 2 conversations
        for i in range(2):
            response = client.post(
                f"/api/{authenticated_user['user_id']}/chat",
                json={"message": f"Message {i}"},
                headers={"Authorization": authenticated_user["token"]},
            )
            assert response.status_code == 200

        # List conversations
        response = client.get(
            f"/api/{authenticated_user['user_id']}/conversations",
            headers={"Authorization": authenticated_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("id" in item for item in data)
        assert all("created_at" in item for item in data)
        assert all("message_count" in item for item in data)

    def test_get_conversation_detail(
        self,
        client: TestClient,
        authenticated_user: dict,
    ):
        """Test: Get conversation returns full history."""
        # Create conversation with multiple messages
        response1 = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": "First message"},
            headers={"Authorization": authenticated_user["token"]},
        )
        conversation_id = response1.json()["conversation_id"]

        response2 = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"conversation_id": conversation_id, "message": "Second message"},
            headers={"Authorization": authenticated_user["token"]},
        )

        # Get conversation
        response = client.get(
            f"/api/{authenticated_user['user_id']}/conversations/{conversation_id}",
            headers={"Authorization": authenticated_user["token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert len(data["messages"]) == 4  # 2 user + 2 assistant
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

    def test_delete_conversation(
        self,
        client: TestClient,
        authenticated_user: dict,
        db_session: Session,
    ):
        """Test: Delete conversation removes all messages."""
        # Create conversation
        response = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": "Test"},
            headers={"Authorization": authenticated_user["token"]},
        )
        conversation_id = response.json()["conversation_id"]

        # Delete conversation
        response = client.delete(
            f"/api/{authenticated_user['user_id']}/conversations/{conversation_id}",
            headers={"Authorization": authenticated_user["token"]},
        )

        assert response.status_code == 204

        # Verify deleted
        response = client.get(
            f"/api/{authenticated_user['user_id']}/conversations/{conversation_id}",
            headers={"Authorization": authenticated_user["token"]},
        )

        assert response.status_code == 404

    def test_ownership_enforcement(
        self,
        client: TestClient,
        authenticated_user: dict,
    ):
        """Test: Cross-user access blocked."""
        # Create conversation as user 1
        response = client.post(
            f"/api/{authenticated_user['user_id']}/chat",
            json={"message": "Test"},
            headers={"Authorization": authenticated_user["token"]},
        )
        conversation_id = response.json()["conversation_id"]

        # Try to access as user 2
        # Note: In real tests, use different JWT token
        response = client.get(
            f"/api/different-user-id/conversations/{conversation_id}",
            headers={"Authorization": authenticated_user["token"]},
        )

        # Should be 401 because JWT user doesn't match path user
        assert response.status_code == 401
