import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Regenerate the CLI's bundled skill from the single source of truth.
//
// `skills/openjobs/` is the ONLY tracked copy of the OpenJobs skill bundle.
// The published `@openjobs/cli` package must physically ship the bundle (its
// `install-skill` command copies it out of the installed package — it can't
// reach back into this repo), so we generate `packages/cli/skill/` from
// `skills/openjobs/` at packaging time. `packages/cli/skill/` is a build
// artifact (gitignored), never committed, so the two can't drift.
//
// Invoked by `@openjobs/cli`'s `prepack` (runs on `npm pack` / `npm publish`,
// which is what `check:npm-pack` and `release.sh` use) and by its `build`.
// The whole tree is copied recursively — SKILL.md, HEARTBEAT.md, INSTALL.md,
// references/, scripts/, and anything added later.

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcDir = path.join(rootDir, "skills", "openjobs");
const destDir = path.join(rootDir, "packages", "cli", "skill");

if (!fs.existsSync(path.join(srcDir, "SKILL.md"))) {
  console.error(
    `❌ sync-cli-skill: source bundle not found at ${srcDir} (no SKILL.md).\n` +
      "   The CLI skill is sourced from skills/openjobs/ — that directory must exist.",
  );
  process.exit(1);
}

// Wipe first so files removed from the source don't linger in the bundle.
fs.rmSync(destDir, { recursive: true, force: true });
fs.mkdirSync(destDir, { recursive: true });
fs.cpSync(srcDir, destDir, { recursive: true });

if (!fs.existsSync(path.join(destDir, "SKILL.md"))) {
  console.error(`❌ sync-cli-skill: copy did not produce ${path.join(destDir, "SKILL.md")}.`);
  process.exit(1);
}

const count = (function walk(dir) {
  let n = 0;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    n += entry.isDirectory() ? walk(path.join(dir, entry.name)) : 1;
  }
  return n;
})(destDir);

// Log to stderr: this runs as the CLI's `prepack`, and `npm pack --json`
// emits machine-readable JSON on stdout (check:npm-pack parses it). Anything
// this script writes to stdout would corrupt that JSON.
process.stderr.write(`sync-cli-skill: skills/openjobs → packages/cli/skill (${count} files)\n`);
