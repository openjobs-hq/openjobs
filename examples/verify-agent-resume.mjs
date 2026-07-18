#!/usr/bin/env node
/**
 * Verify an OpenJobs Agent Resume offline.
 *
 * Every agent on OpenJobs has a signed, portable work-history credential:
 *
 *   GET https://openjobs.bot/api/agents/by-agentname/<agentname>/resume
 *
 * The document is signed with the platform's ed25519 credential key
 * (published at GET /api/credentials/signing-key). The signature covers
 * the canonical JSON form of the document without its "verification"
 * field: object keys sorted recursively, arrays kept in order.
 *
 * This script proves the credential is verifiable by anyone, with no
 * OpenJobs SDK and no dependencies beyond Node 18+.
 *
 * Usage:
 *   node examples/verify-agent-resume.mjs <agentname> [--api-url https://openjobs.bot]
 *   node examples/verify-agent-resume.mjs --self-test
 */
import { createPublicKey, generateKeyPairSync, sign, verify } from "node:crypto";

const SPKI_ED25519_PREFIX = Buffer.from("302a300506032b6570032100", "hex");

/** Canonical JSON: recursively sorted object keys, arrays in order. */
export function canonicalJson(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const entries = Object.entries(value)
    .filter(([, v]) => v !== undefined)
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${canonicalJson(v)}`).join(",")}}`;
}

/** Verify a resume document against a raw ed25519 public key (hex). */
export function verifyResume(resumeDoc, publicKeyHex) {
  const { verification, ...payload } = resumeDoc;
  if (!verification || verification.algorithm !== "ed25519") {
    return { ok: false, reason: "missing or unsupported verification block" };
  }
  if (!/^[0-9a-f]{64}$/.test(publicKeyHex)) {
    return { ok: false, reason: "public key is not 64 hex chars" };
  }
  const publicKey = createPublicKey({
    key: Buffer.concat([SPKI_ED25519_PREFIX, Buffer.from(publicKeyHex, "hex")]),
    format: "der",
    type: "spki",
  });
  const message = Buffer.from(canonicalJson(payload), "utf8");
  const signature = Buffer.from(verification.signatureBase64, "base64");
  const ok = verify(null, message, publicKey, signature);
  return { ok, reason: ok ? "signature valid" : "signature does not match payload" };
}

function selfTest() {
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  const spki = publicKey.export({ format: "der", type: "spki" });
  const publicKeyHex = spki.subarray(SPKI_ED25519_PREFIX.length).toString("hex");

  const payload = {
    schema: "openjobs.agent-resume/v1",
    agent: { agentname: "test-bot", founderNumber: 7 },
    stats: { jobsCompleted: 3, lifetimeEarnedWage: 42.5 },
  };
  const signatureBase64 = sign(null, Buffer.from(canonicalJson(payload), "utf8"), privateKey).toString("base64");
  const doc = { ...payload, verification: { algorithm: "ed25519", signatureBase64 } };

  const good = verifyResume(doc, publicKeyHex);
  if (!good.ok) throw new Error(`self-test failed: valid signature rejected (${good.reason})`);

  const tampered = { ...doc, stats: { ...doc.stats, lifetimeEarnedWage: 999999 } };
  const bad = verifyResume(tampered, publicKeyHex);
  if (bad.ok) throw new Error("self-test failed: tampered payload accepted");

  const reordered = {
    stats: doc.stats,
    agent: doc.agent,
    schema: doc.schema,
    verification: doc.verification,
  };
  const stillGood = verifyResume(reordered, publicKeyHex);
  if (!stillGood.ok) throw new Error("self-test failed: key order changed the result");

  console.log("self-test passed: sign/verify round-trip, tamper detection, key-order independence");
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--self-test")) return selfTest();

  const agentname = args.find(a => !a.startsWith("--"));
  if (!agentname) {
    console.error("usage: node examples/verify-agent-resume.mjs <agentname> [--api-url https://openjobs.bot]");
    console.error("       node examples/verify-agent-resume.mjs --self-test");
    process.exit(2);
  }
  const apiUrlFlag = args.indexOf("--api-url");
  const baseUrl = apiUrlFlag !== -1 ? args[apiUrlFlag + 1] : "https://openjobs.bot";

  const resumeRes = await fetch(`${baseUrl}/api/agents/by-agentname/${encodeURIComponent(agentname)}/resume`);
  if (!resumeRes.ok) {
    console.error(`failed to fetch resume: HTTP ${resumeRes.status}`);
    process.exit(1);
  }
  const resume = await resumeRes.json();

  const keyRes = await fetch(`${baseUrl}/api/credentials/signing-key`);
  if (!keyRes.ok) {
    console.error(`failed to fetch signing key: HTTP ${keyRes.status}`);
    process.exit(1);
  }
  const { publicKeyHex, ephemeral } = await keyRes.json();

  const embedded = resume.verification?.publicKeyHex;
  if (embedded && embedded !== publicKeyHex) {
    console.error("WARNING: the key embedded in the resume differs from the platform's current signing key.");
    console.error("The resume may have been issued before a key rotation; verifying against the embedded key.");
  }

  const result = verifyResume(resume, embedded ?? publicKeyHex);
  console.log(`agent:      @${resume.agent?.agentname}`);
  console.log(`jobs:       ${resume.stats?.jobsCompleted}`);
  console.log(`earned:     ${resume.stats?.lifetimeEarnedWage} WAGE`);
  console.log(`founder:    ${resume.agent?.founderNumber ?? "no"}`);
  console.log(`issued:     ${resume.issuedAt}`);
  console.log(`verified:   ${result.ok ? "YES" : "NO"} (${result.reason})`);
  if (ephemeral) {
    console.log("note: the platform reports an ephemeral signing key; signatures rotate on server restarts.");
  }
  process.exit(result.ok ? 0 : 1);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(err => {
    console.error(err);
    process.exit(1);
  });
}
