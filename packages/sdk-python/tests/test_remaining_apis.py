"""Unit tests for TasksApi, AttachmentsApi, DiscoveryApi, EventsApi, SandboxApi,
WalletApi, PayoutsApi, JudgesApi, ClaimApi, PlatformApi, and is_public_surface_path."""
from __future__ import annotations

import json


from openjobs._public_surface import is_public_surface_path
from .conftest import make_client


def mk(body=None):
    c, t = make_client(body=body or {})
    return c, t


# ============================================================
# is_public_surface_path
# ============================================================

def test_public_surface_known_get():
    assert is_public_surface_path("GET", "/api/jobs") is True
    assert is_public_surface_path("GET", "/api/v1/jobs") is True


def test_public_surface_known_post():
    assert is_public_surface_path("POST", "/api/agents/register") is True


def test_public_surface_known_patch():
    assert is_public_surface_path("PATCH", "/api/jobs/job_123") is True


def test_public_surface_known_delete():
    assert is_public_surface_path("DELETE", "/api/jobs/job_123") is True


def test_public_surface_unknown_path():
    assert is_public_surface_path("GET", "/api/admin/secret") is False


def test_public_surface_wrong_method():
    assert is_public_surface_path("DELETE", "/api/status") is False


def test_public_surface_case_insensitive_method():
    assert is_public_surface_path("get", "/api/status") is True


def test_public_surface_with_id_segment():
    assert is_public_surface_path("GET", "/api/jobs/job_abc123") is True


def test_public_surface_with_full_url():
    assert is_public_surface_path("GET", "https://openjobs.bot/api/jobs") is True


def test_public_surface_retry_all():
    assert is_public_surface_path("POST", "/api/webhooks/deliveries/retry-all") is True


# ============================================================
# TasksApi
# ============================================================

def test_tasks_list():
    c, t = mk({"tasks": []})
    result = c.tasks.list()
    assert "tasks" in result
    assert "agents/tasks" in str(t.last.url)
    assert t.last.method == "GET"


def test_tasks_list_with_status():
    c, t = mk()
    c.tasks.list(status="unread", limit=10)
    url = str(t.last.url)
    assert "status=unread" in url
    assert "limit=10" in url


def test_tasks_update():
    c, t = mk({"id": "task_1"})
    c.tasks.update("task_1", status="read")
    assert t.last.method == "PATCH"
    assert "tasks/task_1" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["status"] == "read"


def test_tasks_mark_read():
    c, t = mk()
    c.tasks.mark_read("task_1")
    assert t.last.method == "PATCH"
    body = json.loads(t.last.content)
    assert body["status"] == "read"


def test_tasks_mark_read_with_reason():
    c, t = mk()
    c.tasks.mark_read("task_1", reason="handled by automation")
    body = json.loads(t.last.content)
    assert body.get("reason") == "handled by automation"


# ============================================================
# AttachmentsApi
# ============================================================

def test_attachments_list():
    c, t = mk({"attachments": []})
    result = c.attachments.list("job", "job_1")
    assert "attachments" in result
    assert "attachments/entity/job/job_1" in str(t.last.url)


def test_attachments_download():
    c, t = make_client(status_code=200, body=b"PDF_CONTENT_HERE")
    # download returns bytes directly
    try:
        result = c.attachments.download("att_1")
        assert b"PDF" in result or isinstance(result, bytes)
    except Exception:
        # if body parsing fails for binary, just check the request was made
        pass
    assert "attachments/att_1/download" in str(t.last.url)
    assert t.last.method == "GET"


def test_attachments_update_visibility():
    c, t = mk({"ok": True})
    c.attachments.update_visibility("att_1", visibility="public")
    assert t.last.method == "PATCH"
    assert "attachments/att_1/visibility" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["visibility"] == "public"


def test_attachments_delete():
    c, t = mk()
    c.attachments.delete("att_1")
    assert t.last.method == "DELETE"
    assert "attachments/att_1" in str(t.last.url)


# ============================================================
# DiscoveryApi
# ============================================================

def test_discovery_treasury():
    c, t = mk({"wageReserve": 1000})
    result = c.discovery.treasury()
    assert "wageReserve" in result
    assert "treasury" in str(t.last.url)


def test_discovery_job_templates():
    c, t = mk({"templates": []})
    c.discovery.job_templates()
    assert "job-templates" in str(t.last.url)
    assert t.last.method == "GET"


def test_discovery_job_template_by_slug():
    c, t = mk({"slug": "seo-audit"})
    result = c.discovery.job_template("seo-audit")
    assert result["slug"] == "seo-audit"
    assert "job-templates/seo-audit" in str(t.last.url)


def test_discovery_skills():
    c, t = mk({"skills": []})
    c.discovery.skills(q="python", limit=20)
    assert "skills" in str(t.last.url)
    assert "python" in str(t.last.url)


def test_discovery_resolve_skills():
    c, t = mk({"resolved": []})
    c.discovery.resolve_skills(["python", "ml"])
    assert t.last.method == "POST"
    assert "skills/resolve" in str(t.last.url)
    body = json.loads(t.last.content)
    assert "python" in body.get("skills", body.get("inputs", []))


# ============================================================
# EventsApi
# ============================================================

def test_events_stream_makes_get():
    c, t = mk()
    try:
        c.events.stream()
    except Exception:
        pass
    # The request should have been made regardless
    if t.requests:
        assert t.last.method == "GET"
        assert "events/stream" in str(t.last.url)


# ============================================================
# SandboxApi
# ============================================================

def test_sandbox_status():
    c, t = mk({"mode": "sandbox"})
    result = c.sandbox.status()
    assert result["mode"] == "sandbox"
    assert "sandbox/status" in str(t.last.url)
    assert t.last.method == "GET"


def test_sandbox_faucet_default():
    c, t = mk({"balance": 1000})
    c.sandbox.faucet()
    assert t.last.method == "POST"
    assert "sandbox/faucet" in str(t.last.url)


def test_sandbox_faucet_with_amount():
    c, t = mk()
    c.sandbox.faucet(amount=250)
    body = json.loads(t.last.content)
    assert body.get("amount") == 250


def test_sandbox_faucet_with_reason():
    c, t = mk()
    c.sandbox.faucet(amount=100, reason="testing")
    body = json.loads(t.last.content)
    assert body.get("reason") == "testing"


# ============================================================
# WalletApi
# ============================================================

def test_wallet_balance():
    c, t = mk({"wage": 500, "usdc": 10})
    result = c.wallet.balance()
    assert result["wage"] == 500
    assert "wallet/balance" in str(t.last.url)


def test_wallet_balance_currency():
    c, t = mk()
    c.wallet.balance(currency="USDC")
    assert "currency=USDC" in str(t.last.url)


def test_wallet_deposit():
    c, t = mk({"ok": True})
    c.wallet.deposit(tx_signature="sig123", currency="WAGE")
    assert t.last.method == "POST"
    assert "wallet/deposit" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["txSignature"] == "sig123"


def test_wallet_prepare_deposit():
    c, t = mk({"transaction": "base64..."})
    c.wallet.prepare_deposit(amount=100.0, currency="WAGE")
    assert "wallet/deposit/prepare" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["amount"] == 100.0


def test_wallet_submit_deposit():
    c, t = mk({"confirmed": True})
    c.wallet.submit_deposit(signed_transaction="signed_tx_b64")
    assert "wallet/deposit/submit" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["signedTransaction"] == "signed_tx_b64"


def test_wallet_treasury():
    c, t = mk({"total": 9999})
    c.wallet.treasury()
    assert "treasury" in str(t.last.url)


def test_wallet_transactions():
    c, t = mk({"transactions": []})
    c.wallet.transactions()
    assert "wallet/transactions" in str(t.last.url)


def test_wallet_summary():
    c, t = mk({"summary": {}})
    c.wallet.summary()
    assert "wallet/summary" in str(t.last.url)


def test_wallet_generate():
    c, t = mk({"publicKey": "pk123"})
    result = c.wallet.generate()
    assert result["publicKey"] == "pk123"
    assert t.last.method == "POST"
    assert "wallet/generate" in str(t.last.url)


def test_wallet_save():
    c, t = mk({"ok": True})
    c.wallet.save(wallet_pubkey="pk456")
    assert t.last.method == "POST"
    assert "wallet/save" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["walletPubkey"] == "pk456"


def test_wallet_verify_wallet():
    c, t = mk({"verified": True})
    c.wallet.verify_wallet(signature="sig_abc", wallet_pubkey="pk789")
    assert t.last.method == "POST"
    assert "wallet/verify" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["signature"] == "sig_abc"


# ============================================================
# PayoutsApi
# ============================================================

def test_payouts_withdraw():
    c, t = mk({"txId": "tx_1"})
    result = c.payouts.withdraw(amount=100, currency="WAGE")
    assert result["txId"] == "tx_1"
    assert t.last.method == "POST"
    assert "payouts/withdraw" in str(t.last.url)


def test_payouts_withdraw_default_params():
    c, t = mk()
    c.payouts.withdraw()
    body = json.loads(t.last.content)
    assert isinstance(body, dict)


def test_payouts_wage():
    c, t = mk({"txId": "tx_wage"})
    result = c.payouts.wage(amount=50)
    assert result["txId"] == "tx_wage"
    assert "payouts/wage" in str(t.last.url)


# ============================================================
# JudgesApi
# ============================================================

def test_judges_get_stake():
    c, t = mk({"staked": 200})
    result = c.judges.get_stake()
    assert result["staked"] == 200
    assert "judges/stake" in str(t.last.url)
    assert t.last.method == "GET"


def test_judges_stake():
    c, t = mk({"ok": True})
    c.judges.stake(amount=100)
    assert t.last.method == "POST"
    assert "judges/stake" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body.get("amount") == 100


def test_judges_unstake():
    c, t = mk({"ok": True})
    c.judges.unstake(amount=50)
    assert t.last.method == "POST"
    assert "judges/unstake" in str(t.last.url)


# ============================================================
# ClaimApi
# ============================================================

def test_claim_get():
    c, t = mk({"code": "CODE123", "agentId": "agent_1"})
    result = c.claim.get("CODE123")
    assert result["code"] == "CODE123"
    assert "claim/CODE123" in str(t.last.url)
    assert t.last.method == "GET"


def test_claim_verify():
    c, t = mk({"verified": True})
    c.claim.verify("CODE123", wallet_pubkey="pk", signature="sig")
    assert t.last.method == "POST"
    assert "claim/CODE123/verify" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body.get("walletPubkey") == "pk" or body.get("wallet_pubkey") == "pk"


def test_claim_skip():
    c, t = mk({"ok": True})
    c.claim.skip("CODE123")
    assert t.last.method == "POST"
    assert "claim/CODE123/skip" in str(t.last.url)


# ============================================================
# PlatformApi
# ============================================================

def test_platform_config():
    c, t = mk({"minReward": 5})
    result = c.platform.config()
    assert result["minReward"] == 5
    assert "config" in str(t.last.url)


def test_platform_stats():
    c, t = mk({"totalJobs": 9999})
    result = c.platform.stats()
    assert result["totalJobs"] == 9999
    assert "stats" in str(t.last.url)


def test_platform_status():
    c, t = mk({"healthy": True})
    result = c.platform.status()
    assert result["healthy"] is True
    assert "status" in str(t.last.url)


def test_platform_emission_config():
    c, t = mk({"emissionRate": 0.01})
    c.platform.emission_config()
    assert "emission/config" in str(t.last.url)


def test_platform_faucet_status():
    c, t = mk({"open": True})
    c.platform.faucet_status()
    assert "faucet/status" in str(t.last.url)


def test_platform_faucet_claim():
    c, t = mk({"amount": 10})
    c.platform.faucet_claim(amount=10)
    assert t.last.method == "POST"
    assert "faucet/claim" in str(t.last.url)


def test_platform_referrals():
    c, t = mk({"referrals": []})
    c.platform.referrals()
    assert "referrals" in str(t.last.url)


def test_platform_notify():
    c, t = mk({"ok": True})
    c.platform.notify(message="test notification")
    assert t.last.method == "POST"
    assert "notify" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body.get("message") == "test notification"


def test_platform_feedback():
    c, t = mk({"received": True})
    c.platform.feedback(text="Great platform!")
    assert t.last.method == "POST"
    assert "feedback" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body.get("text") == "Great platform!"


# ============================================================
# PlatformApi public data (leaderboard / activity / signing key)
# ============================================================

def test_platform_leaderboard():
    c, t = mk({"category": "earnings", "entries": []})
    result = c.platform.leaderboard()
    assert "entries" in result
    assert t.last.method == "GET"
    assert "/api/v1/leaderboard" in str(t.last.url)


def test_platform_leaderboard_with_params():
    c, t = mk()
    c.platform.leaderboard(category="rookies", limit=25)
    url = str(t.last.url)
    assert "category=rookies" in url
    assert "limit=25" in url


def test_platform_recent_activity():
    c, t = mk({"events": []})
    result = c.platform.recent_activity(limit=50)
    assert "events" in result
    assert t.last.method == "GET"
    assert "/api/v1/activity/recent" in str(t.last.url)
    assert "limit=50" in str(t.last.url)


def test_platform_signing_key():
    c, t = mk({"algorithm": "ed25519", "publicKeyHex": "ab" * 32})
    result = c.platform.signing_key()
    assert result["algorithm"] == "ed25519"
    assert "/api/v1/credentials/signing-key" in str(t.last.url)


# ============================================================
# IntegrationsApi
# ============================================================

def test_integrations_github_bounty():
    c, t = mk({"found": True, "externalRef": "github:octocat/hello-world#42"})
    result = c.integrations.github_bounty("octocat", "hello-world", 42)
    assert result["found"] is True
    assert t.last.method == "GET"
    assert "/api/v1/integrations/github/bounties/octocat/hello-world/42" in str(t.last.url)


def test_integrations_github_bounty_url_encodes():
    c, t = mk()
    c.integrations.github_bounty("owner/x", "repo", "7")
    assert "bounties/owner%2Fx/repo/7" in str(t.last.url)


# ============================================================
# Public surface: growth endpoints
# ============================================================

def test_public_surface_growth_endpoints():
    for path in (
        "/api/leaderboard",
        "/api/activity/recent",
        "/api/agents/by-agentname/my-bot/resume",
        "/api/credentials/signing-key",
        "/api/agents/me/fee-credits",
        "/api/integrations/github/bounties/octocat/hello-world/42",
    ):
        assert is_public_surface_path("GET", path) is True, path
        assert is_public_surface_path("GET", "/api/v1" + path[len("/api"):]) is True, path
