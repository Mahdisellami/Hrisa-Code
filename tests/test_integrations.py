"""Tests for webhook and notification integrations."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import json

from hrisa_code.web.agent_manager import (
    WebAgentManager,
    WebhookConfig,
    NotificationChannel,
    WebhookEvent,
)
from hrisa_code.core.config import Config


@pytest.fixture
def agent_manager():
    """Create agent manager instance."""
    config = Config.get_default()
    return WebAgentManager(config=config)


@pytest.mark.asyncio
class TestWebhookIntegration:
    """Test webhook functionality."""

    async def test_add_webhook(self, agent_manager):
        """Test adding a webhook."""
        webhook_id = agent_manager.add_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.completed", "agent.failed"],
            secret="test-secret"
        )

        assert webhook_id in agent_manager.webhooks
        webhook = agent_manager.webhooks[webhook_id]
        assert webhook.name == "Test Webhook"
        assert webhook.url == "https://example.com/webhook"
        assert len(webhook.events) == 2
        assert webhook.secret == "test-secret"
        assert webhook.enabled is True

    async def test_update_webhook(self, agent_manager):
        """Test updating a webhook."""
        webhook_id = agent_manager.add_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.completed"]
        )

        success = agent_manager.update_webhook(
            webhook_id,
            enabled=False,
            events=["agent.completed", "agent.failed"]
        )

        assert success is True
        webhook = agent_manager.webhooks[webhook_id]
        assert webhook.enabled is False
        assert len(webhook.events) == 2

    async def test_delete_webhook(self, agent_manager):
        """Test deleting a webhook."""
        webhook_id = agent_manager.add_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.completed"]
        )

        success = agent_manager.delete_webhook(webhook_id)

        assert success is True
        assert webhook_id not in agent_manager.webhooks

    async def test_get_webhooks(self, agent_manager):
        """Test getting all webhooks."""
        webhook_id1 = agent_manager.add_webhook(
            name="Webhook 1",
            url="https://example.com/webhook1",
            events=["agent.completed"]
        )
        webhook_id2 = agent_manager.add_webhook(
            name="Webhook 2",
            url="https://example.com/webhook2",
            events=["agent.failed"]
        )

        webhooks = agent_manager.get_webhooks()

        assert len(webhooks) == 2
        assert any(w.id == webhook_id1 for w in webhooks)
        assert any(w.id == webhook_id2 for w in webhooks)

    @patch('aiohttp.ClientSession')
    async def test_trigger_webhooks_success(self, mock_session_class, agent_manager):
        """Test successfully triggering webhooks."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session_class.return_value = mock_session

        # Add webhook
        webhook_id = agent_manager.add_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.completed"],
            secret="test-secret"
        )

        # Trigger webhook
        payload = {
            "agent_id": "agent-123",
            "status": "completed",
            "task": "Test task"
        }
        await agent_manager.trigger_webhooks("agent.completed", payload)

        # Verify webhook was called
        webhook = agent_manager.webhooks[webhook_id]
        assert webhook.trigger_count == 1
        assert webhook.failure_count == 0

        # Verify event was recorded
        events = agent_manager.get_webhook_events(webhook_id)
        assert len(events) == 1
        assert events[0].success is True
        assert events[0].event_type == "agent.completed"

    @patch('aiohttp.ClientSession')
    async def test_trigger_webhooks_failure(self, mock_session_class, agent_manager):
        """Test webhook trigger failure handling."""
        # Setup mock to raise exception
        mock_session = AsyncMock()
        mock_session.post.side_effect = Exception("Connection failed")
        mock_session.__aenter__.return_value = mock_session
        mock_session_class.return_value = mock_session

        # Add webhook
        webhook_id = agent_manager.add_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.completed"]
        )

        # Trigger webhook
        payload = {"agent_id": "agent-123"}
        await agent_manager.trigger_webhooks("agent.completed", payload)

        # Verify failure was recorded
        webhook = agent_manager.webhooks[webhook_id]
        assert webhook.failure_count == 1

        events = agent_manager.get_webhook_events(webhook_id)
        assert len(events) == 1
        assert events[0].success is False
        assert events[0].error is not None

    async def test_trigger_webhooks_disabled(self, agent_manager):
        """Test that disabled webhooks are not triggered."""
        webhook_id = agent_manager.add_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["agent.completed"]
        )
        agent_manager.update_webhook(webhook_id, enabled=False)

        payload = {"agent_id": "agent-123"}
        await agent_manager.trigger_webhooks("agent.completed", payload)

        # Verify webhook was not triggered
        webhook = agent_manager.webhooks[webhook_id]
        assert webhook.trigger_count == 0


@pytest.mark.asyncio
class TestNotificationChannels:
    """Test notification channel functionality."""

    async def test_add_notification_channel(self, agent_manager):
        """Test adding a notification channel."""
        channel_id = agent_manager.add_notification_channel(
            name="Slack Alerts",
            channel_type="slack",
            config={"webhook_url": "https://hooks.slack.com/test"},
            events=["agent.completed"]
        )

        assert channel_id in agent_manager.notification_channels
        channel = agent_manager.notification_channels[channel_id]
        assert channel.name == "Slack Alerts"
        assert channel.type == "slack"
        assert channel.enabled is True

    async def test_update_notification_channel(self, agent_manager):
        """Test updating a notification channel."""
        channel_id = agent_manager.add_notification_channel(
            name="Slack Alerts",
            channel_type="slack",
            config={"webhook_url": "https://hooks.slack.com/test"},
            events=["agent.completed"]
        )

        success = agent_manager.update_notification_channel(
            channel_id,
            enabled=False,
            events=["agent.completed", "agent.failed"]
        )

        assert success is True
        channel = agent_manager.notification_channels[channel_id]
        assert channel.enabled is False
        assert len(channel.events) == 2

    async def test_delete_notification_channel(self, agent_manager):
        """Test deleting a notification channel."""
        channel_id = agent_manager.add_notification_channel(
            name="Slack Alerts",
            channel_type="slack",
            config={"webhook_url": "https://hooks.slack.com/test"},
            events=["agent.completed"]
        )

        success = agent_manager.delete_notification_channel(channel_id)

        assert success is True
        assert channel_id not in agent_manager.notification_channels

    @patch('aiohttp.ClientSession')
    async def test_send_slack_notification(self, mock_session_class, agent_manager):
        """Test sending Slack notification."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.__aenter__.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session_class.return_value = mock_session

        channel_id = agent_manager.add_notification_channel(
            name="Slack Alerts",
            channel_type="slack",
            config={"webhook_url": "https://hooks.slack.com/test"},
            events=["agent.completed"]
        )

        payload = {
            "agent_id": "agent-123",
            "status": "completed",
            "task": "Test task"
        }
        await agent_manager.send_notifications("agent.completed", payload)

        channel = agent_manager.notification_channels[channel_id]
        assert channel.send_count == 1
        assert channel.failure_count == 0

    @patch('aiohttp.ClientSession')
    async def test_send_discord_notification(self, mock_session_class, agent_manager):
        """Test sending Discord notification."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.__aenter__.return_value = mock_response

        mock_session = AsyncMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__.return_value = mock_session
        mock_session_class.return_value = mock_session

        channel_id = agent_manager.add_notification_channel(
            name="Discord Alerts",
            channel_type="discord",
            config={"webhook_url": "https://discord.com/api/webhooks/test"},
            events=["agent.failed"]
        )

        payload = {
            "agent_id": "agent-123",
            "status": "failed",
            "task": "Test task"
        }
        await agent_manager.send_notifications("agent.failed", payload)

        channel = agent_manager.notification_channels[channel_id]
        assert channel.send_count == 1

    async def test_send_notifications_disabled_channel(self, agent_manager):
        """Test that disabled channels don't send notifications."""
        channel_id = agent_manager.add_notification_channel(
            name="Slack Alerts",
            channel_type="slack",
            config={"webhook_url": "https://hooks.slack.com/test"},
            events=["agent.completed"]
        )
        agent_manager.update_notification_channel(channel_id, enabled=False)

        payload = {"agent_id": "agent-123"}
        await agent_manager.send_notifications("agent.completed", payload)

        channel = agent_manager.notification_channels[channel_id]
        assert channel.send_count == 0


class TestWebhookEvents:
    """Test webhook event history."""

    def test_get_webhook_events_all(self, agent_manager):
        """Test getting all webhook events."""
        # Add some events manually
        event1 = WebhookEvent(
            id="event-1",
            webhook_id="webhook-1",
            event_type="agent.completed",
            timestamp=datetime.now(),
            payload={},
            success=True
        )
        event2 = WebhookEvent(
            id="event-2",
            webhook_id="webhook-2",
            event_type="agent.failed",
            timestamp=datetime.now(),
            payload={},
            success=False
        )
        agent_manager.webhook_events.extend([event1, event2])

        events = agent_manager.get_webhook_events()

        assert len(events) == 2

    def test_get_webhook_events_filtered(self, agent_manager):
        """Test getting webhook events filtered by webhook_id."""
        event1 = WebhookEvent(
            id="event-1",
            webhook_id="webhook-1",
            event_type="agent.completed",
            timestamp=datetime.now(),
            payload={},
            success=True
        )
        event2 = WebhookEvent(
            id="event-2",
            webhook_id="webhook-2",
            event_type="agent.failed",
            timestamp=datetime.now(),
            payload={},
            success=False
        )
        agent_manager.webhook_events.extend([event1, event2])

        events = agent_manager.get_webhook_events(webhook_id="webhook-1")

        assert len(events) == 1
        assert events[0].id == "event-1"

    def test_get_webhook_events_limit(self, agent_manager):
        """Test limiting webhook events returned."""
        for i in range(10):
            event = WebhookEvent(
                id=f"event-{i}",
                webhook_id="webhook-1",
                event_type="agent.completed",
                timestamp=datetime.now(),
                payload={},
                success=True
            )
            agent_manager.webhook_events.append(event)

        events = agent_manager.get_webhook_events(limit=5)

        assert len(events) == 5
