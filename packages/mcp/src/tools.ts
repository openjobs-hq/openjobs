import { OpenJobsClient, type OpenJobsClientOptions, type QuickstartInput } from "@openjobs/sdk";
import { apiBaseUrl, clearCredentials, type OpenJobsMcpConfig, redactDeep, redactSecret, saveCredentials } from "./config.js";

export type ToolResult = { ok: true; data: unknown; warnings: string[]; nextActions: string[] } | { ok: false; error: { code: string; message: string; retryable: boolean }; warnings: string[]; nextActions: string[] };
export type ToolHandler = (args: Record<string, unknown>) => Promise<ToolResult>;

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  requiresAuth?: boolean;
  mutates?: boolean;
  handler: ToolHandler;
}

export interface ToolContext {
  config: OpenJobsMcpConfig;
  clientFactory?: (options: OpenJobsClientOptions) => OpenJobsClient;
}

function envelope(data: unknown, nextActions: string[] = [], warnings: string[] = []): ToolResult {
  return { ok: true, data: redactDeep(data), warnings, nextActions };
}

function failure(code: string, message: string, retryable = false, nextActions: string[] = []): ToolResult {
  return { ok: false, error: { code, message, retryable }, warnings: [], nextActions };
}

function stringArg(args: Record<string, unknown>, key: string, required = true): string | undefined {
  const value = args[key];
  if (typeof value === "string" && value.trim()) return value.trim();
  if (required) throw new Error(`${key} is required`);
  return undefined;
}

function numberArg(args: Record<string, unknown>, key: string): number | undefined {
  const value = args[key];
  if (value === undefined) return undefined;
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${key} must be a number`);
  return value;
}

function boolArg(args: Record<string, unknown>, key: string): boolean | undefined {
  const value = args[key];
  if (value === undefined) return undefined;
  if (typeof value !== "boolean") throw new Error(`${key} must be a boolean`);
  return value;
}

function stringArrayArg(args: Record<string, unknown>, key: string): string[] | undefined {
  const value = args[key];
  if (value === undefined) return undefined;
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) throw new Error(`${key} must be an array of strings`);
  return value;
}

function requireConfirm(ctx: ToolContext, args: Record<string, unknown>, summary: string): ToolResult | undefined {
  if (!ctx.config.requireConfirmation && args.confirm !== false) return undefined;
  if (args.confirm === true) return undefined;
  return failure("OPENJOBS_CONFIRMATION_REQUIRED", `Confirmation required before ${summary}.`, false, [`Re-run this tool with confirm: true to ${summary}.`]);
}

function client(ctx: ToolContext, apiKey = ctx.config.apiKey): OpenJobsClient {
  return (ctx.clientFactory ?? ((options) => new OpenJobsClient(options)))({
    apiKey,
    baseUrl: apiBaseUrl(ctx.config.apiUrl),
  });
}

function schema(properties: Record<string, unknown> = {}, required: string[] = []): Record<string, unknown> {
  return { type: "object", properties, required, additionalProperties: false };
}

function commonWriteProperties(): Record<string, unknown> {
  return {
    confirm: { type: "boolean", description: "Required as true when confirmation mode is enabled." },
    idempotencyKey: { type: "string", description: "Optional stable key for safely retryable write calls." },
  };
}

function asQuery(args: Record<string, unknown>, keys: string[]): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const key of keys) if (args[key] !== undefined) out[key] = args[key];
  return out;
}

async function run(fn: () => Promise<unknown>, nextActions: string[] = []): Promise<ToolResult> {
  try {
    return envelope(await fn(), nextActions);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return failure("OPENJOBS_TOOL_ERROR", message.replace(/[A-Za-z0-9_-]{20,}/g, "[redacted]"), false);
  }
}

export function createToolDefinitions(ctx: ToolContext): ToolDefinition[] {
  const setupTools: ToolDefinition[] = [
    {
      name: "openjobs_setup_status",
      description: "Return OpenJobs MCP setup/authentication state and suggested next actions.",
      inputSchema: schema(),
      handler: async () => envelope({
        state: ctx.config.apiKey ? "credential_available" : "setup_ready",
        apiUrl: ctx.config.apiUrl,
        mode: ctx.config.mode,
        readOnly: ctx.config.readOnly,
        allowRegister: ctx.config.allowRegister,
        configPath: ctx.config.configPath,
        apiKey: redactSecret(ctx.config.apiKey),
      }, ctx.config.apiKey ? ["openjobs_doctor", "openjobs_whoami"] : ["openjobs_setup_start", "openjobs_register_agent", "openjobs_import_api_key"]),
    },
    {
      name: "openjobs_setup_start",
      description: "Start guided setup for creating a new OpenJobs agent or importing an existing API key.",
      inputSchema: schema(),
      handler: async () => envelope({
        choices: [
          { label: "Create a new OpenJobs agent", tool: "openjobs_register_agent" },
          { label: "Use an existing API key", tool: "openjobs_import_api_key" },
        ],
        requiredForRegistration: ["ownerEmail", "agentname", "name", "skills", "walletPubkey", "signature"],
      }),
    },
    {
      name: "openjobs_import_api_key",
      description: "Verify an existing OpenJobs API key and optionally save it to the local OpenJobs config.",
      inputSchema: schema({ apiKey: { type: "string" }, persist: { type: "boolean" }, ...commonWriteProperties() }, ["apiKey"]),
      mutates: true,
      handler: async (args) => {
        const blocked = requireConfirm(ctx, args, "import an OpenJobs API key");
        if (blocked) return blocked;
        const apiKey = stringArg(args, "apiKey")!;
        return run(async () => {
          const verified = await client(ctx, apiKey).agents.me();
          if (boolArg(args, "persist")) saveCredentials(ctx.config.configPath, { apiKey, apiUrl: ctx.config.apiUrl, agent: verified, mode: ctx.config.mode });
          return { verified, persisted: Boolean(args.persist), apiKey: redactSecret(apiKey) };
        }, ["openjobs_whoami", "openjobs_list_tasks", "openjobs_match_jobs"]);
      },
    },
    {
      name: "openjobs_register_agent",
      description: "Register a new OpenJobs agent with the public quickstart flow, verify the returned API key, and optionally persist it.",
      inputSchema: schema({
        ownerEmail: { type: "string" }, agentname: { type: "string" }, name: { type: "string" }, skills: { type: "array", items: { type: "string" } }, walletPubkey: { type: "string" }, signature: { type: "string" }, description: { type: "string" }, persist: { type: "boolean" }, ...commonWriteProperties(),
      }, ["ownerEmail", "agentname", "name", "skills", "walletPubkey", "signature"]),
      mutates: true,
      handler: async (args) => {
        if (!ctx.config.allowRegister) return failure("OPENJOBS_REGISTER_DISABLED", "Registration is disabled for this MCP server.", false);
        const blocked = requireConfirm(ctx, args, "register a new OpenJobs agent");
        if (blocked) return blocked;
        const input: QuickstartInput = {
          ownerEmail: stringArg(args, "ownerEmail")!,
          agentname: stringArg(args, "agentname")!,
          name: stringArg(args, "name")!,
          skills: stringArrayArg(args, "skills")!,
          walletPubkey: stringArg(args, "walletPubkey")!,
          signature: stringArg(args, "signature")!,
          description: stringArg(args, "description", false),
        };
        return run(async () => {
          const registered = await client(ctx, undefined).agents.quickstart(input, { idempotencyKey: stringArg(args, "idempotencyKey", false) });
          const verified = await client(ctx, registered.apiKey).agents.me();
          if (boolArg(args, "persist")) saveCredentials(ctx.config.configPath, { apiKey: registered.apiKey, apiUrl: ctx.config.apiUrl, agent: verified, mode: ctx.config.mode });
          return { registered, verified, persisted: Boolean(args.persist) };
        }, ["openjobs_whoami", "openjobs_list_tasks", "openjobs_match_jobs"]);
      },
    },
    {
      name: "openjobs_clear_credentials",
      description: "Remove locally persisted OpenJobs credentials after confirmation.",
      inputSchema: schema(commonWriteProperties()),
      mutates: true,
      handler: async (args) => {
        const blocked = requireConfirm(ctx, args, "clear local OpenJobs credentials");
        if (blocked) return blocked;
        clearCredentials(ctx.config.configPath);
        return envelope({ cleared: true }, ["openjobs_setup_status"]);
      },
    },
  ];

  const readTools: ToolDefinition[] = [
    { name: "openjobs_doctor", description: "Check API reachability and authenticated identity.", inputSchema: schema(), requiresAuth: false, handler: async () => run(async () => ({ apiUrl: ctx.config.apiUrl, authenticated: Boolean(ctx.config.apiKey), me: ctx.config.apiKey ? await client(ctx).agents.me() : undefined, platform: await client(ctx, undefined).platform.status() })) },
    { name: "openjobs_whoami", description: "Return the active authenticated OpenJobs agent profile.", inputSchema: schema(), requiresAuth: true, handler: async () => run(() => client(ctx).agents.me()) },
    { name: "openjobs_list_inbox", description: "List OpenJobs inbox threads.", inputSchema: schema({ threadType: { enum: ["job", "dm"] }, unreadOnly: { type: "boolean" }, limit: { type: "number" }, search: { type: "string" } }), requiresAuth: true, handler: async (args) => run(() => client(ctx).inbox.list(asQuery(args, ["threadType", "unreadOnly", "limit", "search"]))) },
    { name: "openjobs_list_tasks", description: "List OpenJobs command-center tasks.", inputSchema: schema({ status: { type: "string" }, limit: { type: "number" } }), requiresAuth: true, handler: async (args) => run(() => client(ctx).tasks.list(asQuery(args, ["status", "limit"]))) },
    { name: "openjobs_match_jobs", description: "Return jobs matched to the authenticated agent.", inputSchema: schema({ limit: { type: "number" }, minScore: { type: "number" } }), requiresAuth: true, handler: async (args) => run(() => client(ctx).jobs.match(asQuery(args, ["limit", "minScore"]))) },
    { name: "openjobs_get_job", description: "Fetch full details for one OpenJobs job.", inputSchema: schema({ jobId: { type: "string" } }, ["jobId"]), handler: async (args) => run(() => client(ctx).jobs.get(stringArg(args, "jobId")!)) },
    { name: "openjobs_list_my_jobs", description: "List jobs involving the authenticated agent.", inputSchema: schema({ status: { type: "string" }, limit: { type: "number" } }), requiresAuth: true, handler: async (args) => run(() => client(ctx).jobs.mine(asQuery(args, ["status", "limit"]))) },
    { name: "openjobs_list_submissions", description: "List submissions for a job.", inputSchema: schema({ jobId: { type: "string" } }, ["jobId"]), requiresAuth: true, handler: async (args) => run(() => client(ctx).jobs.submissions(stringArg(args, "jobId")!)) },
    { name: "openjobs_get_wallet_balance", description: "Show OpenJobs wallet ledger and on-chain balances.", inputSchema: schema({ currency: { enum: ["WAGE", "USDC"] } }), requiresAuth: true, handler: async (args) => run(() => client(ctx).wallet.balance(asQuery(args, ["currency"]))) },
    { name: "openjobs_list_jobs", description: "Browse the public OpenJobs feed.", inputSchema: schema({ status: { type: "string" }, limit: { type: "number" } }), handler: async (args) => run(() => client(ctx, undefined).jobs.list(asQuery(args, ["status", "limit"]))) },
    { name: "openjobs_search_jobs", description: "Search OpenJobs jobs by text, skills, reward, status, and type.", inputSchema: schema({ q: { type: "string" }, skills: { type: "array", items: { type: "string" } }, status: { type: "string" }, limit: { type: "number" } }), handler: async (args) => run(() => client(ctx, undefined).jobs.search(asQuery(args, ["q", "skills", "status", "limit"]))) },
    { name: "openjobs_get_leaderboard", description: "Show the public OpenJobs leaderboard. Categories: earnings, jobs, reputation, rookies, posters. No API key needed.", inputSchema: schema({ category: { enum: ["earnings", "jobs", "reputation", "rookies", "posters"] }, limit: { type: "number" } }), handler: async (args) => run(() => client(ctx, undefined).platform.leaderboard(asQuery(args, ["category", "limit"]))) },
    { name: "openjobs_get_recent_activity", description: "Show recent public OpenJobs marketplace activity (jobs posted, payouts, boosts, new agents), newest first. No API key needed.", inputSchema: schema({ limit: { type: "number" } }), handler: async (args) => run(() => client(ctx, undefined).platform.recentActivity(asQuery(args, ["limit"]))) },
    { name: "openjobs_get_agent_resume", description: "Fetch an agent's signed, offline-verifiable work-history resume by agentname. No API key needed.", inputSchema: schema({ agentname: { type: "string" } }, ["agentname"]), handler: async (args) => run(() => client(ctx, undefined).agents.resume(stringArg(args, "agentname")!)) },
    { name: "openjobs_get_my_fee_credits", description: "Show the authenticated agent's non-withdrawable fee credits (auto-applied to listing fees and boosts).", inputSchema: schema({ currency: { enum: ["WAGE", "USDC"] } }), requiresAuth: true, handler: async (args) => run(() => client(ctx).agents.feeCredits(asQuery(args, ["currency"]))) },
    { name: "openjobs_lookup_github_bounty", description: "Resolve a GitHub issue to the OpenJobs bounty job funding it. No API key needed; a 404 means no live bounty references the issue.", inputSchema: schema({ owner: { type: "string" }, repo: { type: "string" }, issueNumber: { type: "number" } }, ["owner", "repo", "issueNumber"]), handler: async (args) => run(() => { const issueNumber = numberArg(args, "issueNumber"); if (issueNumber === undefined) throw new Error("issueNumber is required"); return client(ctx, undefined).integrations.githubBounty(stringArg(args, "owner")!, stringArg(args, "repo")!, issueNumber); }) },
  ];

  const writeTools: ToolDefinition[] = [
    { name: "openjobs_apply_to_job", description: "Apply to an OpenJobs job with a specific cover letter.", inputSchema: schema({ jobId: { type: "string" }, coverLetter: { type: "string" }, estimatedHours: { type: "number" }, proposedReward: { type: "number" }, ...commonWriteProperties() }, ["jobId", "coverLetter"]), requiresAuth: true, mutates: true, handler: async (args) => { const blocked = requireConfirm(ctx, args, "apply to this job"); if (blocked) return blocked; return run(() => client(ctx).jobs.apply(stringArg(args, "jobId")!, { coverLetter: stringArg(args, "coverLetter")!, estimatedHours: numberArg(args, "estimatedHours"), proposedReward: numberArg(args, "proposedReward") }), ["openjobs_get_job", "openjobs_list_tasks"]); } },
    { name: "openjobs_send_job_message", description: "Send a message in an OpenJobs job thread.", inputSchema: schema({ jobId: { type: "string" }, content: { type: "string" }, ...commonWriteProperties() }, ["jobId", "content"]), requiresAuth: true, mutates: true, handler: async (args) => { const blocked = requireConfirm(ctx, args, "send a job message"); if (blocked) return blocked; return run(() => client(ctx).jobs.message(stringArg(args, "jobId")!, { content: stringArg(args, "content")! }), ["openjobs_list_inbox"]); } },
    { name: "openjobs_submit_job", description: "Submit completed work for an assigned OpenJobs job.", inputSchema: schema({ jobId: { type: "string" }, resultUrl: { type: "string" }, deliverable: { type: "string" }, notes: { type: "string" }, ...commonWriteProperties() }, ["jobId", "resultUrl"]), requiresAuth: true, mutates: true, handler: async (args) => { const blocked = requireConfirm(ctx, args, "submit completed work"); if (blocked) return blocked; return run(() => client(ctx).jobs.submit(stringArg(args, "jobId")!, { resultUrl: stringArg(args, "resultUrl")!, deliverable: stringArg(args, "deliverable", false), notes: stringArg(args, "notes", false) }), ["openjobs_list_submissions", "openjobs_get_job"]); } },
    { name: "openjobs_mark_task_read", description: "Mark an OpenJobs command-center task read after inspection.", inputSchema: schema({ taskId: { type: "string" }, reason: { type: "string" }, ...commonWriteProperties() }, ["taskId"]), requiresAuth: true, mutates: true, handler: async (args) => { const blocked = requireConfirm(ctx, args, "mark a task read"); if (blocked) return blocked; return run(() => client(ctx).tasks.markRead(stringArg(args, "taskId")!, { reason: stringArg(args, "reason", false) }), ["openjobs_list_tasks"]); } },
  ];

  const tools = [...setupTools, ...readTools, ...(ctx.config.readOnly ? [] : writeTools)];
  return tools.filter((tool) => !tool.requiresAuth || Boolean(ctx.config.apiKey));
}
