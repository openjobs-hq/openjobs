import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { loadConfig } from "../src/config.js";
import { OpenJobsMcpServer } from "../src/server.js";
import { createToolDefinitions, type ToolDefinition } from "../src/tools.js";

// Isolated config per call so tests never touch a real ~/.openjobs/config.json.
function config(overrides: Record<string, string | undefined> = {}) {
  return loadConfig({
    OPENJOBS_MCP_CONFIG_PATH: join(mkdtempSync(join(tmpdir(), "openjobs-mcp-cov-")), "config.json"),
    ...overrides,
  });
}

// Records every SDK method the tools invoke, returning canned payloads.
function fakeClient(calls: Array<{ method: string; args: unknown[] }>, apiKey?: string) {
  const record = (method: string, result: unknown) => (...args: unknown[]) => {
    calls.push({ method, args });
    return Promise.resolve(result);
  };
  return {
    agents: {
      me: record("agents.me", { id: "agent_1", name: "Test Agent", apiKey }),
      quickstart: record("agents.quickstart", { agentId: "agent_1", apiKey: "oj_live_secret_123456789" }),
    },
    platform: { status: record("platform.status", { ok: true }) },
    inbox: { list: record("inbox.list", { threads: [] }) },
    tasks: { list: record("tasks.list", { tasks: [] }), markRead: record("tasks.markRead", { ok: true }) },
    jobs: {
      list: record("jobs.list", { jobs: [{ id: "job_1", title: "Test Job" }] }),
      search: record("jobs.search", { jobs: [] }),
      match: record("jobs.match", { jobs: [] }),
      get: record("jobs.get", { id: "job_1" }),
      mine: record("jobs.mine", { jobs: [] }),
      submissions: record("jobs.submissions", { submissions: [] }),
      apply: record("jobs.apply", { applicationId: "app_1" }),
      message: record("jobs.message", { messageId: "msg_1" }),
      submit: record("jobs.submit", { submissionId: "sub_1" }),
    },
    wallet: { balance: record("wallet.balance", { balances: [] }) },
  };
}

function tool(tools: ToolDefinition[], name: string): ToolDefinition {
  const found = tools.find((t) => t.name === name);
  if (!found) {
    throw new Error(`expected tool ${name} to be registered`);
  }
  return found;
}

// (1) Tool listing/registration exposes the expected OpenJobs tools when authenticated.
test("authenticated tool registration exposes the expected OpenJobs tool surface", () => {
  const names = createToolDefinitions({ config: config({ OPENJOBS_API_KEY: "oj_live_123" }) }).map((t) => t.name);
  for (const expected of ["openjobs_setup_status", "openjobs_whoami", "openjobs_list_jobs", "openjobs_get_job", "openjobs_apply_to_job", "openjobs_submit_job", "openjobs_get_leaderboard", "openjobs_get_recent_activity", "openjobs_get_agent_resume", "openjobs_get_my_fee_credits", "openjobs_lookup_github_bounty"]) {
    assert(names.includes(expected), `missing tool ${expected}`);
  }
});

// (2) A basic read-only tool call succeeds and returns the documented envelope shape.
test("read-only public tool call returns the ok envelope shape", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const tools = createToolDefinitions({ config: config(), clientFactory: (o) => fakeClient(calls, o.apiKey) as never });
  const result = await tool(tools, "openjobs_list_jobs").handler({ limit: 5 });
  assert.equal(result.ok, true);
  assert.ok(result.ok && Array.isArray((result.data as { jobs: unknown[] }).jobs));
  assert.ok(Array.isArray(result.warnings));
  assert.ok(Array.isArray(result.nextActions));
  assert.equal(calls[0].method, "jobs.list");
});

// (3) Argument validation rejects a missing required field without touching the client.
test("missing required argument fails cleanly and never calls the SDK", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const tools = createToolDefinitions({ config: config({ OPENJOBS_API_KEY: "oj_live_123" }), clientFactory: (o) => fakeClient(calls, o.apiKey) as never });
  const result = await tool(tools, "openjobs_get_job").handler({});
  assert.equal(result.ok, false);
  assert.ok(!result.ok && result.error.code === "OPENJOBS_TOOL_ERROR");
  assert.match(JSON.stringify(result), /jobId is required/);
  assert.equal(calls.length, 0);
});

// (4) Argument validation rejects malformed input types (wrong scalar type).
test("malformed argument type is rejected before the write reaches the SDK", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const tools = createToolDefinitions({ config: config({ OPENJOBS_API_KEY: "oj_live_123" }), clientFactory: (o) => fakeClient(calls, o.apiKey) as never });
  const result = await tool(tools, "openjobs_apply_to_job").handler({ jobId: "job_1", coverLetter: "I can do this.", estimatedHours: "soon" });
  assert.equal(result.ok, false);
  assert.match(JSON.stringify(result), /estimatedHours must be a number/);
  assert.equal(calls.find((c) => c.method === "jobs.apply"), undefined);
});

// (5) Upstream SDK errors surface cleanly AND long secret-like tokens are redacted from the message.
test("upstream error is surfaced cleanly with secrets redacted", async () => {
  const failingClient = {
    agents: { me: () => Promise.reject(new Error("boom leaked oj_live_secret_abcdefghijklmnopqrstuvwxyz")) },
  };
  const tools = createToolDefinitions({ config: config({ OPENJOBS_API_KEY: "oj_live_123" }), clientFactory: () => failingClient as never });
  const result = await tool(tools, "openjobs_whoami").handler({});
  assert.equal(result.ok, false);
  assert.ok(!result.ok && result.error.code === "OPENJOBS_TOOL_ERROR");
  assert.doesNotMatch(JSON.stringify(result), /oj_live_secret_abcdefghijklmnopqrstuvwxyz/);
  assert.match(JSON.stringify(result), /\[redacted\]/);
});

// (6) A representative authenticated tool call succeeds and forwards to the right SDK method.
test("authenticated whoami succeeds and forwards to agents.me", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const tools = createToolDefinitions({ config: config({ OPENJOBS_API_KEY: "oj_live_123" }), clientFactory: (o) => fakeClient(calls, o.apiKey) as never });
  const result = await tool(tools, "openjobs_whoami").handler({});
  assert.equal(result.ok, true);
  assert.ok(result.ok && (result.data as { name: string }).name === "Test Agent");
  assert.equal(calls[0].method, "agents.me");
});

// (7) With no credentials, auth-only and mutating tools are gated out cleanly (no crash).
test("unauthenticated context gates out auth-only and write tools", () => {
  const names = createToolDefinitions({ config: config() }).map((t) => t.name);
  assert(names.includes("openjobs_list_jobs"));
  assert(!names.includes("openjobs_whoami"));
  assert(!names.includes("openjobs_apply_to_job"));
  assert(!names.includes("openjobs_submit_job"));
});

// (8) Tool results normalize to a stable, JSON-serializable envelope with nested secrets redacted.
test("tool result serialization is stable and redacts nested secrets via JSON-RPC", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const server = new OpenJobsMcpServer({
    config: config({ OPENJOBS_API_KEY: "oj_live_secret_123456789" }),
    clientFactory: (o) => fakeClient(calls, o.apiKey) as never,
  });
  const called = await server.handle({ jsonrpc: "2.0", id: 7, method: "tools/call", params: { name: "openjobs_whoami", arguments: {} } });
  const serialized = JSON.stringify(called);
  assert.equal(called?.jsonrpc, "2.0");
  assert.equal(called?.id, 7);
  // agents.me echoes the apiKey back; redactDeep must strip the raw secret from the response.
  assert.doesNotMatch(serialized, /oj_live_secret_123456789/);
  assert.match(serialized, /Test Agent/);
});
