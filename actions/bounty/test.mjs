// Unit tests for the OpenJobs Bounty Bridge helpers.
// Run with: node actions/bounty/test.mjs
// No test framework required; failures throw via node:assert and exit non-zero.

import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const {
  parseBountyLabel,
  extractLinkedIssues,
  buildJobDescription,
  openjobsRequest,
  githubRequest,
} = require("./index.js");

let passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log(`ok - ${name}`);
}

// ---------------------------------------------------------------------------
// parseBountyLabel
// ---------------------------------------------------------------------------

test("parseBountyLabel parses a valid amount from prefix:amount", () => {
  assert.equal(parseBountyLabel("agent-bounty:25", "agent-bounty", 10), 25);
  assert.equal(parseBountyLabel("agent-bounty:2.5", "agent-bounty", 10), 2.5);
  assert.equal(parseBountyLabel("  agent-bounty:100  ", "agent-bounty", 10), 100);
});

test("parseBountyLabel returns the default reward for a bare prefix label", () => {
  assert.equal(parseBountyLabel("agent-bounty", "agent-bounty", 10), 10);
  assert.equal(parseBountyLabel("bounty", "bounty", 42), 42);
});

test("parseBountyLabel returns null for non-matching labels", () => {
  assert.equal(parseBountyLabel("bug", "agent-bounty", 10), null);
  assert.equal(parseBountyLabel("agent-bounty-high", "agent-bounty", 10), null);
  assert.equal(parseBountyLabel("Agent-Bounty:25", "agent-bounty", 10), null);
  assert.equal(parseBountyLabel("", "agent-bounty", 10), null);
  assert.equal(parseBountyLabel(undefined, "agent-bounty", 10), null);
});

test("parseBountyLabel falls back to the default reward on invalid amounts", () => {
  assert.equal(parseBountyLabel("agent-bounty:banana", "agent-bounty", 10), 10);
  assert.equal(parseBountyLabel("agent-bounty:-5", "agent-bounty", 10), 10);
  assert.equal(parseBountyLabel("agent-bounty:0", "agent-bounty", 10), 10);
  assert.equal(parseBountyLabel("agent-bounty:", "agent-bounty", 10), 10);
  assert.equal(parseBountyLabel("agent-bounty:Infinity", "agent-bounty", 10), 10);
});

// ---------------------------------------------------------------------------
// extractLinkedIssues
// ---------------------------------------------------------------------------

test("extractLinkedIssues finds a closing keyword reference", () => {
  assert.deepEqual(extractLinkedIssues("", "This closes #12 for good."), [12]);
});

test("extractLinkedIssues finds keyword variants and bare references together", () => {
  assert.deepEqual(extractLinkedIssues("", "Fixes #3 and #4"), [3, 4]);
  assert.deepEqual(extractLinkedIssues("", "Resolved #9. Fixed #8. close #7"), [9, 8, 7]);
});

test("extractLinkedIssues honors closing keywords in the title", () => {
  assert.deepEqual(extractLinkedIssues("Fix #21: flaky test", ""), [21]);
});

test("extractLinkedIssues falls back to bare #N references in the body", () => {
  assert.deepEqual(extractLinkedIssues("Improve docs", "Related to #7"), [7]);
});

test("extractLinkedIssues deduplicates repeated references", () => {
  assert.deepEqual(extractLinkedIssues("Fixes #5", "closes #5, see #5 and #5 again"), [5]);
});

test("extractLinkedIssues returns an empty list when nothing is referenced", () => {
  assert.deepEqual(extractLinkedIssues("Tidy up", "No linked issues here."), []);
  assert.deepEqual(extractLinkedIssues(null, undefined), []);
});

// ---------------------------------------------------------------------------
// buildJobDescription
// ---------------------------------------------------------------------------

test("buildJobDescription keeps short bodies intact and appends the footer", () => {
  const url = "https://github.com/octo/repo/issues/1";
  const output = buildJobDescription("Fix the flaky login test.", url);
  assert.ok(output.startsWith("Fix the flaky login test."));
  assert.ok(output.includes(`Source issue: ${url}`));
  assert.ok(output.includes("Submissions must reference this GitHub issue"));
  assert.ok(!output.includes("Description truncated"));
});

test("buildJobDescription truncates long bodies to the limit", () => {
  const url = "https://github.com/octo/repo/issues/2";
  const longBody = "x".repeat(5000);
  const output = buildJobDescription(longBody, url);
  assert.ok(output.startsWith("x".repeat(4000)));
  assert.ok(!output.includes("x".repeat(4001)));
  assert.ok(output.includes("Description truncated"));
  assert.ok(output.includes(`Source issue: ${url}`));
});

test("buildJobDescription respects a custom max length", () => {
  const output = buildJobDescription("abcdefghij", "https://example.com/i/3", 5);
  assert.ok(output.startsWith("abcde\n"));
  assert.ok(!output.startsWith("abcdef"));
  assert.ok(output.includes("Description truncated"));
});

test("buildJobDescription substitutes a placeholder for empty bodies", () => {
  const output = buildJobDescription("", "https://example.com/i/4");
  assert.ok(output.startsWith("(No issue description was provided.)"));
  const nullOutput = buildJobDescription(null, "https://example.com/i/4");
  assert.ok(nullOutput.startsWith("(No issue description was provided.)"));
});

// ---------------------------------------------------------------------------
// request helpers are exported and callable
// ---------------------------------------------------------------------------

test("request helpers are exported as functions", () => {
  assert.equal(typeof openjobsRequest, "function");
  assert.equal(typeof githubRequest, "function");
});

console.log(`\nAll ${passed} tests passed.`);
