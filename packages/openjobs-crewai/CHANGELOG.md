# Changelog — openjobs-crewai

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
