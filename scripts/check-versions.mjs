import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const errors = [];

const jsPackages = [
  { label: "@openjobs/sdk", file: "packages/sdk-js/package.json" },
  { label: "@openjobs/cli", file: "packages/cli/package.json" },
  { label: "@openjobs/langchain", file: "packages/langchain-js/package.json" },
];

const pyPackages = [
  { label: "openjobs-py", file: "packages/sdk-python/pyproject.toml", init: "packages/sdk-python/openjobs/__init__.py" },
  { label: "openjobs-langchain", file: "packages/openjobs-langchain/pyproject.toml", init: "packages/openjobs-langchain/openjobs_langchain/__init__.py" },
  { label: "openjobs-crewai", file: "packages/openjobs-crewai/pyproject.toml", init: "packages/openjobs-crewai/openjobs_crewai/__init__.py" },
  { label: "openjobs-openai", file: "packages/openjobs-openai/pyproject.toml", init: "packages/openjobs-openai/openjobs_openai/__init__.py" },
];

const changelogs = [
  ["@openjobs/sdk", "packages/sdk-js/CHANGELOG.md"],
  ["@openjobs/cli", "packages/cli/CHANGELOG.md"],
  ["@openjobs/langchain", "packages/langchain-js/CHANGELOG.md"],
  ["openjobs-py", "packages/sdk-python/CHANGELOG.md"],
  ["openjobs-langchain", "packages/openjobs-langchain/CHANGELOG.md"],
  ["openjobs-crewai", "packages/openjobs-crewai/CHANGELOG.md"],
  ["openjobs-openai", "packages/openjobs-openai/CHANGELOG.md"],
];

function read(rel) {
  return fs.readFileSync(path.join(root, rel), "utf8");
}

function readJson(rel) {
  return JSON.parse(read(rel));
}

function extractTomlString(source, key, rel) {
  const match = source.match(new RegExp(`^${key}\\s*=\\s*"([^"]+)"`, "m"));
  if (!match) fail(rel, `missing ${key} = "..."`);
  return match?.[1];
}

function extractInitVersion(rel) {
  const match = read(rel).match(/^__version__\s*=\s*"([^"]+)"/m);
  if (!match) fail(rel, "missing __version__ string");
  return match?.[1];
}

function fail(location, message) {
  errors.push(`${location}: ${message}`);
}

function expectEqual(location, actual, expected, label) {
  if (actual !== expected) {
    fail(location, `${label} is ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
  }
}

function expectMatch(location, source, pattern, label) {
  if (!pattern.test(source)) {
    fail(location, `missing ${label}`);
  }
}

const versions = new Map();
for (const pkg of jsPackages) {
  const json = readJson(pkg.file);
  versions.set(pkg.label, json.version);
}

for (const pkg of pyPackages) {
  const pyproject = read(pkg.file);
  const version = extractTomlString(pyproject, "version", pkg.file);
  versions.set(pkg.label, version);
  expectEqual(pkg.init, extractInitVersion(pkg.init), version, "__version__");
}

const canonicalVersion = versions.get("@openjobs/sdk");
for (const [label, version] of versions) {
  expectEqual(label, version, canonicalVersion, "package version");
}

const nextMajor = `${Number(canonicalVersion.split(".")[0]) + 1}.0.0`;
const expectedRange = `>=${canonicalVersion},<${nextMajor}`;
const expectedNpmRange = `>=${canonicalVersion} <${nextMajor}`;

const langchainJs = readJson("packages/langchain-js/package.json");
expectEqual(
  "packages/langchain-js/package.json",
  langchainJs.peerDependencies?.["@openjobs/sdk"],
  expectedNpmRange,
  "@openjobs/sdk peer range",
);

for (const rel of [
  "packages/openjobs-langchain/pyproject.toml",
  "packages/openjobs-crewai/pyproject.toml",
  "packages/openjobs-openai/pyproject.toml",
]) {
  const source = read(rel);
  expectMatch(rel, source, new RegExp(`openjobs-py>=${escapeRegExp(canonicalVersion)},<${escapeRegExp(nextMajor)}`), "openjobs-py dependency range");
}

for (const rel of [
  "packages/openjobs-crewai/pyproject.toml",
  "packages/openjobs-openai/pyproject.toml",
]) {
  const source = read(rel);
  expectMatch(rel, source, new RegExp(`openjobs-langchain>=${escapeRegExp(canonicalVersion)},<${escapeRegExp(nextMajor)}`), "openjobs-langchain dependency range");
}

const cliSource = read("packages/cli/src/index.ts");
expectMatch("packages/cli/src/index.ts", cliSource, new RegExp(`CLI_VERSION\\s*=\\s*"${escapeRegExp(canonicalVersion)}"`), "CLI_VERSION matching package version");

const sdkTsSource = read("packages/sdk-js/src/index.ts");
expectMatch("packages/sdk-js/src/index.ts", sdkTsSource, new RegExp(`openjobs-sdk-ts/${escapeRegExp(canonicalVersion)}`, "g"), "TypeScript SDK User-Agent version");

const sdkPySource = read("packages/sdk-python/openjobs/client.py");
expectMatch("packages/sdk-python/openjobs/client.py", sdkPySource, new RegExp(`openjobs-sdk-python/${escapeRegExp(canonicalVersion)}`), "Python SDK User-Agent version");

for (const [label, rel] of changelogs) {
  const version = versions.get(label);
  expectMatch(rel, read(rel), new RegExp(`^## \\[${escapeRegExp(version)}\\]`, "m"), `CHANGELOG entry for ${version}`);
}

const lock = readJson("package-lock.json");
for (const pkg of jsPackages.slice(0, 3)) {
  const lockEntry = lock.packages?.[pkg.file.replace(/\/package\.json$/, "").replace(/\\/g, "/")];
  if (lockEntry?.version) {
    expectEqual("package-lock.json", lockEntry.version, versions.get(pkg.label), `${pkg.label} lockfile version`);
  }
}

if (errors.length > 0) {
  console.error("Version consistency check failed:");
  for (const error of errors) console.error(`- ${error}`);
  console.error("\nFix: run packages/release.sh for coordinated releases, or update every listed manifest, dependency range, user-agent, and changelog entry together.");
  process.exit(1);
}

console.log(`Version consistency check passed for OpenJobs ${canonicalVersion}.`);

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
