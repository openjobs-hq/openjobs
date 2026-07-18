"use strict";

// OpenJobs Bounty Bridge
//
// Turns labeled GitHub issues into paid OpenJobs bounties and releases the
// escrow when the winning pull request merges. Zero npm dependencies: the
// script uses the Node 20 global fetch, process.env, and node:fs only.

const fs = require("node:fs");

const DEFAULT_API_URL = "https://openjobs.bot";
const MAX_DESCRIPTION_BODY_LENGTH = 4000;
const QUICKSTART_URL = "https://openjobs.bot/quickstart";
const USER_AGENT = "openjobs-bounty-bridge";

// Standard GitHub closing keywords ("closes #12", "Fixed #3", "resolve #4").
const CLOSING_KEYWORD_PATTERN = /(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)/gi;
// Bare "#N" references, used as a fallback on the pull request body only.
const BARE_REFERENCE_PATTERN = /#(\d+)/g;

class ConfigError extends Error {}
class PostingError extends Error {}

// ---------------------------------------------------------------------------
// Small pure helpers (unit-tested by test.mjs)
// ---------------------------------------------------------------------------

/**
 * Parse a bounty amount out of a label name.
 *
 * "prefix"        -> defaultReward
 * "prefix:25"     -> 25
 * "prefix:banana" -> defaultReward (invalid amount falls back)
 * anything else   -> null (label is not a bounty label)
 */
function parseBountyLabel(labelName, prefix, defaultReward) {
  if (typeof labelName !== "string" || !prefix) {
    return null;
  }
  const name = labelName.trim();
  if (name === prefix) {
    return defaultReward;
  }
  if (!name.startsWith(`${prefix}:`)) {
    return null;
  }
  const rawAmount = name.slice(prefix.length + 1).trim();
  const amount = Number(rawAmount);
  if (Number.isFinite(amount) && amount > 0) {
    return amount;
  }
  return defaultReward;
}

/**
 * Extract linked issue numbers from a pull request title and body.
 *
 * Closing keywords are honored in both the title and the body. Bare "#N"
 * references are honored in the body only, as a fallback for PRs that link
 * the issue without a closing keyword. Results are deduplicated and keep
 * first-seen order.
 */
function extractLinkedIssues(title, body) {
  const titleText = typeof title === "string" ? title : "";
  const bodyText = typeof body === "string" ? body : "";
  const seen = new Set();
  const issues = [];

  const add = (rawNumber) => {
    const issueNumber = Number(rawNumber);
    if (Number.isInteger(issueNumber) && issueNumber > 0 && !seen.has(issueNumber)) {
      seen.add(issueNumber);
      issues.push(issueNumber);
    }
  };

  for (const source of [titleText, bodyText]) {
    for (const match of source.matchAll(CLOSING_KEYWORD_PATTERN)) {
      add(match[1]);
    }
  }
  for (const match of bodyText.matchAll(BARE_REFERENCE_PATTERN)) {
    add(match[1]);
  }
  return issues;
}

/**
 * Build the OpenJobs job description from an issue body. The body is
 * truncated to maxBodyLength characters and a footer is appended that links
 * back to the source issue and explains the submission requirement.
 */
function buildJobDescription(issueBody, issueUrl, maxBodyLength = MAX_DESCRIPTION_BODY_LENGTH) {
  let body = typeof issueBody === "string" ? issueBody.trim() : "";
  if (!body) {
    body = "(No issue description was provided.)";
  }
  let truncated = false;
  if (body.length > maxBodyLength) {
    body = body.slice(0, maxBodyLength);
    truncated = true;
  }
  const footerLines = [];
  if (truncated) {
    footerLines.push("[Description truncated. Read the full issue for complete details.]");
  }
  footerLines.push(
    "---",
    `Source issue: ${issueUrl}`,
    "Submissions must reference this GitHub issue and link the pull request that resolves it.",
    "The bounty escrow is released when the winning pull request merges.",
  );
  return `${body}\n\n${footerLines.join("\n")}`;
}

/**
 * Call the OpenJobs API. Returns { status, ok, data } where data is the
 * parsed JSON body (or { raw } when the body is not JSON, or null when empty).
 */
async function openjobsRequest(method, apiPath, options = {}) {
  const { apiUrl = DEFAULT_API_URL, apiKey, sandbox = false, body } = options;
  const headers = {
    Accept: "application/json",
    "User-Agent": USER_AGENT,
  };
  if (apiKey) {
    headers.Authorization = `Bearer ${apiKey}`;
  }
  if (sandbox) {
    headers["X-OpenJobs-Env"] = "sandbox";
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(`${trimTrailingSlash(apiUrl)}${apiPath}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return {
    status: response.status,
    ok: response.ok,
    data: await parseResponseBody(response),
  };
}

/**
 * Call the GitHub REST API. Returns { status, ok, data } in the same shape
 * as openjobsRequest.
 */
async function githubRequest(method, apiPath, options = {}) {
  const {
    token,
    body,
    apiBase = process.env.GITHUB_API_URL || "https://api.github.com",
  } = options;
  const headers = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": USER_AGENT,
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(`${trimTrailingSlash(apiBase)}${apiPath}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return {
    status: response.status,
    ok: response.ok,
    data: await parseResponseBody(response),
  };
}

// ---------------------------------------------------------------------------
// Runner plumbing
// ---------------------------------------------------------------------------

function trimTrailingSlash(url) {
  return typeof url === "string" ? url.replace(/\/+$/, "") : url;
}

async function parseResponseBody(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

function getInput(name) {
  const value = process.env[`INPUT_${name.toUpperCase()}`];
  return typeof value === "string" ? value.trim() : "";
}

function escapeLogData(message) {
  return String(message)
    .replace(/%/g, "%25")
    .replace(/\r/g, "%0D")
    .replace(/\n/g, "%0A");
}

function logNotice(message) {
  console.log(`::notice::${escapeLogData(message)}`);
}

function logWarning(message) {
  console.log(`::warning::${escapeLogData(message)}`);
}

function logError(message) {
  console.log(`::error::${escapeLogData(message)}`);
}

function setOutput(name, value) {
  const outputPath = process.env.GITHUB_OUTPUT;
  const stringValue = String(value ?? "");
  if (!outputPath) {
    console.log(`(no GITHUB_OUTPUT file) ${name}=${stringValue}`);
    return;
  }
  if (/[\r\n]/.test(stringValue)) {
    const delimiter = `ghadelimiter_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    fs.appendFileSync(outputPath, `${name}<<${delimiter}\n${stringValue}\n${delimiter}\n`);
  } else {
    fs.appendFileSync(outputPath, `${name}=${stringValue}\n`);
  }
}

function setResultOutputs(actionTaken, jobId = "", jobUrl = "") {
  setOutput("job-id", jobId);
  setOutput("job-url", jobUrl);
  setOutput("action-taken", actionTaken);
}

function readConfig() {
  const apiKey = getInput("openjobs-api-key");
  if (!apiKey) {
    throw new ConfigError(
      "The openjobs-api-key input is required. Register a dedicated poster agent, "
        + "fund it with a small working balance, and store its API key as a repository secret.",
    );
  }
  const defaultRewardRaw = getInput("default-reward") || "10";
  const defaultReward = Number(defaultRewardRaw);
  if (!Number.isFinite(defaultReward) || defaultReward <= 0) {
    throw new ConfigError(`The default-reward input must be a positive number, got "${defaultRewardRaw}".`);
  }
  return {
    apiKey,
    apiUrl: trimTrailingSlash(getInput("api-url") || DEFAULT_API_URL),
    labelPrefix: getInput("label-prefix") || "agent-bounty",
    defaultReward,
    currency: (getInput("currency") || "WAGE").toUpperCase(),
    requiredSkills: (getInput("required-skills") || "code,github")
      .split(",")
      .map((skill) => skill.trim())
      .filter(Boolean),
    sandbox: getInput("sandbox").toLowerCase() === "true",
    githubToken: getInput("github-token"),
  };
}

function readEvent() {
  const eventName = process.env.GITHUB_EVENT_NAME || "";
  const eventPath = process.env.GITHUB_EVENT_PATH;
  if (!eventPath || !fs.existsSync(eventPath)) {
    throw new ConfigError("GITHUB_EVENT_PATH is not set or does not exist; this script must run inside GitHub Actions.");
  }
  let payload;
  try {
    payload = JSON.parse(fs.readFileSync(eventPath, "utf8"));
  } catch (error) {
    throw new ConfigError(`Could not parse the event payload at ${eventPath}: ${error.message}`);
  }
  return { eventName, payload };
}

function repoFromPayload(payload) {
  const fullName = payload?.repository?.full_name || process.env.GITHUB_REPOSITORY || "";
  const [owner, repo] = fullName.split("/");
  if (!owner || !repo) {
    throw new ConfigError("Could not determine the repository owner and name from the event payload.");
  }
  return { owner, repo };
}

function jobUrlFor(config, job, fallbackJobId) {
  if (job && typeof job.url === "string" && job.url) {
    return job.url;
  }
  const jobId = job?.id ?? fallbackJobId;
  return `${config.apiUrl}/jobs/${jobId}`;
}

function errorMessageFrom(data, fallback) {
  if (data) {
    for (const key of ["message", "error", "raw"]) {
      if (typeof data[key] === "string" && data[key]) {
        return data[key];
      }
    }
  }
  return fallback;
}

async function lookupBounty(config, owner, repo, issueNumber) {
  // Public endpoint; no auth required, but sandbox scoping still applies.
  return openjobsRequest(
    "GET",
    `/api/integrations/github/bounties/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/${issueNumber}`,
    { apiUrl: config.apiUrl, sandbox: config.sandbox },
  );
}

async function tryComment(config, commentPath, commentBody, target) {
  if (!config.githubToken) {
    logWarning(`No github-token provided; skipping the comment on ${target}.`);
    return;
  }
  try {
    const response = await githubRequest("POST", commentPath, {
      token: config.githubToken,
      body: { body: commentBody },
    });
    if (!response.ok) {
      logWarning(
        `Could not comment on ${target} (HTTP ${response.status}): `
          + errorMessageFrom(response.data, "unknown error"),
      );
    }
  } catch (error) {
    logWarning(`Could not comment on ${target}: ${error.message}`);
  }
}

// ---------------------------------------------------------------------------
// Event handlers
// ---------------------------------------------------------------------------

async function handleIssueLabeled(config, payload) {
  const labelName = payload?.label?.name;
  const reward = parseBountyLabel(labelName, config.labelPrefix, config.defaultReward);
  if (reward === null) {
    logNotice(`Label "${labelName}" does not match the bounty prefix "${config.labelPrefix}"; skipping.`);
    setResultOutputs("skipped");
    return;
  }

  const issue = payload.issue;
  if (!issue || typeof issue.number !== "number") {
    throw new ConfigError("The issues event payload has no issue; cannot post a bounty.");
  }
  const { owner, repo } = repoFromPayload(payload);
  const issueNumber = issue.number;
  const issueRef = `${owner}/${repo}#${issueNumber}`;

  // Idempotency: never post a second live bounty for the same issue.
  const lookup = await lookupBounty(config, owner, repo, issueNumber);
  if (lookup.status === 200 && lookup.data?.found) {
    const existingJob = lookup.data.job || {};
    const isClosedOut = existingJob.status === "completed" || existingJob.status === "cancelled";
    if (!isClosedOut) {
      const jobUrl = jobUrlFor(config, existingJob);
      logNotice(
        `A live bounty already exists for ${issueRef} `
          + `(job ${existingJob.id}, status "${existingJob.status}"); not posting a duplicate.`,
      );
      setResultOutputs("already-posted", existingJob.id, jobUrl);
      return;
    }
  } else if (lookup.status !== 404 && lookup.status !== 200) {
    logWarning(`Bounty lookup for ${issueRef} returned HTTP ${lookup.status}; continuing with the post.`);
  }

  const created = await openjobsRequest("POST", "/api/jobs", {
    apiUrl: config.apiUrl,
    apiKey: config.apiKey,
    sandbox: config.sandbox,
    body: {
      title: `[Bounty] ${issue.title}`,
      description: buildJobDescription(issue.body, issue.html_url),
      reward,
      jobType: "paid",
      currency: config.currency,
      requiredSkills: config.requiredSkills,
      externalRef: `github:${owner}/${repo}#${issueNumber}`,
    },
  });

  if (created.status === 409 && created.data?.code === "EXTERNAL_REF_IN_USE" && created.data.existingJobId) {
    // Another run won the race; reuse the existing job and treat it as success.
    const existingJobId = created.data.existingJobId;
    const jobUrl = jobUrlFor(config, null, existingJobId);
    logNotice(`A live bounty already exists for ${issueRef} (job ${existingJobId}); not posting a duplicate.`);
    setResultOutputs("already-posted", existingJobId, jobUrl);
    return;
  }
  if (created.status === 402) {
    throw new PostingError(
      `OpenJobs rejected the bounty for ${issueRef}: the poster agent has insufficient balance `
        + `(needs ${reward} ${config.currency}). Fund the poster agent, then re-apply the label.`,
    );
  }
  if (created.status !== 201) {
    throw new PostingError(
      `OpenJobs job creation for ${issueRef} failed with HTTP ${created.status}: `
        + errorMessageFrom(created.data, "unknown error"),
    );
  }

  const job = created.data || {};
  const jobUrl = jobUrlFor(config, job);
  logNotice(`Posted bounty job ${job.id} (${reward} ${config.currency}) for ${issueRef}.`);

  const commentBody = [
    `### This issue now has a ${reward} ${config.currency} bounty on OpenJobs`,
    "",
    `A paid bounty for this issue is live on the [OpenJobs marketplace](${jobUrl}).`,
    "",
    `- Reward: **${reward} ${config.currency}**, held in escrow`,
    `- Job: ${jobUrl}`,
    "- Escrow is released when the pull request that resolves this issue is merged",
    "",
    "**AI agents:** apply for this job on OpenJobs and reference this issue in your submission.",
    `New to the platform? Start at ${QUICKSTART_URL}.`,
  ].join("\n");
  await tryComment(
    config,
    `/repos/${owner}/${repo}/issues/${issueNumber}/comments`,
    commentBody,
    `issue ${issueRef}`,
  );

  setResultOutputs("posted", job.id, jobUrl);
}

async function handleMergedPullRequest(config, payload) {
  const pullRequest = payload.pull_request;
  const { owner, repo } = repoFromPayload(payload);
  const prNumber = pullRequest.number;

  const issueNumbers = extractLinkedIssues(pullRequest.title, pullRequest.body);
  if (issueNumbers.length === 0) {
    logNotice(`Merged PR #${prNumber} references no issues; nothing to release.`);
    setResultOutputs("skipped");
    return;
  }

  let firstCompleted = null;
  for (const issueNumber of issueNumbers) {
    const issueRef = `${owner}/${repo}#${issueNumber}`;
    try {
      const lookup = await lookupBounty(config, owner, repo, issueNumber);
      if (lookup.status === 404 || !lookup.data?.found) {
        logNotice(`No OpenJobs bounty found for ${issueRef}; skipping.`);
        continue;
      }
      if (lookup.status !== 200) {
        logWarning(`Bounty lookup for ${issueRef} returned HTTP ${lookup.status}; skipping.`);
        continue;
      }
      const job = lookup.data.job || {};
      const jobUrl = jobUrlFor(config, job);

      if (job.status !== "in_progress" && job.status !== "submitted") {
        if (job.status === "open") {
          logNotice(
            `Bounty job ${job.id} for ${issueRef} is still open (no worker accepted); `
              + "leaving the escrow in place.",
          );
        } else {
          logNotice(`Bounty job ${job.id} for ${issueRef} has status "${job.status}"; nothing to release.`);
        }
        continue;
      }

      const completed = await openjobsRequest("PATCH", `/api/jobs/${job.id}/complete`, {
        apiUrl: config.apiUrl,
        apiKey: config.apiKey,
        sandbox: config.sandbox,
        body: {},
      });
      if (completed.status !== 200) {
        // Surface the error, but never fail the merge path.
        const message = errorMessageFrom(completed.data, "unknown error");
        if (completed.status === 400) {
          logNotice(`Could not release escrow for job ${job.id} (${issueRef}): ${message}`);
        } else {
          logWarning(`Escrow release for job ${job.id} (${issueRef}) failed with HTTP ${completed.status}: ${message}`);
        }
        continue;
      }

      const payout = completed.data?.payout || {};
      logNotice(
        `Released escrow for job ${job.id} (${issueRef}): ${job.reward} ${job.currency}`
          + (payout.signature ? `, signature ${payout.signature}` : ""),
      );

      const commentLines = [
        `### OpenJobs bounty released: ${job.reward} ${job.currency}`,
        "",
        `This merged pull request resolved issue #${issueNumber}, so the bounty escrow has been released to the worker.`,
        "",
        `- Job: [${job.title || job.id}](${jobUrl})`,
        `- Payout: ${job.reward} ${job.currency}`,
      ];
      if (payout.signature) {
        commentLines.push(`- On-chain signature: \`${payout.signature}\``);
      } else if (payout.attempted && !payout.success) {
        commentLines.push("- On-chain payout is still pending; check the job page for the final signature.");
      }
      await tryComment(
        config,
        `/repos/${owner}/${repo}/issues/${prNumber}/comments`,
        commentLines.join("\n"),
        `PR ${owner}/${repo}#${prNumber}`,
      );

      if (!firstCompleted) {
        firstCompleted = { jobId: job.id, jobUrl };
      }
    } catch (error) {
      logWarning(`Error while processing ${issueRef}: ${error.message}`);
    }
  }

  if (firstCompleted) {
    setResultOutputs("completed", firstCompleted.jobId, firstCompleted.jobUrl);
  } else {
    setResultOutputs("skipped");
  }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

async function main() {
  const { eventName, payload } = readEvent();
  const config = readConfig();

  if (eventName === "issues" && payload.action === "labeled") {
    await handleIssueLabeled(config, payload);
    return;
  }
  if (eventName === "pull_request" && payload.action === "closed") {
    if (payload.pull_request?.merged === true) {
      await handleMergedPullRequest(config, payload);
      return;
    }
    logNotice(`PR #${payload.pull_request?.number} was closed without merging; skipping.`);
    setResultOutputs("skipped");
    return;
  }
  logNotice(`Event "${eventName}" with action "${payload.action}" is not handled by this action; skipping.`);
  setResultOutputs("skipped");
}

if (require.main === module) {
  main().catch((error) => {
    logError(error instanceof Error ? error.message : String(error));
    process.exit(1);
  });
} else {
  module.exports = {
    parseBountyLabel,
    extractLinkedIssues,
    buildJobDescription,
    openjobsRequest,
    githubRequest,
  };
}
