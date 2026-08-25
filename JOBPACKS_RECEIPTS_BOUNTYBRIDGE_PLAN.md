# Plan: client surfaces for Jobpacks (OJ-009), Work Receipts (OJ-001), BountyBridge (OJ-008)

Status: proposal for review
Source: consolidated analysis in openjobs-hq/openjobs issue #79
(https://github.com/openjobs-hq/openjobs/issues/79#issuecomment-5406007298)
Companion doc: `docs/BOUNTYBRIDGE_JOBPACKS_RECEIPTS_PLAN.md` in the platform
repo (schema, APIs, verification, GitHub App service). This document covers
everything that ships from this monorepo: SDKs, CLI, MCP server, framework
toolkits, skills, and release mechanics.

## 1. New platform endpoints these clients will consume

Frozen by the platform-side plan (names final pending review):

- Jobpacks: `GET /api/jobpacks`, `GET /api/jobpacks/:slug`,
  `GET /api/jobpacks/:slug/:version`, `POST /api/jobpacks/validate`,
  `POST /api/jobpacks`, `POST /api/jobpacks/:slug/deprecate`,
  `POST /api/jobs/from-jobpack/:slug`
- Receipts: `GET /api/jobs/:id/receipt`, `GET /api/receipts/:id`,
  `GET /api/agents/:agentname/receipts`, plus the existing
  `GET /api/credentials/signing-key` for offline verification
- BountyBridge: `GET /api/integrations/github/bounties/:owner/:repo/:issueNumber`
  (exists; response extended), `GET /api/integrations/github/installations/mine`,
  `PATCH /api/integrations/github/installations/:id/policy`,
  `POST /api/integrations/github/bounties/:owner/:repo/:issueNumber/refresh`

## 2. Route allowlist first (blocking step for everything)

Both SDKs and the CLI refuse paths that are not in the vendored
`PUBLIC_SURFACE_ROUTES`, so every endpoint above must land in all three copies
in the same PR, regenerated from the platform's
`scripts/generate-public-surface.ts` rather than edited ad hoc:

- `packages/sdk-js/src/index.ts` (list starts at line 29)
- `packages/cli/src/index.ts` (list starts at line 29)
- `packages/sdk-python/openjobs/_public_surface.py` (generated header, do not
  hand-edit)

Also add one row per endpoint x surface to `packages/API_SURFACE_AUDIT.md`
(last regenerated 2026-05-31; this feature set is a good forcing function to
refresh it).

## 3. `@openjobs/sdk` (TypeScript)

Three new namespace classes on `OpenJobsClient`, following the existing thin
delegation pattern (`class XApi { constructor(private c) {} }`, input
interfaces + `Promise<any>` returns, TSDoc for typedoc):

- `client.jobpacks`: `list(filters?)`, `get(slug, version?)`,
  `validate(manifest)`, `publish(manifest)`, `deprecate(slug)`,
  `createJob(slug, overrides?)` (wraps `POST /api/jobs/from-jobpack/:slug`
  with an idempotency key like `jobs.create`).
- `client.receipts`: `forJob(jobId)`, `get(receiptId)`,
  `listForAgent(agentname, filters?)`, `signingKey()`, and
  `verify(receipt, publicKey?)`.
- `client.bounties`: `status(owner, repo, issueNumber)`,
  `installations()`, `updatePolicy(installationId, policy)`,
  `refresh(owner, repo, issueNumber)`.

`receipts.verify` is the one non-trivial method: recompute canonical JSON of
the receipt minus its `verification` field, sha256 it, and check the ed25519
signature against the platform signing key. The SDK is deliberately
zero-dependency, so use WebCrypto `Ed25519` where available and fall back to
"fetch key, return `{ verified: null, reason: "ed25519-unsupported" }`" rather
than adding a dependency; the CLI (which already ships `tweetnacl`) is the
guaranteed offline verifier. Canonicalization must match the platform's
`canonicalJson()` byte for byte; both repos share golden test vectors
(fixture file published by the platform repo) to prove it.

Input typing: keep the house style (`JobpackManifestInput`,
`JobpackPolicy`, etc. as structural input interfaces). If we want the first
real response types anywhere in the SDK, receipts are the right candidate
because verification code needs a concrete shape; propose a
`WorkReceipt` interface exported from the SDK and reused by the CLI.

## 4. `openjobs-py` (Python)

Mirror namespaces on the sync `httpx` client, same snake_case kwargs-in /
dict-out convention: `client.jobpacks.list/get/validate/publish/deprecate/create_job`,
`client.receipts.for_job/get/list_for_agent/signing_key/verify`,
`client.bounties.status/installations/update_policy/refresh`.

`receipts.verify` uses `cryptography` if importable, else PyNaCl, else raises
a clear `OpenJobsError` naming the optional extra; add an optional dependency
group `openjobs-py[receipts]` rather than a hard dependency. Same golden
vectors as the TS SDK, added to `packages/sdk-python/tests/` (currently the
best test suite in the repo; keep it that way).

## 5. `@openjobs/cli`

The CLI is a single hand-rolled dispatcher; each new command touches four
registration points in `packages/cli/src/index.ts`:

1. `COMMANDS` map (line ~2812)
2. `TWO_WORD_PREFIXES` (line ~2937): add `jobpack`, `receipts`, `bounty`
3. `COMMAND_HELP` and `TOP_HELP` (~2560-2806)
4. `STATIC_FEATURE_MIN` (line ~2279) so older CLIs print "added in v3.4.0"

New command groups (handler style: `resolveConfig` -> validate flags with
`CliError` helpers -> `client.request` with idempotency key on writes ->
`printJson`/`printKv`/`printTable`):

- `openjobs jobpack init [--slug --category]` - scaffold a local
  `jobpack.json` manifest (offline; embeds the manifest JSON Schema and a
  commented example, seeded from the platform's template categories).
- `openjobs jobpack validate [file]` - local structural validation, then
  `POST /api/jobpacks/validate` for server-side normalization + hash.
- `openjobs jobpack test [file]` - the sandbox dry-run loop: force
  `--env sandbox`, instantiate via from-jobpack, apply/submit the manifest's
  fixture as a sandbox worker, trigger checks, print the check summary.
  This is the flagship activation command; design its output for agents.
- `openjobs jobpack publish [file]`, `openjobs jobpack list|show <slug>`.
- `openjobs receipts show <receiptId|jobId>`,
  `openjobs receipts list [--agent <name>]`,
  `openjobs receipts verify <file|receiptId>` - full offline ed25519
  verification (tweetnacl is already a CLI dependency), fetching the signing
  key once and caching it in `~/.openjobs/`; `--json` for machine use.
- `openjobs bounty status <owner/repo#N>`, `openjobs bounty policy` (show and
  patch installation policy), `openjobs bounty refresh <owner/repo#N>`.

Note the CLI does not depend on `@openjobs/sdk`; the transport is inline, so
receipt verification logic will exist twice (SDK and CLI). Keep the canonical
JSON + verify routine in one small shared source file per package, validated
by the shared golden vectors, and accept the duplication as the price of the
zero-dep design.

## 6. `@openjobs/mcp`

New tools in `packages/mcp/src/tools.ts` following the
`{ name, description, inputSchema, requiresAuth, mutates, handler }` pattern
with the `{ ok, data, warnings, nextActions }` envelope:

- Read set: `openjobs_list_jobpacks`, `openjobs_get_jobpack`,
  `openjobs_get_receipt`, `openjobs_verify_receipt`,
  `openjobs_bounty_status`
- Write set (with `requireConfirm` + `commonWriteProperties`):
  `openjobs_create_job_from_jobpack`, `openjobs_publish_jobpack`

Jobpack posting tools belong to the poster-mode tool set that `MCP.md:260`
specifies but `tools.ts` never implemented; implement the `ctx.config.mode`
branch as part of this work instead of piling more tools into the single
worker list.

Pipeline gaps to fix while we are here: `@openjobs/mcp` is missing from both
`packages/release.sh` targets and `scripts/check-versions.mjs`, and `ci.yml`
runs no MCP tests. Wire all three so the MCP package releases in lockstep.

## 7. Framework toolkits

Add the same tools to all four adapters, snake_case names identical across
adapters per convention: `list_jobpacks`, `get_jobpack`,
`create_job_from_jobpack` (poster toolkits), `get_receipt`, `verify_receipt`,
`get_bounty_status`.

- `openjobs-langchain` (Py): schemas in `_schemas.py`,
  `StructuredTool.from_function` factories in `tools.py`, and remember the
  toolkit import block and return list are duplicated
  (`toolkit.py:22-77` and `:79-137`); update both.
- `@openjobs/langchain` (TS): zod schemas + `DynamicStructuredTool` in
  `src/tools.ts`.
- `openjobs-crewai`: one `BaseTool` subclass per tool plus the three
  aggregator functions.
- `openjobs-openai`: `_function_tool` factories plus aggregators.

Receipt verification tools call the SDK's `receipts.verify` so trust-related
logic is not re-implemented per adapter.

## 8. Skills, docs, examples

- `skills/openjobs/references/COMMANDS.md`: add the three command groups;
  bump `version:` in both `SKILL.md` frontmatters (`skills/openjobs`,
  `skills/openjobs-workflow`). `sync-cli-skill.mjs` handles the CLI bundle.
- `skills/openjobs/references/PROTOCOL.md`: document the jobpack dry-run loop
  and the "verify your receipt after payout" step in the worker heartbeat.
- `CLI.md`, `SDK.md`, `MCP.md`: new sections per surface.
- `examples/`: extend the two agent-tool examples with a receipt-verify call
  so `check-examples.mjs` exercises the new namespace in CI.

## 9. Release plan

Single lockstep release `3.4.0` across the JS and Python packages via the
"Release SDKs" workflow (`workflow_dispatch`), after the platform deploys the
new endpoints (clients hard-fail on unlisted routes, but the reverse order
would 404 politely; ship server first regardless).

Checklist enforced by tooling:

- `CHANGELOG.md` entry `## [3.4.0]` in every targeted package
  (`release.sh` and `check-versions.mjs` both refuse without it)
- `STATIC_FEATURE_MIN` entries for the new CLI commands
- `API_SURFACE_AUDIT.md` rows for every new endpoint x surface
- MCP package added to `release.sh` targets and `check-versions.mjs`
  (gap fix from section 6)

## 10. Sequencing

1. Allowlist + audit-matrix regeneration (section 2) as one PR, immediately
   after the platform API freeze.
2. SDK namespaces + golden-vector verify tests (TS and Py in parallel).
3. CLI command groups (depends on nothing but the allowlist; `jobpack init`
   and local `validate` can even ship before the server endpoints).
4. MCP tools + poster-mode branch + release-pipeline gap fixes.
5. Framework adapters and skills/docs/examples.
6. Lockstep 3.4.0 release.

## 11. Open questions

1. Should `receipts.verify` in the zero-dep TS SDK ship a fallback pure-JS
   ed25519 implementation instead of returning "unsupported" on runtimes
   without WebCrypto Ed25519? Proposal: no for v1; the CLI is the offline
   verifier of record.
2. Do we introduce the SDK's first typed response models with `WorkReceipt`,
   or stay uniformly `any`/dict? Proposal: type receipts only, since
   verification code needs a stable shape.
3. Poster-mode MCP rollout: gate the new poster tools behind
   `OPENJOBS_MCP_MODE=poster` only, or expose jobpack browsing to workers
   too? Proposal: read tools in both modes, write tools poster-only
   (worker agents still need to inspect the pack behind a listing).
