import { execFileSync } from "node:child_process";

const GENERATED_PATH_SEGMENTS = new Set([
  "dist",
  "build",
  "__pycache__",
  ".pytest_cache",
  ".ruff_cache",
]);

const GENERATED_FILE_NAMES = new Set([
  ".DS_Store",
]);

function gitLsFiles(args) {
  const output = execFileSync("git", ["ls-files", ...args], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  return output.split(/\r?\n/).filter(Boolean);
}

function normalizePath(filePath) {
  return filePath.replace(/\\/g, "/");
}

function isGeneratedArtifact(filePath) {
  const parts = normalizePath(filePath).split("/");
  return parts.some((part) => GENERATED_PATH_SEGMENTS.has(part))
    || GENERATED_FILE_NAMES.has(parts[parts.length - 1]);
}

function collectCandidateFiles() {
  const tracked = gitLsFiles(["--cached"]);
  const untracked = gitLsFiles(["--others", "--exclude-standard"]);
  const ignored = gitLsFiles(["--others", "--ignored", "--exclude-standard"]);
  return [...new Set([...tracked, ...untracked, ...ignored])].sort();
}

const offenders = collectCandidateFiles().filter(isGeneratedArtifact);

if (offenders.length > 0) {
  console.error("Generated artifacts were found in the repository:");
  for (const offender of offenders) {
    console.error(`- ${offender}`);
  }
  console.error("");
  console.error("Remove these files from the working tree or from git tracking,");
  console.error("then ensure the matching artifact pattern is covered by .gitignore.");
  process.exit(1);
}

console.log("No generated artifacts detected.");
