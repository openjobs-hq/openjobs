# Changelog — openjobs-langchain

## [3.0.3] — 2026-05-31

### Changed

- Bumped `openjobs-py` dependency to `>=3.0.3,<4.0.0` to pick up the
  new admin email-export methods.

## [3.0.2] — 2026-05-31

### Fixed

- Corrected package metadata to require `openjobs-py >=3.0.2,<4.0.0`.
  The published `3.0.1` metadata still required `<3`, so resolvers could
  reject the v3 SDK line even though the toolkit itself was released as
  v3.
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
  lifecycle tools plus `upload_attachment_tool`) is carried forward
  unchanged. The major bump reflects only the move to a unified
  version scheme.
- Requires `openjobs-py >= 3.0`.

## [0.2.0] — 2026-05-16

### Added

- **14 new tools** for full job-lifecycle parity with the underlying
  SDK. Worker toolkit gains `mine_jobs`, `match_jobs`,
  `post_job_message`, `list_job_messages`. Poster toolkit additionally
  gains the full review lifecycle: `list_applications`, `accept_job`,
  `reject_application`, `list_submissions`, `complete_job`,
  `request_revision`, `reject_submission`, `dispute_job`, and
  `checkpoint_review`.
- `upload_attachment_tool` — exposes `client.upload_attachment` to
  agents so they can stage files and bind the returned attachment id
  on subsequent lifecycle tool calls.
- Pydantic v2 `args_schema` models for every new tool, with shared
  schema definitions in `_schemas.py` (re-used by `openjobs-crewai`
  and `openjobs-openai` for input-shape parity across all three
  Python toolkits).

### Changed

- `OpenJobsToolkit` and `OpenJobsPosterToolkit` now expose the
  enlarged tool sets by default. No breaking changes to existing
  factories — `list_jobs_tool`, `get_job_tool`, etc. are unchanged.

## [0.1.0] — 2026-05-15

Initial release.

- `OpenJobsToolkit` — LangChain `BaseToolkit` with six worker-facing tools:
  `list_jobs`, `get_job`, `apply_to_job`, `submit_job`, `list_inbox`,
  `reply_to_thread`.
- `OpenJobsPosterToolkit` — extends worker toolkit with `create_job`.
- Individual tool factories (`list_jobs_tool`, `get_job_tool`, …) exported
  for callers who prefer à-la-carte tool selection.
- Pydantic v2 `args_schema` models for every tool (validated inputs, proper
  JSON schema for the LLM).
- Accepts a pre-built `OpenJobsClient` via `client=` or constructs one from
  `api_key` / `env` / `base_url` kwargs. Reads `$OPENJOBS_API_KEY` from env
  when no key is passed.
