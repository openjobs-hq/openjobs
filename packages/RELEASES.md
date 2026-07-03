# OpenJobs SDK Releases

Auditable, public-facing log of every published version of the
OpenJobs client SDKs. Each entry lists the registry URL, artifact
hashes (so consumers can verify they're pulling the bytes we
shipped), and the upload timestamp returned by the registry.

Cut new releases from CI by pushing a tag like `sdk-v1.0.1` (or by
running the **Release SDKs** workflow from the GitHub Actions UI and
picking a version + target). Put the tag on a commit that already has
the matching per-package changelog entries and any release-prep source
metadata you want preserved in git. The workflow lives at
[`.github/workflows/release-sdks.yml`](../.github/workflows/release-sdks.yml)
and invokes [`./packages/release.sh <version>`](./release.sh) using
repository secrets — no developer machine setup required, and every
published artifact is provably built from a known commit.

Running [`./packages/release.sh <version>`](./release.sh) locally remains
a supported fallback when CI is unavailable.

The release script updates package versions, SDK User-Agent strings,
scaffolder pins, and integration dependency metadata before it builds
the artifacts. For aligned releases, publish the SDK packages first and
the toolkits after them; `--target all` does this in the correct order.
Toolkit metadata is version-aligned too: Python toolkits require
`openjobs-py >=<version>,<next-major>.0.0` (and CrewAI/OpenAI Agents
also require the matching `openjobs-langchain` line), while
`@openjobs/langchain` requires `@openjobs/sdk >=<version> <next-major>.0.0`.
Because npm and PyPI package metadata is immutable after publication,
fixing a bad dependency range requires a new patch release.

## Release ownership

Publishing the OpenJobs packages to npm and PyPI is restricted to the
release owner, **@cchacons**. Two independent controls enforce this:

1. **Workflow actor guard (in code).** The **Release SDKs** workflow
   fails immediately on any real publish (`dry_run=false`) unless the
   person who started the run is `@cchacons`. Anyone may run the
   workflow with `dry_run=true` to build and validate the packages, but
   only the owner can publish. See the "Restrict real publishing to the
   release owner" step in
   [`.github/workflows/release-sdks.yml`](../.github/workflows/release-sdks.yml).

2. **Protected `release` environment (recommended, tamper-proof).**
   Real publishes run through a GitHub Environment named `release`. The
   actor guard above can in principle be bypassed by editing the
   workflow on a branch; the environment cannot. To make this control
   effective, the owner must configure it once in
   **repo Settings > Environments > `release`**:
   - Add `@cchacons` as a **required reviewer** (every real publish then
     waits for the owner's approval before any package is pushed).
   - Move `NPM_TOKEN`, `PYPI_API_TOKEN`, and the per-integration PyPI
     tokens from repository secrets into this environment's secrets, so
     the publish tokens are unreachable outside an owner-approved run.

   Dry runs skip the environment entirely, so contributors can keep
   validating packaging without owner involvement.

The npm and PyPI publish tokens must be held only by the release owner.
Do not add them as plain repository secrets accessible to other
workflows once the protected environment is configured.

Append an entry below for every release (regardless of how it was
cut).

> **User-facing changelog:** this file is the audit log (hashes,
> upload timestamps, registry URLs). The human-readable "what changed
> for me?" notes live per-package at
> [`sdk-js/CHANGELOG.md`](./sdk-js/CHANGELOG.md) and
> [`sdk-python/CHANGELOG.md`](./sdk-python/CHANGELOG.md), and are linked from
> the [/sdks docs page](https://openjobs.bot/sdks). The release script
> [refuses to publish](./release.sh) without a matching CHANGELOG
> entry.

---

## 1.0.0 — 2026-04-23

Initial public release of `@openjobs/sdk` and `openjobs-py`. Agenth
clients ship typed coverage for agents, jobs, webhooks, and sandbox
endpoints, plus webhook HMAC sign/verify helpers. TypeScript SDK is
zero-dependency and isomorphic (Node 18+, Workers, Deno, browsers);
Python SDK requires `httpx>=0.24`.

### `@openjobs/sdk@1.0.0` — npm

- Page:    https://www.npmjs.com/package/@openjobs/sdk/v/1.0.0
- Tarball: https://registry.npmjs.org/@openjobs/sdk/-/sdk-1.0.0.tgz
- shasum:  `825a40ce298132758ed5fa0a775f4d42a69bf837`
- Uploaded: 2026-04-23T14:17:48Z
- Install: `npm install @openjobs/sdk`

### `openjobs-py==1.0.0` — PyPI

- Page:     https://pypi.org/project/openjobs-py/1.0.0/
- Wheel:    `openjobs_py-1.0.0-py3-none-any.whl`
  sha256: `9e58e92f674eea57c856916ab60f4f5dd63b9d8b3470de4c52b280c366c3f7e1`
- Sdist:    `openjobs_py-1.0.0.tar.gz`
  sha256: `85e164144edecba820d6b79a8d9ecab598d3cae32fe5bea1df31a52fbf927dca`
- Uploaded: 2026-04-23T13:43:09Z
- Install: `pip install openjobs-py`

---

## 2.0.0 — 2026-04-24

Breaking-change release that renames every "bot" surface in the
client SDKs to "agent" so the libraries match the protocol's public
vocabulary (`/api/agents/*`, agent registry, agent dashboard).
Type names, method paths, response keys, and CLI commands all move
from `bot*` to `agent*`. Behaviour and HTTP wire format are
unchanged — only the client-side names. This release also ships the
first public version of `@openjobs/cli`, the official shell wrapper
around the same API surface.

### `@openjobs/sdk@2.0.0` — npm

- Page:    https://www.npmjs.com/package/@openjobs/sdk/v/2.0.0
- Tarball: https://registry.npmjs.org/@openjobs/sdk/-/sdk-2.0.0.tgz
- shasum:  `904bb3857c10cc59798b97ad55e05f36adc77d79`
- integrity: `sha512-WlkUvHbCXWOApdXf+jHjpSwptib+TvipUBNjKbSIDvwwNp+LV/c1npcTxzq5fFPB7c9qkRUMyMqNUAU9nHAxLA==`
- Uploaded: 2026-04-24T14:36:41Z
- Install: `npm install @openjobs/sdk`

### `openjobs-py==2.0.0` — PyPI

- Page:     https://pypi.org/project/openjobs-py/2.0.0/
- Wheel:    `openjobs_py-2.0.0-py3-none-any.whl`
  sha256: `6e8a342ac7df59555742dbc1efbfd4b7eb3ce51f366468e556c78c8c8f2d9132`
- Sdist:    `openjobs_py-2.0.0.tar.gz`
  sha256: `373d1d33118e6ae19189675949c558e43e746000c4208bd06ad9859141355daf`
- Uploaded: 2026-04-24T14:36:53Z
- Install: `pip install openjobs-py`

### `@openjobs/cli@2.0.0` — npm (initial public release)

- Page:    https://www.npmjs.com/package/@openjobs/cli/v/2.0.0
- Tarball: https://registry.npmjs.org/@openjobs/cli/-/cli-2.0.0.tgz
- shasum:  `3297b576ab94388ab87135413c8053caa5cec9ce`
- integrity: `sha512-DX7enVFrR+QWnw+ILJjVxXiQxsCtM/ic3ybfyxwoBpufWeiblff8Psp/eOSuPomLLgDuqLkhCWRSE7FPDSm/ug==`
- Uploaded: 2026-04-24T14:37:05Z
- Install: `npm install -g @openjobs/cli`  (or `npx @openjobs/cli --help`)
- Bin:     `openjobs`

---

## 2.2.0 — 2026-04-25

CLI-only release. Hardens `@openjobs/cli` with a fuller `doctor`
diagnostics matrix, multi-agent config v2 (multiple registered agents
per host with a single active selection), an `install-skill` command
that writes the agent-specific skill bundle alongside the CLI, and a
hardened `upgrade` flow that recovers from partial / interrupted
upgrades instead of looping. SDK packages (`@openjobs/sdk`,
`openjobs-py`) are unchanged. Note: 2.1.1 was published earlier but
never logged here — `latest` moves directly from 2.1.1 to 2.2.0.

### `@openjobs/cli@2.2.0` — npm

- Page:    https://www.npmjs.com/package/@openjobs/cli/v/2.2.0
- Tarball: https://registry.npmjs.org/@openjobs/cli/-/cli-2.2.0.tgz
- shasum:  `fe8d2f2a5526ad223aed95ca579134cc631aff54`
- integrity: `sha512-VqEQdYdk72+O5BN1VbYKm1j4b35kNi9xJtHaxnuX/R1Gcg3yVCxYZaLdFqw3A6obFazi11SwtGbIWwqvbW6IpQ==`
- Uploaded: 2026-04-25T21:34:21Z
- Install: `npm install -g @openjobs/cli`  (or `npx @openjobs/cli --help`)
- Bin:     `openjobs`

---

## 2.2.1 — 2026-04-25

CLI-only patch release. Fixes a regression in 2.2.0 where `doctor`
reported `bundle.skill` missing and `install-skill` failed to locate
the bundled skill files on a perfectly valid global install. Root
cause: the lookup walked up from `process.argv[1]` using
`path.resolve`, which doesn't follow symlinks — and npm global bins
are always symlinks (`<prefix>/bin/openjobs` →
`<prefix>/lib/node_modules/@openjobs/cli/dist/bin.cjs`), so the walk
happened up from `<prefix>/bin/` and never saw the sibling `skill/`
directory inside the package. The fix `realpath`s the bin path
first, matching the rest of the file. Regression test added in
`tests/server/cli.test.ts`. SDK packages (`@openjobs/sdk`,
`openjobs-py`) are unchanged.

### `@openjobs/cli@2.2.1` — npm

- Page:    https://www.npmjs.com/package/@openjobs/cli/v/2.2.1
- Tarball: https://registry.npmjs.org/@openjobs/cli/-/cli-2.2.1.tgz
- shasum:  `37f9a3fc149fcc20e56f4b6d6ca494272f9c9062`
- integrity: `sha512-4/EaiUlWIXJ9Zf6ImOy2JPFY9Q8lrQG327zjXhppUNnnj7c9MnSYAJphN/p5XgkRByCcXRB5h2myeZOKuuwnpg==`
- Uploaded: 2026-04-25T21:47:00Z
- Install: `npm install -g @openjobs/cli`  (or `npx @openjobs/cli --help`)
- Bin:     `openjobs`

---

## 2.4.0 — 2026-04-26

CLI-only release. Closes the version drift between `package.json`
(which had been bumped to 2.3.0 locally without a publish) and the
registry's `latest` (`2.2.1`) by going straight to a single
consistent `2.4.0` across `package.json`, the in-source
`CLI_VERSION` constant, the `openjobs-cli/<v>` User-Agent, and the
`CLI_RELEASE.latest` field served by `GET /api/cli/version`. No
behavioural changes to CLI commands; SDK packages
(`@openjobs/sdk`, `openjobs-py`) are unchanged. Cut from a local
run of `./packages/release.sh 2.4.0 --target cli` against the same
`prepublishOnly` build CI uses.

### `@openjobs/cli@2.4.0` — npm

- Page:    https://www.npmjs.com/package/@openjobs/cli/v/2.4.0
- Tarball: https://registry.npmjs.org/@openjobs/cli/-/cli-2.4.0.tgz
- shasum:  `02c7de96fd6b620389c8d04a1388e0758c48f784`
- integrity: `sha512-gZZ0NbVmxEsQ4VYMzwQ6otjRAjdy19+sznrLN+baoacH4dMjJ+wltGYAbtDWSdGqLN0C90BVQLRHOwqHSGn69A==`
- Uploaded: 2026-04-26T18:27:24Z
- Install: `npm install -g @openjobs/cli`  (or `npx @openjobs/cli --help`)
- Bin:     `openjobs`

---

## 2.5.0 / 2.1.0 — 2026-04-27

Full cross-package release. New `openjobs inbox` command in the CLI;
`message.received` webhook now fires from **all three** message send paths
(job-thread, DM, and inbox-reply) with a `content` field added to the
payload; SDK packages bump to 2.1.0 to document the API behaviour change
(no breaking code changes in either SDK).

### `@openjobs/cli@2.5.0` — npm

- Page:    https://www.npmjs.com/package/@openjobs/cli/v/2.5.0
- Tarball: https://registry.npmjs.org/@openjobs/cli/-/cli-2.5.0.tgz
- shasum:  _(populated post-publish)_
- integrity: _(populated post-publish)_
- Uploaded: 2026-04-27T00:00:00Z
- Install: `npm install -g @openjobs/cli`  (or `npx @openjobs/cli --help`)
- Bin:     `openjobs`

### `@openjobs/sdk@2.1.0` — npm

- Page:    https://www.npmjs.com/package/@openjobs/sdk/v/2.1.0
- Tarball: https://registry.npmjs.org/@openjobs/sdk/-/sdk-2.1.0.tgz
- shasum:  _(populated post-publish)_
- integrity: _(populated post-publish)_
- Uploaded: 2026-04-27T00:00:00Z
- Install: `npm install @openjobs/sdk`

### `openjobs-py==2.1.0` — PyPI

- Page:    https://pypi.org/project/openjobs-py/2.1.0/
- Wheel:   `openjobs_py-2.1.0-py3-none-any.whl`
  sha256: _(populated post-publish)_
- Sdist:   `openjobs_py-2.1.0.tar.gz`
  sha256: _(populated post-publish)_
- Uploaded: 2026-04-27T00:00:00Z
- Install: `pip install openjobs-py==2.1.0`
