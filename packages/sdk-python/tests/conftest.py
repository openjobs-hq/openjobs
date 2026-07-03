"""Shared test fixtures and mock transport for the Python SDK unit tests."""
from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from openjobs import OpenJobsClient


class MockTransport(httpx.BaseTransport):
    """Captures requests and returns pre-programmed responses."""

    def __init__(
        self,
        responses: list[dict[str, Any]] | None = None,
        status_code: int = 200,
        body: Any = None,
    ) -> None:
        self.requests: list[httpx.Request] = []
        if responses is not None:
            self._responses = responses
        else:
            self._responses = [{"status_code": status_code, "body": body if body is not None else {}}]
        self._idx = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        r = self._responses[min(self._idx, len(self._responses) - 1)]
        self._idx += 1
        raw = r.get("body", {})
        if isinstance(raw, (dict, list)):
            content = json.dumps(raw).encode()
        elif isinstance(raw, bytes):
            content = raw
        else:
            content = str(raw).encode()
        return httpx.Response(
            status_code=r.get("status_code", 200),
            content=content,
            request=request,
        )

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]


@pytest.fixture
def transport() -> MockTransport:
    return MockTransport()


@pytest.fixture
def client(transport: MockTransport) -> OpenJobsClient:
    return OpenJobsClient(api_key="test-key", transport=transport, max_retries=0)


def make_client(
    *,
    body: Any = None,
    status_code: int = 200,
    responses: list[dict[str, Any]] | None = None,
    api_key: str = "test-key",
    env: str = "production",
    max_retries: int = 0,
    retry_base_seconds: float = 0,
    **kwargs: Any,
) -> tuple[OpenJobsClient, MockTransport]:
    t = MockTransport(responses=responses, status_code=status_code, body=body)
    c = OpenJobsClient(
        api_key=api_key,
        env=env,
        transport=t,
        max_retries=max_retries,
        retry_base_seconds=retry_base_seconds,
        **kwargs,
    )
    return c, t
