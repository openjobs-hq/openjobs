# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately via GitHub's
[private vulnerability reporting](https://github.com/openjobs-hq/openjobs/security/advisories/new)
for this repository. Do not open a public issue for security reports.
You should receive a response within a few days.

## Release and publish ownership

Publishing the OpenJobs packages to npm and PyPI is restricted to the
release owner, [@cchacons](https://github.com/cchacons). The controls
that enforce this (workflow actor guard, protected `release`
environment, code-owner review) are documented in
[`packages/RELEASES.md`](./packages/RELEASES.md). The publish tokens
are held only by the release owner and are never committed to this
repository.

## How pull requests are qualified

Every pull request must pass these automated checks before merge, in
addition to code-owner review by the release owner:

| Check | Workflow | What it catches |
| --- | --- | --- |
| CI (build, typecheck, lint, tests, packaging) | `ci.yml` | Broken or misbehaving code, version drift, stray generated artifacts |
| Secret scanning (TruffleHog) | `secret-scanning.yml` | Committed credentials and tokens |
| CodeQL (JS/TS + Python, security-extended) | `codeql.yml` | Injectable, unsafe, or malicious code patterns |
| Dependency review | `pr-security.yml` | Newly introduced dependencies with known advisories or malware flags |
| Workflow audit (zizmor) | `pr-security.yml` | GitHub Actions tampering: template injection, dangerous triggers, unpinned actions |
| npm signatures and provenance | `pr-security.yml` | Registry artifacts that fail signature or provenance verification |

Supporting conventions:

- All GitHub Actions are pinned to full commit SHAs, so a compromised
  or re-published action tag cannot inject code into CI or releases.
- Dependencies install from committed lockfiles (`npm ci`), and
  Dependabot proposes updates as reviewable pull requests.
- Workflows run with least-privilege `GITHUB_TOKEN` permissions
  (`contents: read` by default).

Automated scanning reduces risk but cannot certify intent; the final
gate for every change is human review by the code owner, which branch
protection makes mandatory.
