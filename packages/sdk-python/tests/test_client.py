"""Unit tests for OpenJobsClient core: constructor, request(), retry, errors, headers."""
from __future__ import annotations

import pytest

from openjobs import OpenJobsApiError
from .conftest import make_client


# ---------------------------------------------------------------------------
# Constructor defaults
# ---------------------------------------------------------------------------

def test_defaults_base_url():
    c, _ = make_client()
    assert c.base_url == "https://openjobs.bot"


def test_sandbox_base_url():
    c, _ = make_client(env="sandbox")
    assert c.base_url == "https://sandbox.openjobs.bot"


def test_explicit_base_url():
    c, _ = make_client(base_url="http://localhost:3000")
    assert c.base_url == "http://localhost:3000"


def test_api_key_stored():
    c, _ = make_client(api_key="my-key")
    assert c.api_key == "my-key"


def test_max_retries_default():
    from openjobs.client import OpenJobsClient as C
    import httpx

    class NullTransport(httpx.BaseTransport):
        def handle_request(self, req):
            return httpx.Response(200, content=b"{}", request=req)

    c = C(transport=NullTransport())
    assert c.max_retries == 4


def test_context_manager():
    c, _ = make_client()
    with c:
        pass


# ---------------------------------------------------------------------------
# Auth header
# ---------------------------------------------------------------------------

def test_api_key_header_sent(client, transport):
    client.request("GET", "/api/status")
    assert transport.last.headers.get("x-api-key") == "test-key"


def test_no_api_key_header_when_anonymous():
    c, t = make_client(api_key=None)
    c.request("GET", "/api/status")
    assert "x-api-key" not in t.last.headers


def test_sandbox_env_header():
    c, t = make_client(env="sandbox")
    c.request("GET", "/api/status")
    assert t.last.headers.get("x-openjobs-env") == "sandbox"


def test_production_no_env_header(client, transport):
    client.request("GET", "/api/status")
    assert "x-openjobs-env" not in transport.last.headers


def test_idempotency_key_header(client, transport):
    client.request("POST", "/api/agents/register", json_body={}, idempotency_key="idem-123")
    assert transport.last.headers.get("idempotency-key") == "idem-123"


# ---------------------------------------------------------------------------
# Path canonicalisation  /api/x  →  /api/v1/x
# ---------------------------------------------------------------------------

def test_canonical_path(client, transport):
    client.request("GET", "/api/jobs")
    assert "/api/v1/jobs" in str(transport.last.url)


def test_v1_path_unchanged(client, transport):
    client.request("GET", "/api/v1/jobs")
    assert "/api/v1/jobs" in str(transport.last.url)


# ---------------------------------------------------------------------------
# Surface guard
# ---------------------------------------------------------------------------

def test_unknown_path_raises(client):
    with pytest.raises(Exception, match="public API surface"):
        client.request("GET", "/api/admin/secret")


def test_unknown_method_raises(client):
    with pytest.raises(ValueError):
        client.request("PUT", "/api/jobs")


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_4xx_raises_api_error():
    c, _ = make_client(status_code=404, body={"error": "not found"})
    with pytest.raises(OpenJobsApiError) as exc_info:
        c.request("GET", "/api/jobs/missing")
    assert exc_info.value.status == 404
    assert "not found" in str(exc_info.value)


def test_api_error_has_body():
    c, _ = make_client(status_code=422, body={"error": "validation", "field": "title"})
    with pytest.raises(OpenJobsApiError) as exc_info:
        c.request("GET", "/api/jobs/x")
    assert exc_info.value.body["field"] == "title"


def test_non_retriable_5xx_raises():
    c, _ = make_client(status_code=501, body={"error": "not implemented"}, max_retries=0)
    with pytest.raises(OpenJobsApiError) as exc_info:
        c.request("GET", "/api/status")
    assert exc_info.value.status == 501


# ---------------------------------------------------------------------------
# Retry behaviour
# ---------------------------------------------------------------------------

def test_retry_on_503_then_success():
    c, t = make_client(
        responses=[
            {"status_code": 503, "body": {"error": "overloaded"}},
            {"status_code": 200, "body": {"ok": True}},
        ],
        max_retries=1,
        retry_base_seconds=0,
    )
    result = c.request("GET", "/api/status")
    assert result == {"ok": True}
    assert len(t.requests) == 2


def test_retry_exhausted_raises():
    c, t = make_client(
        responses=[
            {"status_code": 500, "body": {"error": "boom"}},
            {"status_code": 500, "body": {"error": "boom"}},
        ],
        max_retries=1,
        retry_base_seconds=0,
    )
    with pytest.raises(OpenJobsApiError) as exc_info:
        c.request("GET", "/api/status")
    assert exc_info.value.status == 500
    assert len(t.requests) == 2


def test_no_retry_on_400():
    c, t = make_client(
        responses=[
            {"status_code": 400, "body": {"error": "bad request"}},
            {"status_code": 200, "body": {}},
        ],
        max_retries=1,
        retry_base_seconds=0,
    )
    with pytest.raises(OpenJobsApiError):
        c.request("GET", "/api/status")
    assert len(t.requests) == 1


def test_retry_on_429():
    c, t = make_client(
        responses=[
            {"status_code": 429, "body": {"error": "rate limited"}},
            {"status_code": 200, "body": {"ok": True}},
        ],
        max_retries=1,
        retry_base_seconds=0,
    )
    result = c.request("GET", "/api/status")
    assert result["ok"] is True


def test_retry_on_408():
    c, t = make_client(
        responses=[
            {"status_code": 408, "body": {"error": "timeout"}},
            {"status_code": 200, "body": {}},
        ],
        max_retries=1,
        retry_base_seconds=0,
    )
    c.request("GET", "/api/status")
    assert len(t.requests) == 2


# ---------------------------------------------------------------------------
# Query parameters
# ---------------------------------------------------------------------------

def test_query_params_added(client, transport):
    client.request("GET", "/api/jobs", params={"status": "open", "limit": 10})
    url_str = str(transport.last.url)
    assert "status=open" in url_str
    assert "limit=10" in url_str


def test_none_query_params_dropped(client, transport):
    client.request("GET", "/api/jobs", params={"status": None, "limit": 10})
    url_str = str(transport.last.url)
    assert "status" not in url_str
    assert "limit=10" in url_str


# ---------------------------------------------------------------------------
# upload_attachment
# ---------------------------------------------------------------------------

def test_upload_attachment_file_not_found(client):
    with pytest.raises(FileNotFoundError):
        client.upload_attachment("job", "job_123", "/no/such/file.pdf")


def test_upload_attachment_success(tmp_path):
    f = tmp_path / "test.txt"
    f.write_bytes(b"hello")
    c, t = make_client(body={"id": "att_1", "status": "pending"})
    result = c.upload_attachment("submission", "draft:sub:123", str(f))
    assert result["id"] == "att_1"
    assert t.requests[-1].method == "POST"
    assert "/api/v1/attachments/submission/" in str(t.requests[-1].url)


def test_upload_attachment_error(tmp_path):
    f = tmp_path / "bad.txt"
    f.write_bytes(b"data")
    c, _ = make_client(status_code=422, body={"error": "too large"})
    with pytest.raises(OpenJobsApiError) as exc_info:
        c.upload_attachment("job", "job_1", str(f))
    assert exc_info.value.status == 422
