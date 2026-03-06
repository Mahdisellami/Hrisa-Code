"""Tests for web API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from hrisa_code.web.server import app
from hrisa_code.web.agent_manager import (
    WebAgentManager,
    AgentInfo,
    AgentStatus,
    AgentProgress,
    WebhookConfig,
    NotificationChannel,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_agent_manager():
    """Create mock agent manager."""
    manager = Mock(spec=WebAgentManager)
    manager.agents = {}
    manager.webhooks = {}
    manager.notification_channels = {}
    manager.webhook_events = []
    return manager


@pytest.fixture(autouse=True)
def setup_agent_manager(mock_agent_manager):
    """Setup mock agent manager for all tests."""
    with patch('hrisa_code.web.server.agent_manager', mock_agent_manager):
        yield


class TestWebhookEndpoints:
    """Test webhook management endpoints."""

    def test_create_webhook(self, client, mock_agent_manager):
        """Test creating a webhook."""
        mock_agent_manager.add_webhook.return_value = "webhook-123"
        webhook = WebhookConfig(
            id="webhook-123",
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.completed"],
            enabled=True,
            created_at=datetime.now(),
            trigger_count=0,
            failure_count=0,
        )
        mock_agent_manager.webhooks = {"webhook-123": webhook}

        response = client.post(
            "/api/webhooks",
            json={
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "events": ["agent.completed"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "webhook-123"
        assert data["name"] == "Test Webhook"
        assert data["url"] == "https://example.com/webhook"
        assert data["events"] == ["agent.completed"]
        assert data["enabled"] is True

    def test_list_webhooks(self, client, mock_agent_manager):
        """Test listing webhooks."""
        webhook = WebhookConfig(
            id="webhook-123",
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.completed"],
            enabled=True,
            created_at=datetime.now(),
            trigger_count=5,
            failure_count=0,
        )
        mock_agent_manager.get_webhooks.return_value = [webhook]

        response = client.get("/api/webhooks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "webhook-123"
        assert data[0]["trigger_count"] == 5

    def test_update_webhook(self, client, mock_agent_manager):
        """Test updating a webhook."""
        webhook = WebhookConfig(
            id="webhook-123",
            name="Updated Webhook",
            url="https://example.com/webhook",
            events=["agent.completed", "agent.failed"],
            enabled=False,
            created_at=datetime.now(),
            trigger_count=0,
            failure_count=0,
        )
        mock_agent_manager.update_webhook.return_value = True
        mock_agent_manager.webhooks = {"webhook-123": webhook}

        response = client.put(
            "/api/webhooks/webhook-123",
            json={"enabled": False, "events": ["agent.completed", "agent.failed"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert len(data["events"]) == 2

    def test_delete_webhook(self, client, mock_agent_manager):
        """Test deleting a webhook."""
        mock_agent_manager.delete_webhook.return_value = True

        response = client.delete("/api/webhooks/webhook-123")

        assert response.status_code == 200
        assert response.json()["message"] == "Webhook deleted successfully"

    def test_delete_webhook_not_found(self, client, mock_agent_manager):
        """Test deleting non-existent webhook."""
        mock_agent_manager.delete_webhook.return_value = False

        response = client.delete("/api/webhooks/nonexistent")

        assert response.status_code == 404


class TestNotificationEndpoints:
    """Test notification channel management endpoints."""

    def test_create_notification_channel(self, client, mock_agent_manager):
        """Test creating a notification channel."""
        mock_agent_manager.add_notification_channel.return_value = "channel-123"
        channel = NotificationChannel(
            id="channel-123",
            name="Slack Alerts",
            type="slack",
            config={"webhook_url": "https://hooks.slack.com/test"},
            events=["agent.completed"],
            enabled=True,
            created_at=datetime.now(),
            send_count=0,
            failure_count=0,
        )
        mock_agent_manager.notification_channels = {"channel-123": channel}

        response = client.post(
            "/api/notifications/channels",
            json={
                "name": "Slack Alerts",
                "type": "slack",
                "config": {"webhook_url": "https://hooks.slack.com/test"},
                "events": ["agent.completed"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "channel-123"
        assert data["name"] == "Slack Alerts"
        assert data["type"] == "slack"

    def test_list_notification_channels(self, client, mock_agent_manager):
        """Test listing notification channels."""
        channel = NotificationChannel(
            id="channel-123",
            name="Slack Alerts",
            type="slack",
            config={},
            events=["agent.completed"],
            enabled=True,
            created_at=datetime.now(),
            send_count=10,
            failure_count=1,
        )
        mock_agent_manager.get_notification_channels.return_value = [channel]

        response = client.get("/api/notifications/channels")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["send_count"] == 10
        assert data[0]["failure_count"] == 1

    def test_update_notification_channel(self, client, mock_agent_manager):
        """Test updating a notification channel."""
        channel = NotificationChannel(
            id="channel-123",
            name="Slack Alerts",
            type="slack",
            config={},
            events=["agent.completed"],
            enabled=False,
            created_at=datetime.now(),
            send_count=0,
            failure_count=0,
        )
        mock_agent_manager.update_notification_channel.return_value = True
        mock_agent_manager.notification_channels = {"channel-123": channel}

        response = client.put(
            "/api/notifications/channels/channel-123",
            json={"enabled": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False

    def test_delete_notification_channel(self, client, mock_agent_manager):
        """Test deleting a notification channel."""
        mock_agent_manager.delete_notification_channel.return_value = True

        response = client.delete("/api/notifications/channels/channel-123")

        assert response.status_code == 200


class TestExportEndpoints:
    """Test export endpoints."""

    def test_export_session(self, client, mock_agent_manager):
        """Test session export."""
        mock_agent_manager.agents = {}
        mock_agent_manager.teams = []
        mock_agent_manager.model_metrics = {}

        response = client.get("/api/export/session")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "export_timestamp" in data
        assert "agents" in data
        assert "teams" in data
        assert "statistics" in data

    def test_export_analytics(self, client, mock_agent_manager):
        """Test analytics export."""
        mock_agent_manager.agents = {}
        mock_agent_manager.teams = []

        response = client.get("/api/export/analytics")

        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "summary" in data
        assert "agent_statistics" in data
        assert "performance_metrics" in data
