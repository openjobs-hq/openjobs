import assert from "node:assert/strict";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { loadConfig } from "../src/config.js";
import { OpenJobsMcpServer } from "../src/server.js";
import { createToolDefinitions } from "../src/tools.js";

function config(overrides: Record<string, string | undefined> = {}) {
  return loadConfig({
    OPENJOBS_MCP_CONFIG_PATH: join(mkdtempSync(join(tmpdir(), "openjobs-mcp-test-")), "config.json"),
    ...overrides,
  });
}

function fakeClient(calls: Array<{ method: string; args: unknown[] }>, apiKey?: string) {
  const record = (method: string, result: unknown) => (...args: unknown[]) => {
    calls.push({ method, args });
    return Promise.resolve(result);
  };
  return {
    agents: {
      me: record("agents.me", { id: "agent_1", name: "Test Agent", apiKey }),
      quickstart: record("agents.quickstart", { agentId: "agent_1", agentname: "test", name: "Test Agent", apiKey: "oj_live_secret_123456789", claimUrl: "https://openjobs.bot/claim/x", verificationCode: "abc", ownerEmail: "owner@example.com" }),
      resume: record("agents.resume", { schema: "openjobs.agent-resume/v1", verification: { algorithm: "ed25519" } }),
      feeCredits: record("agents.feeCredits", { currency: "WAGE", balance: 0, credits: [] }),
    },
    platform: {
      status: record("platform.status", { ok: true }),
      leaderboard: record("platform.leaderboard", { category: "earnings", entries: [] }),
      recentActivity: record("platform.recentActivity", { events: [] }),
    },
    integrations: { githubBounty: record("integrations.githubBounty", { found: true, job: { id: "job_1" } }) },
    inbox: { list: record("inbox.list", { threads: [] }) },
    tasks: { list: record("tasks.list", { tasks: [] }), markRead: record("tasks.markRead", { ok: true }) },
    jobs: {
      list: record("jobs.list", { jobs: [] }),
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

test("unauthenticated server exposes setup and public discovery tools only", () => {
  const tools = createToolDefinitions({ config: config() }).map((tool) => tool.name);
  assert(tools.includes("openjobs_setup_status"));
  assert(tools.includes("openjobs_register_agent"));
  assert(tools.includes("openjobs_list_jobs"));
  assert(tools.includes("openjobs_get_leaderboard"));
  assert(tools.includes("openjobs_get_recent_activity"));
  assert(tools.includes("openjobs_get_agent_resume"));
  assert(tools.includes("openjobs_lookup_github_bounty"));
  assert(!tools.includes("openjobs_get_my_fee_credits"));
  assert(!tools.includes("openjobs_whoami"));
  assert(!tools.includes("openjobs_apply_to_job"));
});

test("public data tools dispatch to the SDK without credentials", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const tools = createToolDefinitions({ config: config(), clientFactory: (options) => fakeClient(calls, options.apiKey) as never });
  const call = async (name: string, args: Record<string, unknown>) => {
    const tool = tools.find((item) => item.name === name)!;
    const result = await tool.handler(args);
    assert.equal(result.ok, true, `${name} should succeed`);
  };
  await call("openjobs_get_leaderboard", { category: "earnings", limit: 10 });
  await call("openjobs_get_recent_activity", { limit: 5 });
  await call("openjobs_get_agent_resume", { agentname: "test-bot" });
  await call("openjobs_lookup_github_bounty", { owner: "octocat", repo: "hello-world", issueNumber: 42 });
  assert.deepEqual(calls.map((c) => c.method), [
    "platform.leaderboard",
    "platform.recentActivity",
    "agents.resume",
    "integrations.githubBounty",
  ]);
  assert.deepEqual(calls[3].args, ["octocat", "hello-world", 42]);
});

test("fee credits tool requires an API key and forwards to agents.feeCredits", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const tools = createToolDefinitions({
    config: config({ OPENJOBS_API_KEY: "oj_live_123" }),
    clientFactory: (options) => fakeClient(calls, options.apiKey) as never,
  });
  const credits = tools.find((tool) => tool.name === "openjobs_get_my_fee_credits")!;
  const result = await credits.handler({ currency: "WAGE" });
  assert.equal(result.ok, true);
  assert.equal(calls[0].method, "agents.feeCredits");
  assert.deepEqual(calls[0].args, [{ currency: "WAGE" }]);
});

test("read-only authenticated mode hides mutating worker tools", () => {
  const tools = createToolDefinitions({ config: config({ OPENJOBS_API_KEY: "oj_live_123", OPENJOBS_MCP_READ_ONLY: "true" }) }).map((tool) => tool.name);
  assert(tools.includes("openjobs_whoami"));
  assert(tools.includes("openjobs_match_jobs"));
  assert(!tools.includes("openjobs_apply_to_job"));
});

test("confirmation mode blocks writes until confirm true", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const tools = createToolDefinitions({
    config: config({ OPENJOBS_API_KEY: "oj_live_123", OPENJOBS_MCP_REQUIRE_CONFIRMATION: "true" }),
    clientFactory: (options) => fakeClient(calls, options.apiKey) as never,
  });
  const apply = tools.find((tool) => tool.name === "openjobs_apply_to_job")!;
  const blocked = await apply.handler({ jobId: "job_1", coverLetter: "I can do this." });
  assert.equal(blocked.ok, false);
  assert.equal(calls.length, 0);
  const allowed = await apply.handler({ jobId: "job_1", coverLetter: "I can do this.", confirm: true });
  assert.equal(allowed.ok, true);
  assert.equal(calls[0].method, "jobs.apply");
});

test("register agent redacts API key and persists only when requested", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const cfg = config({ OPENJOBS_MCP_REQUIRE_CONFIRMATION: "true" });
  const tools = createToolDefinitions({ config: cfg, clientFactory: (options) => fakeClient(calls, options.apiKey) as never });
  const register = tools.find((tool) => tool.name === "openjobs_register_agent")!;
  const result = await register.handler({
    ownerEmail: "owner@example.com",
    agentname: "test_agent",
    name: "Test Agent",
    skills: ["research"],
    walletPubkey: "Wallet111111111111111111111111111111111",
    signature: "signature111111111111111111111111111111111",
    persist: true,
    confirm: true,
  });
  assert.equal(result.ok, true);
  assert.match(JSON.stringify(result), /oj_l…6789/);
  assert.doesNotMatch(JSON.stringify(result), /oj_live_secret_123456789/);
  const stored = JSON.parse(readFileSync(cfg.configPath, "utf8"));
  assert.equal(stored.apiKey, "oj_live_secret_123456789");
  assert.equal(calls[0].method, "agents.quickstart");
  assert.equal(calls[1].method, "agents.me");
});

test("JSON-RPC tools/list and tools/call work", async () => {
  const calls: Array<{ method: string; args: unknown[] }> = [];
  const server = new OpenJobsMcpServer({
    config: config({ OPENJOBS_API_KEY: "oj_live_123" }),
    clientFactory: (options) => fakeClient(calls, options.apiKey) as never,
  });
  const listed = await server.handle({ jsonrpc: "2.0", id: 1, method: "tools/list" });
  assert.deepEqual(listed?.jsonrpc, "2.0");
  assert(JSON.stringify(listed).includes("openjobs_whoami"));
  const called = await server.handle({ jsonrpc: "2.0", id: 2, method: "tools/call", params: { name: "openjobs_whoami", arguments: {} } });
  assert(JSON.stringify(called).includes("Test Agent"));
  assert.equal(calls[0].method, "agents.me");
});
