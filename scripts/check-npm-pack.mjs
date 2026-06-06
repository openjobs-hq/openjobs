import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const npmCmd = process.platform === "win32" ? "npm.cmd" : "npm";
const npmCli = process.env.npm_execpath;
const tscScript = path.join(rootDir, "node_modules", "typescript", "bin", "tsc");

const packages = [
  {
    name: "@openjobs/sdk",
    workspace: "@openjobs/sdk",
    dir: "packages/sdk-js",
    requiredFiles: [
      "package.json",
      "README.md",
      "dist/index.cjs",
      "dist/index.mjs",
      "dist/index.d.ts",
      "src/index.ts",
    ],
  },
  {
    name: "@openjobs/cli",
    workspace: "@openjobs/cli",
    dir: "packages/cli",
    requiredFiles: [
      "package.json",
      "README.md",
      "dist/bin.cjs",
      "dist/bin.mjs",
      "dist/index.cjs",
      "dist/index.mjs",
      "dist/index.d.ts",
      "skill/SKILL.md",
      "skill/HEARTBEAT.md",
      "skill/INSTALL.md",
      "skill/references/COMMANDS.md",
      "skill/references/PROTOCOL.md",
      "skill/references/SKILL.md",
    ],
  },
  {
    name: "@openjobs/langchain",
    workspace: "@openjobs/langchain",
    dir: "packages/langchain-js",
    requiredFiles: [
      "package.json",
      "README.md",
      "dist/index.js",
      "dist/index.d.ts",
      "src/index.ts",
    ],
  },
];

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? rootDir,
    encoding: "utf8",
    shell: process.platform === "win32" && command.endsWith(".cmd"),
  });

  if (result.status !== 0) {
    const renderedCommand = `${command} ${args.join(" ")}`;
    const output = [result.stdout, result.stderr].filter(Boolean).join("\n");
    throw new Error(`${renderedCommand} failed\n${output}`);
  }

  return result.stdout;
}

function runNpm(args, options) {
  if (npmCli) {
    return run(process.execPath, [npmCli, ...args], options);
  }
  return run(npmCmd, args, options);
}

function remove(...segments) {
  fs.rmSync(path.join(...segments), { force: true, recursive: true });
}

function rename(pkgDir, from, to) {
  fs.renameSync(path.join(pkgDir, from), path.join(pkgDir, to));
}

function copy(pkgDir, from, to) {
  fs.copyFileSync(path.join(pkgDir, from), path.join(pkgDir, to));
}

function chmod(pkgDir, file, mode) {
  fs.chmodSync(path.join(pkgDir, file), mode);
}

function prepend(pkgDir, file, content) {
  const target = path.join(pkgDir, file);
  fs.writeFileSync(target, content + fs.readFileSync(target, "utf8"));
}

function replaceText(pkgDir, file, from, to) {
  const target = path.join(pkgDir, file);
  fs.writeFileSync(target, fs.readFileSync(target, "utf8").split(from).join(to));
}

function tsc(pkgDir, args = []) {
  run(process.execPath, [tscScript, ...args], { cwd: pkgDir });
}

function buildSdk() {
  const pkgDir = path.join(rootDir, "packages/sdk-js");
  remove(pkgDir, "dist");
  remove(pkgDir, "dist-cjs");
  remove(pkgDir, "docs");
  tsc(pkgDir, ["-p", "tsconfig.json"]);
  rename(pkgDir, "dist/index.js", "dist/index.mjs");
  tsc(pkgDir, ["-p", "tsconfig.cjs.json"]);
  rename(pkgDir, "dist-cjs/index.js", "dist/index.cjs");
  remove(pkgDir, "dist-cjs");
}

function buildCli() {
  const pkgDir = path.join(rootDir, "packages/cli");
  remove(pkgDir, "dist");
  remove(pkgDir, "dist-cjs");
  tsc(pkgDir, ["-p", "tsconfig.json"]);
  rename(pkgDir, "dist/index.js", "dist/index.mjs");
  rename(pkgDir, "dist/bin.js", "dist/bin.mjs");
  tsc(pkgDir, ["-p", "tsconfig.cjs.json"]);
  copy(pkgDir, "dist-cjs/index.js", "dist/index.cjs");
  copy(pkgDir, "dist-cjs/bin.js", "dist/bin.cjs");
  remove(pkgDir, "dist-cjs");
  replaceText(pkgDir, "dist/bin.cjs", JSON.stringify("./index.js"), JSON.stringify("./index.cjs"));
  replaceText(pkgDir, "dist/bin.mjs", JSON.stringify("./index.js"), JSON.stringify("./index.mjs"));
  prepend(pkgDir, "dist/bin.cjs", "#!/usr/bin/env node\n");
  chmod(pkgDir, "dist/bin.cjs", 0o755);
}

function buildLangChain() {
  const pkgDir = path.join(rootDir, "packages/langchain-js");
  remove(pkgDir, "dist");
  tsc(pkgDir);
}

function buildPackage(pkg) {
  if (pkg.workspace === "@openjobs/sdk") {
    buildSdk();
  } else if (pkg.workspace === "@openjobs/cli") {
    buildCli();
  } else if (pkg.workspace === "@openjobs/langchain") {
    buildLangChain();
  } else {
    throw new Error(`No build routine configured for ${pkg.workspace}`);
  }
}

function parsePackJson(output, pkg) {
  try {
    const parsed = JSON.parse(output);
    const packInfo = Array.isArray(parsed) ? parsed[0] : parsed;
    if (!packInfo?.files) {
      throw new Error("missing files array");
    }
    return packInfo.files.map((file) => file.path).sort();
  } catch (error) {
    throw new Error(`Unable to parse npm pack JSON for ${pkg.name}: ${error.message}\n${output}`);
  }
}

function verifyFiles(pkg, files) {
  const packed = new Set(files);
  const missing = pkg.requiredFiles.filter((file) => !packed.has(file));
  if (missing.length > 0) {
    throw new Error(
      `${pkg.name} npm pack output is missing required file(s): ${missing.join(", ")}`
    );
  }
}

for (const pkg of packages) {
  console.log(`Building ${pkg.name}...`);
  buildPackage(pkg);

  console.log(`Checking npm pack --dry-run for ${pkg.name}...`);
  const output = runNpm(["pack", "--dry-run", "--json"], {
    cwd: path.join(rootDir, pkg.dir),
  });
  const files = parsePackJson(output, pkg);
  verifyFiles(pkg, files);
  console.log(`OK ${pkg.name}: ${files.length} files would be packed.`);
}
