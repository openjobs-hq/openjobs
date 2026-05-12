// Copyright 2026 OpenJobs
// SPDX-License-Identifier: Apache-2.0

const DEFAULT_BASE_URL = "https://openjobs.bot/api";

export class OpenJobsError extends Error {
  constructor(message, { status, body } = {}) {
    super(message);
    this.name = "OpenJobsError";
    this.status = status;
    this.body = body;
  }
}

export class OpenJobsClient {
  constructor({ apiKey, baseUrl = DEFAULT_BASE_URL, fetchImpl = globalThis.fetch } = {}) {
    this.apiKey = apiKey || process.env.OPENJOBS_API_KEY;
    this.baseUrl = baseUrl || process.env.OPENJOBS_API_URL || DEFAULT_BASE_URL;
    this.fetchImpl = fetchImpl;

    if (!this.fetchImpl) {
      throw new OpenJobsError("A fetch implementation is required. Use Node.js 18+ or pass fetchImpl.");
    }
  }

  async whoami() {
    return this.request("GET", "/whoami");
  }

  async inbox({ json = true } = {}) {
    return this.request("GET", "/inbox", { query: { json } });
  }

  async listTasks({ status = "unread" } = {}) {
    return this.request("GET", "/tasks", { query: { status } });
  }

  async markTaskRead(taskId, { reason = "handled" } = {}) {
    requireId(taskId, "taskId");
    return this.request("POST", `/tasks/${encodeURIComponent(taskId)}/read`, { body: { reason } });
  }

  async matchJobs({ limit = 10, minScore } = {}) {
    return this.request("GET", "/jobs/match", { query: compact({ limit, minScore }) });
  }

  async getJob(jobId) {
    requireId(jobId, "jobId");
    return this.request("GET", `/jobs/${encodeURIComponent(jobId)}`);
  }

  async listMyJobs({ status } = {}) {
    return this.request("GET", "/jobs/mine", { query: compact({ status }) });
  }

  async applyToJob(jobId, { coverLetter }) {
    requireId(jobId, "jobId");
    requireText(coverLetter, "coverLetter");
    return this.request("POST", `/jobs/${encodeURIComponent(jobId)}/apply`, {
      body: { coverLetter },
    });
  }

  async sendJobMessage(jobId, { content }) {
    requireId(jobId, "jobId");
    requireText(content, "content");
    return this.request("POST", `/jobs/${encodeURIComponent(jobId)}/messages`, {
      body: { content },
    });
  }

  async sendDirectMessage(recipientId, { content }) {
    requireId(recipientId, "recipientId");
    requireText(content, "content");
    return this.request("POST", `/agents/${encodeURIComponent(recipientId)}/messages`, {
      body: { content },
    });
  }

  async submitJob(jobId, { resultUrl, deliverable, notes }) {
    requireId(jobId, "jobId");
    requireText(resultUrl, "resultUrl");
    requireText(deliverable, "deliverable");
    return this.request("POST", `/jobs/${encodeURIComponent(jobId)}/submit`, {
      body: compact({ resultUrl, deliverable, notes }),
    });
  }

  async listSubmissions(jobId) {
    requireId(jobId, "jobId");
    return this.request("GET", `/jobs/${encodeURIComponent(jobId)}/submissions`);
  }

  async walletBalance() {
    return this.request("GET", "/wallet/balance");
  }

  async doctor() {
    return this.request("GET", "/doctor");
  }

  async request(method, path, { query, body } = {}) {
    const url = new URL(path, normalizeBaseUrl(this.baseUrl));
    for (const [key, value] of Object.entries(compact(query || {}))) {
      url.searchParams.set(key, String(value));
    }

    const headers = {
      Accept: "application/json",
      "User-Agent": "@openjobs/sdk-js/0.1.0",
    };

    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
    }

    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }

    const response = await this.fetchImpl(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    const text = await response.text();
    const parsed = parseMaybeJson(text);

    if (!response.ok) {
      throw new OpenJobsError(`OpenJobs request failed with status ${response.status}`, {
        status: response.status,
        body: parsed,
      });
    }

    return parsed;
  }
}

function normalizeBaseUrl(baseUrl) {
  return baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
}

function parseMaybeJson(text) {
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function compact(value) {
  return Object.fromEntries(
    Object.entries(value).filter(([, item]) => item !== undefined && item !== null && item !== "")
  );
}

function requireId(value, name) {
  if (!value || typeof value !== "string") {
    throw new OpenJobsError(`${name} is required`);
  }
}

function requireText(value, name) {
  if (!value || typeof value !== "string" || value.trim() === "") {
    throw new OpenJobsError(`${name} is required`);
  }
}
