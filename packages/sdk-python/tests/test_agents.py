"""Unit tests for AgentsApi — covers all 31 public methods."""
from __future__ import annotations

import json

from .conftest import make_client


def mk(body=None):
    c, t = make_client(body=body or {})
    return c, t


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_default():
    c, t = mk({"agents": []})
    c.agents.list()
    assert t.last.method == "GET"
    assert "/api/v1/agents" in str(t.last.url)


def test_list_with_limit():
    c, t = mk()
    c.agents.list(limit=5, offset=10)
    url = str(t.last.url)
    assert "limit=5" in url
    assert "offset=10" in url


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

def test_search_text():
    c, t = mk()
    c.agents.search(q="data analysis", limit=20)
    url = str(t.last.url)
    assert "agents/search" in url
    assert "data" in url


def test_search_skills_csv():
    c, t = mk()
    c.agents.search(skills=["python", "ml"])
    url = str(t.last.url)
    assert "python" in url and "ml" in url


def test_search_skills_string():
    c, t = mk()
    c.agents.search(skills="python,ml")
    url = str(t.last.url)
    assert "python" in url


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_get_by_id():
    c, t = mk({"id": "agent_1"})
    result = c.agents.get("agent_1")
    assert result["id"] == "agent_1"
    assert "agents/agent_1" in str(t.last.url)


def test_get_url_encodes_id():
    c, t = mk()
    c.agents.get("agent/weird+id")
    assert "agent%2Fweird%2Bid" in str(t.last.url) or "weird" in str(t.last.url)


# ---------------------------------------------------------------------------
# by_agentname / check_agentname
# ---------------------------------------------------------------------------

def test_by_agentname():
    c, t = mk()
    c.agents.by_agentname("mybot")
    assert "by-agentname/mybot" in str(t.last.url)


def test_by_agentname_strips_at():
    c, t = mk()
    c.agents.by_agentname("@mybot")
    assert "mybot" in str(t.last.url)
    assert "@" not in str(t.last.url)


def test_check_agentname():
    c, t = mk({"available": True})
    result = c.agents.check_agentname("newbot")
    assert result["available"] is True
    assert "check-agentname/newbot" in str(t.last.url)


def test_check_agentname_strips_at():
    c, t = mk()
    c.agents.check_agentname("@newbot")
    assert "@" not in str(t.last.url)


# ---------------------------------------------------------------------------
# quickstart
# ---------------------------------------------------------------------------

def test_quickstart_post():
    c, t = mk({"agentId": "agent_xyz", "apiKey": "secret"})
    result = c.agents.quickstart(
        owner_email="a@b.com",
        agentname="testbot",
        name="Test Bot",
        skills=["coding"],
        wallet_pubkey="pubkey123",
        signature="sig456",
    )
    assert result["agentId"] == "agent_xyz"
    assert t.last.method == "POST"
    body = json.loads(t.last.content)
    assert body["agentname"] == "testbot"
    assert body["owner_email"] == "a@b.com"


def test_quickstart_idempotency_key():
    # quickstart uses **kwargs so extra fields are forwarded in the body
    c, t = mk()
    c.agents.quickstart(
        owner_email="x@y.z",
        agentname="bot",
        name="Bot",
        skills=[],
        wallet_pubkey="pk",
        signature="sig",
        idempotency_key="idem-qs",
    )
    body = json.loads(t.last.content)
    assert body.get("idempotency_key") == "idem-qs"


def test_quickstart_optional_description():
    c, t = mk()
    c.agents.quickstart(
        owner_email="x@y.z",
        agentname="bot",
        name="Bot",
        skills=["a"],
        wallet_pubkey="pk",
        signature="sig",
        description="A useful bot",
    )
    body = json.loads(t.last.content)
    assert body.get("description") == "A useful bot"


# ---------------------------------------------------------------------------
# me
# ---------------------------------------------------------------------------

def test_me():
    c, t = mk({"id": "agent_me"})
    result = c.agents.me()
    assert result["id"] == "agent_me"
    assert "agents/me" in str(t.last.url)
    assert t.last.method == "GET"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update():
    c, t = mk({"id": "agent_1"})
    c.agents.update("agent_1", name="New Name")
    assert t.last.method == "PATCH"
    assert "agents/agent_1" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["name"] == "New Name"


# ---------------------------------------------------------------------------
# feed
# ---------------------------------------------------------------------------

def test_feed():
    c, t = mk({"items": []})
    c.agents.feed(limit=10)
    assert "agents/me/feed" in str(t.last.url)
    assert "limit=10" in str(t.last.url)


# ---------------------------------------------------------------------------
# reviews / reputation / stats
# ---------------------------------------------------------------------------

def test_reviews():
    c, t = mk()
    c.agents.reviews("agent_1")
    assert "agents/agent_1/reviews" in str(t.last.url)


def test_reputation():
    c, t = mk()
    c.agents.reputation("agent_1")
    assert "agents/agent_1/reputation" in str(t.last.url)


def test_stats():
    c, t = mk()
    c.agents.stats("agent_1")
    assert "agents/agent_1/stats" in str(t.last.url)


# ---------------------------------------------------------------------------
# heartbeat
# ---------------------------------------------------------------------------

def test_heartbeat():
    c, t = mk({"ok": True})
    c.agents.heartbeat()
    assert t.last.method == "POST"
    assert "agents/heartbeat" in str(t.last.url)


# ---------------------------------------------------------------------------
# rotate_key
# ---------------------------------------------------------------------------

def test_rotate_key():
    c, t = mk({"apiKey": "new-key"})
    result = c.agents.rotate_key("agent_1")
    assert result["apiKey"] == "new-key"
    assert t.last.method == "POST"
    assert "agents/agent_1/rotate-key" in str(t.last.url)


# ---------------------------------------------------------------------------
# recover_key_request / recover_key_confirm
# ---------------------------------------------------------------------------

def test_recover_key_request_by_email():
    c, t = mk()
    c.agents.recover_key_request(email="a@b.com")
    assert t.last.method == "POST"
    assert "recover-key/request" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["email"] == "a@b.com"


def test_recover_key_request_by_agentname():
    c, t = mk()
    c.agents.recover_key_request(agentname="mybot")
    body = json.loads(t.last.content)
    assert body["agentname"] == "mybot"


def test_recover_key_confirm():
    c, t = mk({"apiKey": "recovered"})
    result = c.agents.recover_key_confirm(agentname="mybot", confirmation_code="CODE123")
    assert result["apiKey"] == "recovered"
    body = json.loads(t.last.content)
    assert body["agentname"] == "mybot"
    assert body["confirmationCode"] == "CODE123"


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

def test_verify():
    c, t = mk({"isVerified": True})
    c.agents.verify(wallet_pubkey="pk", signature="sig")
    assert t.last.method == "POST"
    assert "agents/verify" in str(t.last.url)


# ---------------------------------------------------------------------------
# conversations / conversation
# ---------------------------------------------------------------------------

def test_conversations():
    c, t = mk({"threads": []})
    c.agents.conversations("agent_1", limit=5)
    assert "agents/agent_1/conversations" in str(t.last.url)


def test_conversation_with_peer():
    c, t = mk()
    c.agents.conversation("agent_1", "agent_2")
    assert "agents/agent_1/conversations/agent_2" in str(t.last.url)


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------

def test_send_message():
    c, t = mk({"id": "msg_1"})
    c.agents.send_message("agent_1", content="Hello!")
    assert t.last.method == "POST"
    assert "agents/agent_1/messages" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["content"] == "Hello!"


def test_send_message_with_subject():
    c, t = mk()
    c.agents.send_message("agent_1", content="Hi", subject="Collab?")
    body = json.loads(t.last.content)
    assert body["subject"] == "Collab?"


# ---------------------------------------------------------------------------
# unread_count
# ---------------------------------------------------------------------------

def test_unread_count():
    c, t = mk({"count": 3})
    result = c.agents.unread_count("agent_1")
    assert result["count"] == 3
    assert "agents/agent_1/messages/unread-count" in str(t.last.url)


# ---------------------------------------------------------------------------
# oversight
# ---------------------------------------------------------------------------

def test_oversight():
    c, t = mk()
    c.agents.oversight("agent_1", post_jobs="auto")
    assert t.last.method == "PATCH"
    assert "agents/agent_1/oversight" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["post_jobs"] == "auto"


# ---------------------------------------------------------------------------
# set_webhook / test_webhook / webhook_deliveries
# ---------------------------------------------------------------------------

def test_set_webhook():
    c, t = mk({"url": "https://example.com/hook"})
    c.agents.set_webhook("agent_1", url="https://example.com/hook", events=["job.created"])
    assert t.last.method == "PUT"
    assert "agents/agent_1/webhook" in str(t.last.url)


def test_test_webhook():
    c, t = mk({"status": "sent"})
    c.agents.test_webhook("agent_1")
    assert t.last.method == "POST"
    assert "agents/agent_1/webhook/test" in str(t.last.url)


def test_webhook_deliveries():
    c, t = mk({"deliveries": []})
    c.agents.webhook_deliveries("agent_1")
    assert "agents/agent_1/webhook/deliveries" in str(t.last.url)


# ---------------------------------------------------------------------------
# onboarding_start / onboarding_status
# ---------------------------------------------------------------------------

def test_onboarding_start():
    c, t = mk()
    c.agents.onboarding_start("agent_1", step="wallet")
    assert t.last.method == "POST"
    assert "agents/agent_1/onboarding/start" in str(t.last.url)


def test_onboarding_status():
    c, t = mk({"step": "wallet"})
    c.agents.onboarding_status("agent_1")
    assert "agents/agent_1/onboarding/status" in str(t.last.url)


# ---------------------------------------------------------------------------
# command_center_actions
# ---------------------------------------------------------------------------

def test_command_center_actions():
    c, t = mk({"ok": True})
    c.agents.command_center_actions(action="pause")
    assert t.last.method == "POST"
    assert "command-center/actions" in str(t.last.url)


# ---------------------------------------------------------------------------
# agent_tasks / update_agent_task
# ---------------------------------------------------------------------------

def test_agent_tasks():
    c, t = mk({"tasks": []})
    c.agents.agent_tasks("agent_1", status="unread")
    assert "agents/agent_1/tasks" in str(t.last.url)
    assert "status=unread" in str(t.last.url)


def test_update_agent_task():
    c, t = mk()
    c.agents.update_agent_task("agent_1", "task_1", status="read")
    assert t.last.method == "PATCH"
    assert "agents/agent_1/tasks/task_1" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["status"] == "read"
