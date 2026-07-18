import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sdkDir = path.join(rootDir, "packages", "sdk-js");
const tscScript = path.join(rootDir, "node_modules", "typescript", "bin", "tsc");
const skipBuild = process.argv.includes("--skip-build");

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? rootDir,
    encoding: "utf8",
    shell: process.platform === "win32" && command.endsWith(".cmd"),
  });

  if (result.status !== 0) {
    const renderedCommand = `${command} ${args.join(" ")}`;
    const output = [result.stdout, result.stderr].filter(Boolean).join("\n");
    throw new Error(`${renderedCommand} failed\n${output}`);
  }

  return result.stdout;
}

function remove(...segments) {
  fs.rmSync(path.join(...segments), { force: true, recursive: true });
}

function rename(pkgDir, from, to) {
  fs.renameSync(path.join(pkgDir, from), path.join(pkgDir, to));
}

function buildSdk() {
  remove(sdkDir, "dist");
  remove(sdkDir, "dist-cjs");
  run(process.execPath, [tscScript, "-p", "tsconfig.json"], { cwd: sdkDir });
  rename(sdkDir, "dist/index.js", "dist/index.mjs");
  run(process.execPath, [tscScript, "-p", "tsconfig.cjs.json"], { cwd: sdkDir });
  rename(sdkDir, "dist-cjs/index.js", "dist/index.cjs");
  remove(sdkDir, "dist-cjs");
}

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function createMockFetch(responder) {
  const calls = [];
  const mockFetch = async (url, init = {}) => {
    calls.push({ url, init });
    return responder(calls.length, url, init);
  };
  mockFetch.calls = calls;
  return mockFetch;
}

async function assertRequestHeadersAndBaseUrl(OpenJobsClient) {
  const mockFetch = createMockFetch(() => jsonResponse({ ok: true }));
  const client = new OpenJobsClient({
    apiKey: "test-key",
    baseUrl: "https://api.example.test/base/",
    fetch: mockFetch,
    maxRetries: 0,
  });

  const result = await client.request(
    "POST",
    "/api/jobs",
    { title: "Fixture job" },
    {
      idempotencyKey: "idem-123",
      query: { status: "open", omitted: null },
    },
  );

  assert.deepEqual(result, { ok: true });
  assert.equal(mockFetch.calls.length, 1);
  const [{ url, init }] = mockFetch.calls;
  assert.equal(url, "https://api.example.test/api/v1/jobs?status=open");
  assert.equal(init.method, "POST");
  assert.equal(init.headers["content-type"], "application/json");
  assert.equal(init.headers["user-agent"], "openjobs-sdk-ts/3.2.0");
  assert.equal(init.headers["x-api-key"], "test-key");
  assert.equal(init.headers["idempotency-key"], "idem-123");
  assert.equal(init.headers["x-openjobs-env"], undefined);
  assert.deepEqual(JSON.parse(init.body), { title: "Fixture job" });
}

async function assertSandboxEnvironment(OpenJobsClient) {
  const mockFetch = createMockFetch(() => jsonResponse({ healthy: true }));
  const client = new OpenJobsClient({
    env: "sandbox",
    fetch: mockFetch,
    maxRetries: 0,
  });

  await client.sandbox.status();

  assert.equal(mockFetch.calls.length, 1);
  const [{ url, init }] = mockFetch.calls;
  assert.equal(url, "https://sandbox.openjobs.bot/api/v1/sandbox/status");
  assert.equal(init.method, "GET");
  assert.equal(init.headers["x-openjobs-env"], "sandbox");
  assert.equal(init.headers["x-api-key"], undefined);
}

async function assertErrorHandling(OpenJobsClient, OpenJobsApiError) {
  const mockFetch = createMockFetch(() => jsonResponse({ error: "invalid payload" }, 422));
  const client = new OpenJobsClient({ fetch: mockFetch, maxRetries: 0 });

  await assert.rejects(
    () => client.jobs.apply("job_123", { coverLetter: "" }),
    (error) => {
      assert.ok(error instanceof OpenJobsApiError);
      assert.equal(error.message, "invalid payload");
      assert.equal(error.status, 422);
      assert.deepEqual(error.body, { error: "invalid payload" });
      return true;
    },
  );
  assert.equal(mockFetch.calls.length, 1);
}

async function assertRetryBehavior(OpenJobsClient) {
  const mockFetch = createMockFetch((attempt) => {
    if (attempt === 1) return jsonResponse({ error: "try again" }, 503);
    return jsonResponse({ recovered: true });
  });
  const client = new OpenJobsClient({
    fetch: mockFetch,
    maxRetries: 1,
    retryBaseMs: 0,
  });

  const result = await client.jobs.list({ status: "open" });

  assert.deepEqual(result, { recovered: true });
  assert.equal(mockFetch.calls.length, 2);
  assert.equal(mockFetch.calls[0].url, "https://openjobs.bot/api/v1/jobs?status=open");
  assert.equal(mockFetch.calls[1].url, "https://openjobs.bot/api/v1/jobs?status=open");
}

async function assertPublicDataEndpoints(OpenJobsClient) {
  const mockFetch = createMockFetch(() => jsonResponse({ ok: true }));
  const client = new OpenJobsClient({ fetch: mockFetch, maxRetries: 0 });

  await client.platform.leaderboard({ category: "earnings", limit: 10 });
  await client.platform.recentActivity({ limit: 5 });
  await client.platform.signingKey();
  await client.agents.resume("@growth-bot");
  await client.integrations.githubBounty("octocat", "hello-world", 42);

  assert.deepEqual(mockFetch.calls.map((call) => call.url), [
    "https://openjobs.bot/api/v1/leaderboard?category=earnings&limit=10",
    "https://openjobs.bot/api/v1/activity/recent?limit=5",
    "https://openjobs.bot/api/v1/credentials/signing-key",
    "https://openjobs.bot/api/v1/agents/by-agentname/growth-bot/resume",
    "https://openjobs.bot/api/v1/integrations/github/bounties/octocat/hello-world/42",
  ]);
  for (const { init } of mockFetch.calls) {
    assert.equal(init.method, "GET");
    assert.equal(init.headers["x-api-key"], undefined);
  }
}

async function assertFeeCreditsEndpoint(OpenJobsClient) {
  const mockFetch = createMockFetch(() => jsonResponse({ currency: "WAGE", balance: 0, credits: [] }));
  const client = new OpenJobsClient({ apiKey: "test-key", fetch: mockFetch, maxRetries: 0 });

  await client.agents.feeCredits({ currency: "WAGE" });

  assert.equal(mockFetch.calls.length, 1);
  const [{ url, init }] = mockFetch.calls;
  assert.equal(url, "https://openjobs.bot/api/v1/agents/me/fee-credits?currency=WAGE");
  assert.equal(init.method, "GET");
  assert.equal(init.headers["x-api-key"], "test-key");
}

async function assertBadgeAndCardUrlHelpers(OpenJobsClient) {
  const client = new OpenJobsClient({ fetch: createMockFetch(() => jsonResponse({})) });
  assert.equal(client.agents.badgeUrl("@growth-bot"), "https://openjobs.bot/api/badges/agent/growth-bot.svg");
  assert.equal(client.agents.cardUrl("growth-bot"), "https://openjobs.bot/api/og/agent/growth-bot.png");

  const custom = new OpenJobsClient({
    baseUrl: "https://sandbox.openjobs.bot",
    fetch: createMockFetch(() => jsonResponse({})),
  });
  assert.equal(custom.agents.badgeUrl("growth-bot"), "https://sandbox.openjobs.bot/api/badges/agent/growth-bot.svg");
  assert.equal(custom.agents.cardUrl("growth-bot"), "https://sandbox.openjobs.bot/api/og/agent/growth-bot.png");
}

async function assertWebhookHmacHelpers(OpenJobsClient) {
  assert.ok(globalThis.crypto?.subtle, "Web Crypto SubtleCrypto must be available for webhook HMAC tests");
  const client = new OpenJobsClient({ fetch: createMockFetch(() => jsonResponse({})) });
  const body = JSON.stringify({ type: "payment.released", id: "evt_123" });
  const secret = "whsec_test_secret";

  const signature = await client.webhooks.sign({ secret, body });

  assert.match(signature, /^[a-f0-9]{64}$/);
  assert.equal(await client.webhooks.verify({ secret, body, signature }), true);
  assert.equal(await client.webhooks.verify({ secret, body: `${body}\n`, signature }), false);
  assert.equal(await client.webhooks.verify({ secret, body, signature: "" }), false);
}

if (!skipBuild) {
  buildSdk();
}

const sdkEntry = path.join(sdkDir, "dist", "index.mjs");
const sdk = await import(`${pathToFileURL(sdkEntry).href}?check=${Date.now()}`);

await assertRequestHeadersAndBaseUrl(sdk.OpenJobsClient);
await assertSandboxEnvironment(sdk.OpenJobsClient);
await assertErrorHandling(sdk.OpenJobsClient, sdk.OpenJobsApiError);
await assertRetryBehavior(sdk.OpenJobsClient);
await assertPublicDataEndpoints(sdk.OpenJobsClient);
await assertFeeCreditsEndpoint(sdk.OpenJobsClient);
await assertBadgeAndCardUrlHelpers(sdk.OpenJobsClient);
await assertWebhookHmacHelpers(sdk.OpenJobsClient);

console.log("OK @openjobs/sdk behavioral tests passed.");
