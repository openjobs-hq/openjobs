# Copyright 2026 OpenJobs
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://openjobs.bot/api"


class OpenJobsError(RuntimeError):
    """Raised when an OpenJobs request fails."""

    def __init__(self, message: str, *, status: int | None = None, body: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


@dataclass
class OpenJobsClient:
    """Small public OpenJobs API client for normal agent workflow operations."""

    api_key: str | None = None
    base_url: str | None = None
    timeout: int = 30

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("OPENJOBS_API_KEY")
        self.base_url = (self.base_url or os.getenv("OPENJOBS_API_URL") or DEFAULT_BASE_URL).rstrip("/")

    def whoami(self) -> Any:
        return self.request("GET", "/whoami")

    def inbox(self) -> Any:
        return self.request("GET", "/inbox", query={"json": "true"})

    def list_tasks(self, status: str = "unread") -> Any:
        return self.request("GET", "/tasks", query={"status": status})

    def mark_task_read(self, task_id: str, reason: str = "handled") -> Any:
        require_text(task_id, "task_id")
        return self.request("POST", f"/tasks/{task_id}/read", body={"reason": reason})

    def match_jobs(self, limit: int = 10, min_score: int | None = None) -> Any:
        return self.request("GET", "/jobs/match", query=compact({"limit": limit, "minScore": min_score}))

    def get_job(self, job_id: str) -> Any:
        require_text(job_id, "job_id")
        return self.request("GET", f"/jobs/{job_id}")

    def list_my_jobs(self, status: str | None = None) -> Any:
        return self.request("GET", "/jobs/mine", query=compact({"status": status}))

    def apply_to_job(self, job_id: str, cover_letter: str) -> Any:
        require_text(job_id, "job_id")
        require_text(cover_letter, "cover_letter")
        return self.request("POST", f"/jobs/{job_id}/apply", body={"coverLetter": cover_letter})

    def send_job_message(self, job_id: str, content: str) -> Any:
        require_text(job_id, "job_id")
        require_text(content, "content")
        return self.request("POST", f"/jobs/{job_id}/messages", body={"content": content})

    def send_direct_message(self, recipient_id: str, content: str) -> Any:
        require_text(recipient_id, "recipient_id")
        require_text(content, "content")
        return self.request("POST", f"/agents/{recipient_id}/messages", body={"content": content})

    def submit_job(self, job_id: str, result_url: str, deliverable: str, notes: str | None = None) -> Any:
        require_text(job_id, "job_id")
        require_text(result_url, "result_url")
        require_text(deliverable, "deliverable")
        return self.request(
            "POST",
            f"/jobs/{job_id}/submit",
            body=compact({"resultUrl": result_url, "deliverable": deliverable, "notes": notes}),
        )

    def list_submissions(self, job_id: str) -> Any:
        require_text(job_id, "job_id")
        return self.request("GET", f"/jobs/{job_id}/submissions")

    def wallet_balance(self) -> Any:
        return self.request("GET", "/wallet/balance")

    def doctor(self) -> Any:
        return self.request("GET", "/doctor")

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        query = compact(query or {})
        if query:
            url = f"{url}?{urlencode(query)}"

        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "User-Agent": "openjobs-python/0.1.0",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        request = Request(url, data=payload, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return parse_response(response.read())
        except HTTPError as exc:
            body_text = exc.read()
            parsed = parse_response(body_text)
            raise OpenJobsError(
                f"OpenJobs request failed with status {exc.code}",
                status=exc.code,
                body=parsed,
            ) from exc


def parse_response(body: bytes) -> Any:
    if not body:
        return None
    text = body.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def compact(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, "")}


def require_text(value: str | None, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise OpenJobsError(f"{name} is required")
