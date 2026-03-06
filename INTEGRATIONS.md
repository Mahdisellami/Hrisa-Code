# Integrations Guide

Hrisa Code supports integrations with external services through webhooks and notification channels, allowing you to receive real-time updates about agent activities.

## Table of Contents

- [Overview](#overview)
- [Webhooks](#webhooks)
- [Notification Channels](#notification-channels)
- [Event Types](#event-types)
- [Examples](#examples)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## Overview

Integrations allow Hrisa Code to communicate with external services when specific events occur. There are two types of integrations:

1. **Webhooks** - Generic HTTP callbacks to any endpoint
2. **Notification Channels** - Preconfigured integrations (Slack, Discord, Email)

## Webhooks

Webhooks send HTTP POST requests to a URL of your choice when subscribed events occur.

### Creating a Webhook

**Via UI:**
1. Navigate to 🔌 **Integrations** view
2. Click **+ Add Webhook**
3. Fill in the form:
   - **Name**: Descriptive name for the webhook
   - **URL**: The endpoint to send HTTP POST requests to
   - **Events**: Select which events to subscribe to
   - **Secret** (optional): For HMAC signature verification
4. Click **Create Webhook**

**Via API:**

```bash
curl -X POST http://localhost:8000/api/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Webhook",
    "url": "https://example.com/webhook",
    "events": ["agent.completed", "agent.failed"],
    "secret": "your-secret-key"
  }'
```

### Webhook Payload

When an event occurs, Hrisa Code sends a POST request with this structure:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "agent.completed",
  "timestamp": "2026-03-06T10:30:00Z",
  "data": {
    "agent_id": "agent-abc123",
    "status": "completed",
    "task": "Generate README.md",
    "model": "qwen2.5-coder:32b",
    "created_at": "2026-03-06T10:15:00Z",
    "progress": {
      "total_steps": 10,
      "completed_steps": 10,
      "tool_calls": 25,
      "errors": 0
    }
  }
}
```

### HMAC Signature Verification

If you provide a secret when creating a webhook, Hrisa Code will include an `X-Webhook-Signature` header with an HMAC SHA-256 signature.

**Verifying the signature (Python):**

```python
import hmac
import hashlib

def verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify webhook HMAC signature."""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]

    return hmac.compare_digest(expected_signature, signature)

# Usage
@app.post("/webhook")
async def handle_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Webhook-Signature", "")

    if verify_webhook_signature(body, signature, "your-secret-key"):
        payload = await request.json()
        # Process webhook...
        return {"status": "success"}
    else:
        return {"error": "Invalid signature"}, 401
```

**Node.js Example:**

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secret) {
    const expectedSignature = crypto
        .createHmac('sha256', secret)
        .update(payload)
        .digest('hex');

    const receivedSignature = signature.replace('sha256=', '');
    return crypto.timingSafeEqual(
        Buffer.from(expectedSignature),
        Buffer.from(receivedSignature)
    );
}
```

### Managing Webhooks

**List all webhooks:**
```bash
curl http://localhost:8000/api/webhooks
```

**Update a webhook:**
```bash
curl -X PUT http://localhost:8000/api/webhooks/{webhook_id} \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

**Delete a webhook:**
```bash
curl -X DELETE http://localhost:8000/api/webhooks/{webhook_id}
```

**View webhook events:**
```bash
curl http://localhost:8000/api/webhooks/{webhook_id}/events?limit=50
```

## Notification Channels

Notification channels are preconfigured integrations with popular services.

### Slack Integration

**Setup:**
1. Create a Slack Incoming Webhook:
   - Go to https://api.slack.com/apps
   - Create a new app or select existing
   - Enable Incoming Webhooks
   - Add New Webhook to Workspace
   - Copy the webhook URL

2. Add to Hrisa Code:
   - Navigate to 🔌 **Integrations**
   - Click **+ Add Notification**
   - Select **Slack** as type
   - Paste webhook URL
   - Select events to notify on
   - Click **Create Channel**

**Example Message:**

```
Agent Completed
ID: `agent-abc123`
Status: completed
Task: Generate comprehensive README.md
```

### Discord Integration

**Setup:**
1. Create a Discord Webhook:
   - Open Discord server settings
   - Go to Integrations → Webhooks
   - Click "New Webhook"
   - Copy the webhook URL

2. Add to Hrisa Code:
   - Navigate to 🔌 **Integrations**
   - Click **+ Add Notification**
   - Select **Discord** as type
   - Paste webhook URL
   - Select events
   - Click **Create Channel**

**Example Embed:**

Discord messages are sent as rich embeds with color coding:
- 🟢 Green: `agent.completed`
- 🔴 Red: `agent.failed`
- 🟠 Orange: `agent.stuck`
- 🔵 Blue: `agent.started`

### Email Integration

**Setup:**
1. Configure SMTP settings:
   - SMTP host (e.g., smtp.gmail.com)
   - SMTP port (typically 587 for TLS)
   - Authentication credentials

2. Add to Hrisa Code:
   - Navigate to 🔌 **Integrations**
   - Click **+ Add Notification**
   - Select **Email** as type
   - Enter recipient email and SMTP settings
   - Select events
   - Click **Create Channel**

**Note:** Email integration requires SMTP server configuration. For production use, consider using a service like SendGrid, Mailgun, or AWS SES.

## Event Types

Hrisa Code supports the following event types:

| Event Type | Description | When Triggered |
|------------|-------------|----------------|
| `agent.started` | Agent begins execution | When agent is created and starts running |
| `agent.completed` | Agent finishes successfully | When agent completes all tasks without errors |
| `agent.failed` | Agent encounters fatal error | When agent fails due to errors or exceptions |
| `agent.stuck` | Agent appears stuck | When agent has no activity for threshold period |

### Subscribing to Events

You can subscribe to one or more events per webhook/channel:

```json
{
  "events": ["agent.completed", "agent.failed"]
}
```

**Common Patterns:**

- **Success only**: `["agent.completed"]`
- **Failures only**: `["agent.failed", "agent.stuck"]`
- **All events**: `["agent.started", "agent.completed", "agent.failed", "agent.stuck"]`
- **Critical events**: `["agent.failed", "agent.stuck"]`

## Examples

### Example 1: Slack Notification on Completion

1. Get Slack webhook URL from https://api.slack.com/apps
2. Create notification channel:

```bash
curl -X POST http://localhost:8000/api/notifications/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Slack Completions",
    "type": "slack",
    "config": {
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    },
    "events": ["agent.completed"]
  }'
```

3. Start an agent - you'll receive a Slack message when it completes!

### Example 2: Custom Webhook Handler

**FastAPI webhook endpoint:**

```python
from fastapi import FastAPI, Request
import hmac
import hashlib

app = FastAPI()

@app.post("/hrisa-webhook")
async def handle_hrisa_webhook(request: Request):
    # Get signature for verification
    signature = request.headers.get("X-Webhook-Signature", "")
    body = await request.body()

    # Verify signature
    secret = "your-secret-key"
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(f"sha256={expected}", signature):
        return {"error": "Invalid signature"}, 401

    # Process webhook
    payload = await request.json()
    event_type = payload["event_type"]
    agent_data = payload["data"]

    if event_type == "agent.completed":
        print(f"✅ Agent {agent_data['agent_id']} completed!")
        # Send to monitoring system, update database, etc.

    elif event_type == "agent.failed":
        print(f"❌ Agent {agent_data['agent_id']} failed!")
        # Alert on-call engineer, create ticket, etc.

    return {"status": "processed"}
```

### Example 3: Discord Bot Integration

```python
import aiohttp
import asyncio

async def send_discord_notification(webhook_url: str, message: str, color: int):
    """Send notification to Discord."""
    embed = {
        "embeds": [{
            "title": "Hrisa Code Alert",
            "description": message,
            "color": color,
            "timestamp": datetime.now().isoformat()
        }]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=embed) as response:
            return response.status == 204

# Usage
await send_discord_notification(
    webhook_url="https://discord.com/api/webhooks/...",
    message="Agent completed successfully!",
    color=0x00FF00  # Green
)
```

## Security

### Best Practices

1. **Use HMAC Signatures**
   - Always provide a secret when creating webhooks
   - Verify signatures on your webhook endpoint
   - Use strong, randomly generated secrets

2. **HTTPS Only**
   - Only send webhooks to HTTPS endpoints
   - Never use plain HTTP in production

3. **Secret Management**
   - Store secrets in environment variables or secret managers
   - Rotate secrets periodically
   - Never commit secrets to version control

4. **Rate Limiting**
   - Implement rate limiting on webhook endpoints
   - Handle webhook retries gracefully

5. **Validation**
   - Validate webhook payload structure
   - Sanitize data before processing
   - Implement idempotency checks

### Secret Rotation

To rotate a webhook secret:

1. Update the webhook with a new secret
2. Deploy new signature verification code
3. Monitor for failed verifications
4. Remove old secret after verification

```bash
curl -X PUT http://localhost:8000/api/webhooks/{webhook_id} \
  -H "Content-Type: application/json" \
  -d '{"secret": "new-secret-key"}'
```

## Troubleshooting

### Webhook Not Triggering

**Check:**
1. Webhook is enabled: `enabled: true`
2. Event type matches subscription
3. Webhook URL is accessible
4. No firewall blocking requests

**Debug:**
- View webhook events: `/api/webhooks/{id}/events`
- Check failure_count and error messages
- Verify webhook endpoint is responding

### Invalid Signature Errors

**Solutions:**
1. Verify secret matches on both sides
2. Check signature format: `sha256=...`
3. Ensure payload is raw bytes, not parsed JSON
4. Use constant-time comparison (`hmac.compare_digest`)

### Notifications Not Sending

**Check:**
1. Channel is enabled: `enabled: true`
2. Webhook URL is valid
3. Events are subscribed
4. Service endpoint is accessible

**Slack-specific:**
- Verify Incoming Webhooks are enabled in app
- Check webhook URL format: `https://hooks.slack.com/services/...`
- Test webhook with curl

**Discord-specific:**
- Verify webhook URL: `https://discord.com/api/webhooks/...`
- Check server permissions
- Embeds may be disabled in server settings

### Performance Issues

If webhooks cause delays:

1. **Async Processing**: Webhook triggers are async and shouldn't block
2. **Timeout**: Default 10s timeout - increase if needed
3. **Retries**: Failed webhooks are not retried automatically
4. **Disable**: Temporarily disable high-volume webhooks

### Getting Help

- **View Event History**: Check `/api/webhooks/{id}/events` for detailed logs
- **Enable Debug Logging**: Set log level to DEBUG for verbose output
- **Test Manually**: Use curl to test webhook endpoints
- **Check Network**: Verify firewall, DNS, and connectivity

## API Reference

### Webhook Endpoints

```
POST   /api/webhooks                    Create webhook
GET    /api/webhooks                    List all webhooks
GET    /api/webhooks/{id}              Get webhook details
PUT    /api/webhooks/{id}              Update webhook
DELETE /api/webhooks/{id}              Delete webhook
GET    /api/webhooks/{id}/events       Get webhook event history
```

### Notification Channel Endpoints

```
POST   /api/notifications/channels     Create notification channel
GET    /api/notifications/channels     List all channels
GET    /api/notifications/channels/{id}  Get channel details
PUT    /api/notifications/channels/{id}  Update channel
DELETE /api/notifications/channels/{id}  Delete channel
```

### Request Examples

See [API.md](./API.md) for complete API documentation.

---

For more information, see:
- [API Documentation](./API.md)
- [Main README](./README.md)
- [Contributing Guide](./CONTRIBUTING.md)
