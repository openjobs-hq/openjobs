import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const npmCmd = process.platform === "win32" ? "npm.cmd" : "npm";
const npmCli = process.env.npm_execpath;
const cliBin = path.join(rootDir, "packages", "cli", "dist", "bin.cjs");
const cliPackageJson = JSON.parse(
  fs.readFileSync(path.join(rootDir, "packages", "cli", "package.json"), "utf8"),
);

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? rootDir,
    encoding: "utf8",
    env: options.env ?? process.env,
    shell: process.platform === "win32" && command.endsWith(".cmd"),
  });

  if (result.status !== 0) {
    const renderedCommand = `${command} ${args.join(" ")}`;
    const output = [result.stdout, result.stderr].filter(Boolean).join("\n");
    throw new Error(`${renderedCommand} failed with exit ${result.status}\n${output}`);
  }

  return result;
}

function runNpm(args, options) {
  if (npmCli) {
    return run(process.execPath, [npmCli, ...args], options);
  }
  return run(npmCmd, args, options);
}

function assertIncludes(text, expected, label) {
  if (!text.includes(expected)) {
    throw new Error(`${label} did not include ${JSON.stringify(expected)}\n${text}`);
  }
}

function runCli(args, options = {}) {
  return run(process.execPath, [cliBin, ...args], options);
}

console.log("Building @openjobs/cli...");
runNpm(["--workspace", "@openjobs/cli", "run", "build"]);

if (!fs.existsSync(cliBin)) {
  throw new Error(`Expected built CLI binary at ${cliBin}`);
}

const tempHome = fs.mkdtempSync(path.join(os.tmpdir(), "openjobs-cli-smoke-"));
const smokeEnv = {
  ...process.env,
  HOME: tempHome,
  USERPROFILE: tempHome,
  OPENJOBS_API_KEY: "",
  OPENJOBS_AGENT: "",
};

try {
  console.log("Checking openjobs --help...");
  const help = runCli(["--help"], { env: smokeEnv });
  assertIncludes(help.stdout, "openjobs", "--help output");
  assertIncludes(help.stdout, "COMMANDS", "--help output");

  console.log("Checking openjobs --version...");
  const version = runCli(["--version"], { env: smokeEnv });
  assertIncludes(version.stdout, `@openjobs/cli ${cliPackageJson.version}`, "--version output");

  console.log("Checking openjobs agents list-local --json...");
  const localAgents = runCli(["agents", "list-local", "--json"], { env: smokeEnv });
  const parsed = JSON.parse(localAgents.stdout);
  if (!Array.isArray(parsed.agents)) {
    throw new Error(`agents list-local --json did not return an agents array\n${localAgents.stdout}`);
  }
  if (parsed.agents.length !== 0) {
    throw new Error(`temporary HOME should not contain local agents\n${localAgents.stdout}`);
  }

  console.log("OK CLI smoke tests passed.");
} finally {
  fs.rmSync(tempHome, { recursive: true, force: true });
}
