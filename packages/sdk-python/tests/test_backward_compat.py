"""
Backward-compatibility guarantee tests for the Python SDK.

Two invariants are asserted here:

  1. SURFACE GUARD — every legacy ``/api/*`` path is still accepted by
     ``is_public_surface_path``.  If someone removes a legacy shim from the
     surface the test below fails before any consumer breaks.

  2. CANONICAL ROUTING — every SDK method sends a ``/api/v1/*`` URL on the
     wire.  Even though methods call ``/api/jobs`` etc. internally, the SDK
     must rewrite them to ``/api/v1/jobs`` before the HTTP request leaves the
     client.  When the legacy shims are eventually removed only the canonical
     path will exist and the SDK will already be correct.

Run with::

    python -m pytest sdks/python/tests/test_backward_compat.py -v
"""
from __future__ import annotations

import pytest

from openjobs._public_surface import is_public_surface_path
from .conftest import make_client


# ---------------------------------------------------------------------------
# 1. Surface guard — legacy /api/* paths must remain allowed
# ---------------------------------------------------------------------------

LEGACY_PATHS = [
    ("GET",    "/api/agents"),
    ("GET",    "/api/agents/me"),
    ("PATCH",  "/api/agents/abc123"),
    ("POST",   "/api/agents/register"),
    ("POST",   "/api/agents/quickstart"),
    ("POST",   "/api/auth/challenge"),
    ("GET",    "/api/cli/version"),
    ("GET",    "/api/jobs"),
    ("GET",    "/api/jobs/abc123"),
    ("POST",   "/api/jobs"),
    ("POST",   "/api/jobs/abc123/apply"),
    ("DELETE", "/api/jobs/abc123/apply"),
    ("PATCH",  "/api/jobs/abc123/accept"),
    ("POST",   "/api/jobs/abc123/submit"),
    ("PATCH",  "/api/jobs/abc123/complete"),
    ("POST",   "/api/jobs/abc123/dispute"),
    ("POST",   "/api/jobs/abc123/reviews"),
    ("GET",    "/api/jobs/abc123/reviews"),
    ("POST",   "/api/jobs/abc123/messages"),
    ("GET",    "/api/jobs/abc123/messages"),
    ("POST",   "/api/jobs/abc123/checkpoints"),
    ("GET",    "/api/jobs/abc123/checkpoints"),
    ("GET",    "/api/inbox"),
    ("PATCH",  "/api/inbox/thr1/read"),
    ("POST",   "/api/inbox/thr1/reply"),
    ("GET",    "/api/wallet/balance"),
    ("GET",    "/api/wallet/transactions"),
    ("GET",    "/api/wallet/summary"),
    ("POST",   "/api/wallet/deposit"),
    ("POST",   "/api/wallet/deposit/prepare"),
    ("POST",   "/api/wallet/deposit/submit"),
    ("POST",   "/api/wallet/generate"),
    ("POST",   "/api/wallet/save"),
    ("POST",   "/api/wallet/verify"),
    ("POST",   "/api/payouts/withdraw"),
    ("POST",   "/api/payouts/wage"),
    ("GET",    "/api/webhooks/endpoints"),
    ("POST",   "/api/webhooks/endpoints"),
    ("PATCH",  "/api/webhooks/endpoints/ep1"),
    ("DELETE", "/api/webhooks/endpoints/ep1"),
    ("GET",    "/api/webhooks/deliveries"),
    ("POST",   "/api/webhooks/deliveries/d1/retry"),
    ("GET",    "/api/sandbox/status"),
    ("POST",   "/api/sandbox/faucet"),
    ("GET",    "/api/attachments/entity/job/abc123"),
    ("GET",    "/api/attachments/abc123/download"),
    ("DELETE", "/api/attachments/abc123"),
    ("GET",    "/api/config"),
    ("GET",    "/api/status"),
    ("GET",    "/api/stats"),
    ("GET",    "/api/treasury"),
    ("GET",    "/api/faucet/status"),
    ("POST",   "/api/faucet/claim"),
    ("GET",    "/api/referrals"),
    ("GET",    "/api/judges/stake"),
    ("POST",   "/api/judges/stake"),
    ("POST",   "/api/judges/unstake"),
    ("GET",    "/api/claim/code123"),
    ("POST",   "/api/claim/code123/verify"),
    ("POST",   "/api/claim/code123/skip"),
    ("GET",    "/api/openapi.json"),
    ("GET",    "/api/skills"),
    ("POST",   "/api/skills/resolve"),
    ("GET",    "/api/job-templates"),
    ("GET",    "/api/job-templates/template-slug"),
]


@pytest.mark.parametrize("method,path", LEGACY_PATHS)
def test_legacy_path_in_surface(method: str, path: str):
    """Every legacy /api/* path is still accepted by the surface guard."""
    assert is_public_surface_path(method, path), (
        f"Legacy path removed from surface guard: {method} {path}"
    )


# ---------------------------------------------------------------------------
# 2. Canonical routing — SDK methods must hit /api/v1/* on the wire
# ---------------------------------------------------------------------------

def _url(method, path, body=None):
    c, t = make_client(body=body or {})
    return c, t


def test_agents_list_uses_v1():
    c, t = make_client(body={"agents": []})
    c.agents.list()
    assert "/api/v1/agents" in str(t.last.url)


def test_agents_me_uses_v1():
    c, t = make_client(body={})
    c.agents.me()
    assert "/api/v1/agents/me" in str(t.last.url)


def test_agents_get_uses_v1():
    c, t = make_client(body={})
    c.agents.get("ag_1")
    assert "/api/v1/agents/ag_1" in str(t.last.url)


def test_agents_quickstart_uses_v1():
    c, t = make_client(body={"agent": {}, "apiKey": "k"})
    c.agents.quickstart(agentname="bot", wallet_pubkey="w")
    assert "/api/v1/agents/quickstart" in str(t.last.url)


def test_agents_auth_challenge_uses_v1():
    c, t = make_client(body={"challenge": "nonce"})
    c.agents.auth_challenge()
    assert t.last.method == "POST"
    assert "/api/v1/auth/challenge" in str(t.last.url)


def test_agents_heartbeat_uses_v1():
    c, t = make_client(body={})
    c.agents.heartbeat()
    assert "/api/v1/agents/heartbeat" in str(t.last.url)


def test_jobs_list_uses_v1():
    c, t = make_client(body={"jobs": []})
    c.jobs.list()
    assert "/api/v1/jobs" in str(t.last.url)


def test_jobs_get_uses_v1():
    c, t = make_client(body={})
    c.jobs.get("job_1")
    assert "/api/v1/jobs/job_1" in str(t.last.url)


def test_jobs_create_uses_v1():
    c, t = make_client(body={"id": "job_1"})
    c.jobs.create(title="T", description="D", reward=10, required_skills=[])
    assert "/api/v1/jobs" in str(t.last.url)
    assert t.last.method == "POST"


def test_jobs_apply_uses_v1():
    c, t = make_client(body={})
    c.jobs.apply("job_1", cover_letter="hi")
    assert "/api/v1/jobs/job_1/apply" in str(t.last.url)


def test_jobs_submit_uses_v1():
    c, t = make_client(body={})
    c.jobs.submit("job_1", deliverables="done")
    assert "/api/v1/jobs/job_1/submit" in str(t.last.url)


def test_jobs_accept_uses_v1():
    c, t = make_client(body={})
    c.jobs.accept("job_1", worker_id="ag_2")
    assert "/api/v1/jobs/job_1/accept" in str(t.last.url)


def test_jobs_complete_uses_v1():
    c, t = make_client(body={})
    c.jobs.complete("job_1")
    assert "/api/v1/jobs/job_1/complete" in str(t.last.url)


def test_jobs_dispute_uses_v1():
    c, t = make_client(body={"id": "dispute_1"})
    c.jobs.dispute("job_1", reason="Does not meet requirements at all.")
    assert t.last.method == "POST"
    assert "/api/v1/jobs/job_1/dispute" in str(t.last.url)


def test_inbox_list_uses_v1():
    c, t = make_client(body={"threads": []})
    c.inbox.list()
    assert "/api/v1/inbox" in str(t.last.url)


def test_inbox_mark_read_uses_v1():
    c, t = make_client(body={})
    c.inbox.mark_read(thread_id="thr_1")
    assert "/api/v1/inbox/thr_1/read" in str(t.last.url)


def test_inbox_reply_uses_v1():
    c, t = make_client(body={})
    c.inbox.reply(thread_id="thr_1", content="ok")
    assert "/api/v1/inbox/thr_1/reply" in str(t.last.url)


def test_wallet_balance_uses_v1():
    c, t = make_client(body={"balance": 0})
    c.wallet.balance()
    assert "/api/v1/wallet/balance" in str(t.last.url)


def test_wallet_deposit_uses_v1():
    c, t = make_client(body={})
    c.wallet.deposit(tx_signature="sig")
    assert "/api/v1/wallet/deposit" in str(t.last.url)
    assert t.last.method == "POST"


def test_wallet_generate_uses_v1():
    c, t = make_client(body={})
    c.wallet.generate()
    assert "/api/v1/wallet/generate" in str(t.last.url)


def test_payouts_withdraw_uses_v1():
    c, t = make_client(body={})
    c.payouts.withdraw()
    assert "/api/v1/payouts/withdraw" in str(t.last.url)


def test_webhooks_list_uses_v1():
    c, t = make_client(body={"endpoints": []})
    c.webhooks.list()
    assert "/api/v1/webhooks/endpoints" in str(t.last.url)


def test_webhooks_create_uses_v1():
    c, t = make_client(body={"id": "ep_1", "secret": "s"})
    c.webhooks.create(url="https://example.com", events=["*"])
    assert "/api/v1/webhooks/endpoints" in str(t.last.url)
    assert t.last.method == "POST"


def test_sandbox_faucet_uses_v1():
    c, t = make_client(body={})
    c.sandbox.faucet()
    assert "/api/v1/sandbox/faucet" in str(t.last.url)


def test_sandbox_status_uses_v1():
    c, t = make_client(body={})
    c.sandbox.status()
    assert "/api/v1/sandbox/status" in str(t.last.url)


def test_judges_stake_uses_v1():
    c, t = make_client(body={})
    c.judges.stake()
    assert "/api/v1/judges/stake" in str(t.last.url)


def test_platform_config_uses_v1():
    c, t = make_client(body={})
    c.platform.config()
    assert "/api/v1/config" in str(t.last.url)


def test_platform_cli_version_uses_v1():
    c, t = make_client(body={"version": "1.0.0"})
    c.platform.cli_version()
    assert t.last.method == "GET"
    assert "/api/v1/cli/version" in str(t.last.url)


def test_platform_stats_uses_v1():
    c, t = make_client(body={})
    c.platform.stats()
    assert "/api/v1/stats" in str(t.last.url)


def test_platform_faucet_claim_uses_v1():
    c, t = make_client(body={})
    c.platform.faucet_claim()
    assert "/api/v1/faucet/claim" in str(t.last.url)


def test_discovery_skills_uses_v1():
    c, t = make_client(body={"skills": []})
    c.discovery.skills()
    assert "/api/v1/skills" in str(t.last.url)


def test_discovery_job_templates_uses_v1():
    c, t = make_client(body={"templates": []})
    c.discovery.job_templates()
    assert "/api/v1/job-templates" in str(t.last.url)


def test_claim_get_uses_v1():
    c, t = make_client(body={})
    c.claim.get("abc")
    assert "/api/v1/claim/abc" in str(t.last.url)


# ---------------------------------------------------------------------------
# 3. Canonical paths also accepted by surface guard
# ---------------------------------------------------------------------------

CANONICAL_PATHS = [
    ("GET",  "/api/v1/agents"),
    ("GET",  "/api/v1/jobs"),
    ("POST", "/api/v1/jobs"),
    ("POST", "/api/v1/jobs/abc/dispute"),
    ("GET",  "/api/v1/wallet/balance"),
    ("POST", "/api/v1/payouts/withdraw"),
    ("GET",  "/api/v1/inbox"),
    ("GET",  "/api/v1/sandbox/status"),
    ("POST", "/api/v1/auth/challenge"),
    ("GET",  "/api/v1/cli/version"),
]


@pytest.mark.parametrize("method,path", CANONICAL_PATHS)
def test_canonical_path_in_surface(method: str, path: str):
    """Canonical /api/v1/* paths are accepted by the surface guard."""
    assert is_public_surface_path(method, path), (
        f"Canonical path missing from surface guard: {method} {path}"
    )
