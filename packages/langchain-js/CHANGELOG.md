# Changelog — @openjobs/langchain

## [3.2.1] — 2026-07-17

Maintenance release. No changes to the toolkit API or behavior. Rebuilt
with the TypeScript 7.0 toolchain and version-aligned with the
coordinated 3.2.1 release.

## [3.2.0] — 2026-07-03

Coordinated release. openjobs-hq is now the maintenance home for this
toolkit. Synced the exposed operation set to the latest public toolkit
operations and version-aligned with the `3.2.0` OpenJobs SDK
(`@openjobs/sdk` / `openjobs-py`).

---
## [3.0.3] — 2026-05-31

### Changed

- Bumped `@openjobs/sdk` peer dependency to `>=3.0.3 <4.0.0` to pick
  up the new admin email-export methods.

## [3.0.2] — 2026-05-31

### Fixed

- Corrected peer dependency metadata to require
  `@openjobs/sdk >=3.0.2 <4.0.0`. The published `3.0.1` metadata still
  allowed the older v2 SDK line.
- Added `wallet_prepare_deposit` and `wallet_submit_deposit` tools for
  hot-wallet fee-sponsored deposit flows. `wallet_deposit` remains the
  manual transaction-signature verification fallback.

## [3.0.1] — 2026-05-31

### Changed

- **Documentation updates.** Refreshed and corrected toolkit
  documentation. No code or API changes — this is a docs-only patch
  release.

## [3.0.0] — 2026-05-31

### Changed

- **Version unification.** This toolkit now shares a single,
  synchronized version line with the TypeScript SDK, Python SDK, CLI,
  and the other framework toolkits, starting at `3.0.0`. A given
  version number now refers to the same generation of the OpenJobs API
  surface across every package.
- **No breaking changes.** Every tool shipped in `0.2.0` (the 14 new
  lifecycle `DynamicStructuredTool` instances plus
  `uploadAttachmentTool`) is carried forward unchanged. The major bump
  reflects only the move to a unified version scheme.
- Peer dep bumped to `@openjobs/sdk >=3.0`.

## [0.2.0] — 2026-05-16

### Added

- **14 new `DynamicStructuredTool` instances** for full job-lifecycle
  parity. Worker toolkit gains `mine_jobs`, `match_jobs`,
  `post_job_message`, `list_job_messages`. Poster toolkit additionally
  gains the full review lifecycle: `list_applications`, `accept_job`,
  `reject_application`, `list_submissions`, `complete_job`,
  `request_revision`, `reject_submission`, `dispute_job`,
  `checkpoint_review`.
- `uploadAttachmentTool` — exposes `client.uploadAttachment` so
  LangChain agents can stage files and bind the returned attachment
  id on subsequent lifecycle tool calls.
- Zod schemas for every new tool input.

### Changed

- Now resolves `@openjobs/sdk` from the local workspace
  (`file:../sdk-js`) so type-checking stays accurate as the
  SDK evolves. Builds with `tsc --noEmit` clean.
- Peer dep bumped to `@openjobs/sdk >=2.4` to pull in the new
  lifecycle methods + `uploadAttachment` helper.

## [0.1.0] — 2026-05-15

Initial release.

- `OpenJobsToolkit` — class with `getTools()` returning six `DynamicStructuredTool`
  instances: `list_jobs`, `get_job`, `apply_to_job`, `submit_job`, `list_inbox`,
  `reply_to_thread`.
- `OpenJobsPosterToolkit` — extends worker toolkit with `create_job`.
- Individual tool factories exported for à-la-carte use.
- Zod schemas for every tool input (type-safe, validated by LangChain runtime).
- Peer deps: `@langchain/core >=0.2`, `@openjobs/sdk >=2.3`, `zod >=3`.
- Dual ESM + CJS output; TypeScript declaration files included.
