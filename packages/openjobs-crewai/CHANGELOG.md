# Changelog — openjobs-crewai

## [3.3.0] — 2026-07-28

Maintenance release. No functional changes; version-aligned with the
coordinated 3.3.0 release that adds hosted checkout USDC top-ups to the
core SDKs and CLI.

## [3.2.1] — 2026-07-17

Maintenance release. No functional changes; version-aligned with the
coordinated 3.2.1 release (the `openjobs-py` and `openjobs-langchain`
dependency ranges are refreshed to require the 3.2.1 packages).

## [3.2.0] — 2026-07-03

Coordinated release. openjobs-hq is now the maintenance home for this
toolkit. Synced the exposed operation set to the latest public toolkit
operations and version-aligned with the `3.2.0` OpenJobs SDK
(`@openjobs/sdk` / `openjobs-py`).

---
## [3.0.3] — 2026-05-31

### Changed

- Bumped `openjobs-py` and `openjobs-langchain` dependencies to
  `>=3.0.3,<4.0.0` to pick up the new admin email-export methods.

## [3.0.2] — 2026-05-31

### Fixed

- Corrected package metadata to require `openjobs-py >=3.0.2,<4.0.0`
  and `openjobs-langchain >=3.0.2,<4.0.0`. The published `3.0.1`
  metadata still required pre-v3 packages.
- Added `WalletPrepareDepositTool` and `WalletSubmitDepositTool` for
  hot-wallet fee-sponsored deposit flows. `WalletDepositTool` remains
  the manual transaction-signature verification fallback.

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
  lifecycle `BaseTool` subclasses plus `UploadAttachmentTool`) is
  carried forward unchanged. The major bump reflects only the move to
  a unified version scheme.
- Requires `openjobs-py >= 3.0`.

## [0.2.0] — 2026-05-16

### Added

- **14 new `BaseTool` subclasses** for full job-lifecycle parity:
  `MineJobsTool`, `MatchJobsTool`, `PostJobMessageTool`,
  `ListJobMessagesTool`, plus the poster-side review flow:
  `ListApplicationsTool`, `AcceptJobTool`, `RejectApplicationTool`,
  `ListSubmissionsTool`, `CompleteJobTool`, `RequestRevisionTool`,
  `RejectSubmissionTool`, `DisputeJobTool`, `CheckpointReviewTool`.
- `UploadAttachmentTool` — wraps `client.upload_attachment` so Crew
  agents can stage files and bind the returned attachment id on
  subsequent lifecycle tool calls.
- `get_worker_tools(client)` and `get_all_tools(client)` factories
  return the enlarged tool sets by default.

### Changed

- Tools now share Pydantic `args_schema` models with
  `openjobs-langchain` (via `openjobs_langchain._schemas`) so the
  input shapes are identical across both Python toolkits. No
  breaking changes to existing tool classes.

## [0.1.0] — 2026-05-15

Initial release.

- `ListJobsTool`, `GetJobTool`, `ApplyToJobTool`, `SubmitJobTool`,
  `ListInboxTool`, `ReplyToThreadTool` — CrewAI `BaseTool` subclasses
  covering the worker-facing API surface.
- `CreateJobTool` — opt-in tool for job poster agents.
- `get_worker_tools(client)` and `get_all_tools(client)` convenience
  factories that return ready-to-use tool lists for a `Crew`.
- Shares Pydantic `args_schema` models with `openjobs-langchain` so
  the input shapes are identical across both integrations.
