import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const configPath = path.join(rootDir, "markdown-links.config.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
const ignoreUrlPatterns = (config.ignoreUrlPatterns ?? []).map((pattern) => new RegExp(pattern, "i"));

function gitLsFiles(args) {
  const output = execFileSync("git", ["ls-files", ...args], {
    cwd: rootDir,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  return output.split(/\r?\n/).filter(Boolean);
}

function normalizePath(filePath) {
  return filePath.replace(/\\/g, "/");
}

function isTargetMarkdown(filePath) {
  const normalized = normalizePath(filePath);
  return /^[^/]+\.md$/i.test(normalized)
    || /^packages\/[^/]+\/README\.md$/i.test(normalized)
    || /^skills\/.+\.md$/i.test(normalized);
}

function collectTargetFiles() {
  return gitLsFiles(["--cached"])
    .filter(isTargetMarkdown)
    .sort();
}

function stripFencedCode(lines) {
  let inFence = false;
  return lines.map((line) => {
    if (/^\s*(```|~~~)/.test(line)) {
      inFence = !inFence;
      return "";
    }
    return inFence ? "" : line;
  });
}

function parseMarkdownDestination(rawDestination) {
  const raw = rawDestination.trim();
  if (raw.startsWith("<")) {
    const end = raw.indexOf(">");
    if (end !== -1) {
      return raw.slice(1, end).trim();
    }
  }

  const match = raw.match(/^\S+/);
  return match ? match[0].trim() : "";
}

function extractLinks(filePath) {
  const absolutePath = path.join(rootDir, filePath);
  const rawLines = fs.readFileSync(absolutePath, "utf8").split(/\r?\n/);
  const lines = stripFencedCode(rawLines);
  const links = [];

  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    const withoutInlineCode = line.replace(/`[^`]*`/g, " ");

    for (const regex of [
      /!?\[[^\]\n]*\]\(([^)\n]+)\)/g,
      /\b(?:href|src)=["']([^"']+)["']/gi,
    ]) {
      for (const match of withoutInlineCode.matchAll(regex)) {
        links.push({
          line: lineNumber,
          target: parseMarkdownDestination(match[1]),
        });
      }
    }

    const referenceMatch = withoutInlineCode.match(/^\s*\[[^\]]+\]:\s*(\S+)/);
    if (referenceMatch) {
      links.push({
        line: lineNumber,
        target: parseMarkdownDestination(referenceMatch[1]),
      });
    }
  });

  return links.filter((link) => link.target);
}

function isIgnoredUrl(target) {
  return ignoreUrlPatterns.some((pattern) => pattern.test(target));
}

function splitLocalTarget(target) {
  const cutPoints = [target.indexOf("#"), target.indexOf("?")]
    .filter((index) => index >= 0);
  const cutAt = cutPoints.length > 0 ? Math.min(...cutPoints) : target.length;
  return target.slice(0, cutAt);
}

function decodeLocalPath(target) {
  try {
    return decodeURI(target);
  } catch {
    return target;
  }
}

function resolveLocalTarget(sourceFile, target) {
  const localPath = decodeLocalPath(splitLocalTarget(target));
  if (!localPath) {
    return null;
  }

  if (localPath.startsWith("/")) {
    return path.resolve(rootDir, `.${localPath}`);
  }

  return path.resolve(path.dirname(path.join(rootDir, sourceFile)), localPath);
}

function pathExistsCaseSensitive(absolutePath) {
  const relativePath = path.relative(rootDir, absolutePath);
  if (!relativePath || relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
    return false;
  }

  let currentPath = rootDir;
  for (const segment of relativePath.split(path.sep)) {
    if (!segment) {
      continue;
    }
    if (!fs.existsSync(currentPath) || !fs.statSync(currentPath).isDirectory()) {
      return false;
    }
    const entries = fs.readdirSync(currentPath);
    if (!entries.includes(segment)) {
      return false;
    }
    currentPath = path.join(currentPath, segment);
  }

  return fs.existsSync(currentPath);
}

const targetFiles = collectTargetFiles();
const failures = [];
let localLinkCount = 0;
let ignoredLinkCount = 0;

for (const filePath of targetFiles) {
  for (const link of extractLinks(filePath)) {
    if (isIgnoredUrl(link.target)) {
      ignoredLinkCount += 1;
      continue;
    }

    localLinkCount += 1;
    const resolvedTarget = resolveLocalTarget(filePath, link.target);
    if (!resolvedTarget) {
      continue;
    }

    const relativeTarget = path.relative(rootDir, resolvedTarget);
    if (relativeTarget.startsWith("..") || path.isAbsolute(relativeTarget)) {
      failures.push(`${filePath}:${link.line} -> ${link.target} points outside the repository`);
      continue;
    }

    if (!pathExistsCaseSensitive(resolvedTarget)) {
      failures.push(`${filePath}:${link.line} -> ${link.target} was not found`);
    }
  }
}

if (failures.length > 0) {
  console.error("Broken Markdown links were found:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log(
  `OK checked ${targetFiles.length} Markdown files and ${localLinkCount} local links `
    + `(${ignoredLinkCount} configured skips).`,
);
