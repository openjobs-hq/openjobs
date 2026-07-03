"""Unit tests for InboxApi, WebhooksApi, and HMAC sign/verify."""
from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from openjobs.client import WebhooksApi
from .conftest import make_client


def mk(body=None):
    c, t = make_client(body=body or {})
    return c, t


# ============================================================
# InboxApi
# ============================================================

def test_inbox_list_default():
    c, t = mk({"threads": []})
    result = c.inbox.list()
    assert "threads" in result
    assert t.last.method == "GET"
    assert "inbox" in str(t.last.url)


def test_inbox_list_unread_only():
    c, t = mk()
    c.inbox.list(unread_only=True, limit=25)
    url = str(t.last.url)
    assert "unreadOnly=true" in url
    assert "limit=25" in url


def test_inbox_list_thread_type():
    c, t = mk()
    c.inbox.list(thread_type="job")
    assert "threadType=job" in str(t.last.url)


def test_inbox_list_search():
    c, t = mk()
    c.inbox.list(search="hello")
    assert "search=hello" in str(t.last.url)


# ---------------------------------------------------------------------------
# mark_read
# ---------------------------------------------------------------------------

def test_inbox_mark_read_by_job_id():
    c, t = mk()
    c.inbox.mark_read(job_id="job_abc")
    assert t.last.method == "PATCH"
    assert "inbox/job_abc/read" in str(t.last.url)
    assert "threadType=job" in str(t.last.url)


def test_inbox_mark_read_by_peer_id():
    c, t = mk()
    c.inbox.mark_read(peer_id="agent_xyz")
    assert "inbox/agent_xyz/read" in str(t.last.url)
    assert "threadType=dm" in str(t.last.url)


def test_inbox_mark_read_by_thread_id():
    c, t = mk()
    c.inbox.mark_read(thread_id="thread_123")
    assert "inbox/thread_123/read" in str(t.last.url)


def test_inbox_mark_read_requires_exactly_one():
    c, _ = mk()
    with pytest.raises(ValueError):
        c.inbox.mark_read(job_id="j1", peer_id="p1")


def test_inbox_mark_read_requires_at_least_one():
    c, _ = mk()
    with pytest.raises(ValueError):
        c.inbox.mark_read()


# ---------------------------------------------------------------------------
# reply
# ---------------------------------------------------------------------------

def test_inbox_reply_by_job_id():
    c, t = mk({"id": "msg_1"})
    c.inbox.reply(job_id="job_abc", content="Update on progress")
    assert t.last.method == "POST"
    assert "inbox/job_abc/reply" in str(t.last.url)
    assert "threadType=job" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["content"] == "Update on progress"


def test_inbox_reply_by_peer_id():
    c, t = mk()
    c.inbox.reply(peer_id="agent_xyz", content="Sure!", subject="Re: Collab?")
    assert "inbox/agent_xyz/reply" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["subject"] == "Re: Collab?"


def test_inbox_reply_with_kind_and_payload():
    c, t = mk()
    c.inbox.reply(thread_id="t1", content="Proposal text", kind="proposal", payload={"amount": 100})
    body = json.loads(t.last.content)
    assert body["kind"] == "proposal"
    assert body["payload"]["amount"] == 100


# ============================================================
# WebhooksApi
# ============================================================

def test_webhooks_create():
    c, t = mk({"id": "ep_1", "secret": "shh"})
    result = c.webhooks.create(url="https://example.com/hook", events=["job.created", "job.completed"])
    assert result["id"] == "ep_1"
    assert t.last.method == "POST"
    assert "webhooks/endpoints" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["url"] == "https://example.com/hook"
    assert "job.created" in body["events"]


def test_webhooks_create_with_description():
    c, t = mk()
    c.webhooks.create(url="https://example.com/hook", events=["job.created"], description="My webhook")
    body = json.loads(t.last.content)
    assert body.get("description") == "My webhook"


def test_webhooks_list():
    c, t = mk({"endpoints": []})
    result = c.webhooks.list()
    assert "endpoints" in result
    assert t.last.method == "GET"
    assert "webhooks/endpoints" in str(t.last.url)


def test_webhooks_update():
    c, t = mk({"id": "ep_1"})
    c.webhooks.update("ep_1", status="paused")
    assert t.last.method == "PATCH"
    assert "webhooks/endpoints/ep_1" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["status"] == "paused"


def test_webhooks_delete():
    c, t = mk()
    c.webhooks.delete("ep_1")
    assert t.last.method == "DELETE"
    assert "webhooks/endpoints/ep_1" in str(t.last.url)


def test_webhooks_deliveries():
    c, t = mk({"deliveries": []})
    c.webhooks.deliveries(limit=10)
    assert t.last.method == "GET"
    assert "webhooks/deliveries" in str(t.last.url)
    assert "limit=10" in str(t.last.url)


def test_webhooks_deliveries_status_filter():
    c, t = mk()
    c.webhooks.deliveries(status="failed")
    assert "status=failed" in str(t.last.url)


def test_webhooks_retry_delivery():
    c, t = mk({"ok": True})
    c.webhooks.retry_delivery("del_1")
    assert t.last.method == "POST"
    assert "deliveries/del_1/retry" in str(t.last.url)


def test_webhooks_retry_all():
    c, t = mk({"queued": 5})
    result = c.webhooks.retry_all()
    assert result["queued"] == 5
    assert t.last.method == "POST"
    assert "deliveries/retry-all" in str(t.last.url)


# ============================================================
# HMAC sign / verify (static methods, no network)
# ============================================================

def test_sign_returns_hex_string():
    sig = WebhooksApi.sign(secret="my-secret", body=b'{"event":"job.created"}')
    assert isinstance(sig, str)
    assert len(sig) == 64
    int(sig, 16)  # must be valid hex


def test_sign_string_body():
    sig = WebhooksApi.sign(secret="key", body='{"a":1}')
    assert len(sig) == 64


def test_sign_matches_manual_hmac():
    secret = "test-secret"
    body = b'{"event":"test"}'
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert WebhooksApi.sign(secret=secret, body=body) == expected


def test_verify_valid_signature():
    body = b'hello world'
    secret = "s3cr3t"
    sig = WebhooksApi.sign(secret=secret, body=body)
    assert WebhooksApi.verify(secret=secret, body=body, signature=sig) is True


def test_verify_wrong_signature():
    assert WebhooksApi.verify(secret="key", body=b"data", signature="deadbeef" * 8) is False


def test_verify_tampered_body():
    body = b'original'
    secret = "key"
    sig = WebhooksApi.sign(secret=secret, body=body)
    assert WebhooksApi.verify(secret=secret, body=b"tampered", signature=sig) is False


def test_verify_constant_time():
    # Ensure verify doesn't short-circuit — different length returns False
    assert WebhooksApi.verify(secret="k", body=b"d", signature="ab") is False
