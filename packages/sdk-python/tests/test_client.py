import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openjobs import OpenJobsApiError, OpenJobsClient


def json_response(payload, status_code=200):
    return httpx.Response(status_code, json=payload)


def test_auth_headers_and_idempotency_key_are_forwarded():
    seen = []

    def handler(request):
        seen.append(request)
        return json_response({"ok": True})

    transport = httpx.MockTransport(handler)

    with OpenJobsClient(
        api_key="test-api-key",
        base_url="https://api.example.test",
        max_retries=0,
        transport=transport,
    ) as client:
        result = client.request(
            "POST",
            "/api/jobs",
            json_body={"title": "Fixture job"},
            params={"status": "open", "omitted": None},
            idempotency_key="idem-123",
        )

    assert result == {"ok": True}
    assert len(seen) == 1
    request = seen[0]
    assert str(request.url) == "https://api.example.test/api/jobs?status=open"
    assert request.method == "POST"
    assert request.headers["user-agent"] == "openjobs-sdk-python/3.0.3"
    assert request.headers["accept"] == "application/json"
    assert request.headers["x-api-key"] == "test-api-key"
    assert request.headers["idempotency-key"] == "idem-123"
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"title": "Fixture job"}


def test_sandbox_env_uses_sandbox_host_and_header():
    seen = []

    def handler(request):
        seen.append(request)
        return json_response({"healthy": True})

    transport = httpx.MockTransport(handler)

    with OpenJobsClient(env="sandbox", max_retries=0, transport=transport) as client:
        result = client.sandbox.status()

    assert result == {"healthy": True}
    assert len(seen) == 1
    request = seen[0]
    assert str(request.url) == "https://sandbox.openjobs.bot/api/sandbox/status"
    assert request.headers["x-openjobs-env"] == "sandbox"
    assert "x-api-key" not in request.headers


def test_api_error_exposes_status_and_body():
    def handler(request):
        return json_response({"error": "invalid payload"}, status_code=422)

    transport = httpx.MockTransport(handler)

    with OpenJobsClient(max_retries=0, transport=transport) as client:
        with pytest.raises(OpenJobsApiError) as exc_info:
            client.jobs.apply("job_123", cover_letter="")

    assert str(exc_info.value) == "invalid payload"
    assert exc_info.value.status == 422
    assert exc_info.value.body == {"error": "invalid payload"}


def test_retries_retriable_http_statuses(monkeypatch):
    attempts = []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            return json_response({"error": "try again"}, status_code=503)
        return json_response({"jobs": []})

    monkeypatch.setattr("openjobs.client.time.sleep", lambda seconds: None)
    transport = httpx.MockTransport(handler)

    with OpenJobsClient(max_retries=1, retry_base_seconds=0, transport=transport) as client:
        result = client.jobs.list(status="open")

    assert result == {"jobs": []}
    assert len(attempts) == 2
    assert str(attempts[0].url) == "https://openjobs.bot/api/jobs?status=open"
    assert str(attempts[1].url) == "https://openjobs.bot/api/jobs?status=open"


def test_network_errors_are_retried(monkeypatch):
    attempts = []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            raise httpx.ConnectError("temporary failure", request=request)
        return json_response({"ok": True})

    monkeypatch.setattr("openjobs.client.time.sleep", lambda seconds: None)
    transport = httpx.MockTransport(handler)

    with OpenJobsClient(max_retries=1, retry_base_seconds=0, transport=transport) as client:
        result = client.agents.me()

    assert result == {"ok": True}
    assert len(attempts) == 2
