import { spawnSync } from "node:child_process";
import { rmSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const buildRoot = join(repoRoot, ".python-package-build");

const targets = [
  { name: "openjobs-py", dir: "packages/sdk-python" },
  { name: "openjobs-langchain", dir: "packages/openjobs-langchain" },
  { name: "openjobs-crewai", dir: "packages/openjobs-crewai" },
  { name: "openjobs-openai", dir: "packages/openjobs-openai" },
];

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    stdio: "inherit",
    ...options,
  });

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed with exit code ${result.status}`);
  }
}

function checkPythonModule(python, moduleName, installName = moduleName) {
  const result = spawnSync(
    python,
    ["-m", moduleName, "--version"],
    {
      cwd: repoRoot,
      stdio: "ignore",
    },
  );

  if (result.status !== 0) {
    throw new Error(
      `Missing Python module "${moduleName}". Install release-check dependencies with: ${python} -m pip install build twine ${installName === "build" ? "" : ""}`.trim(),
    );
  }
}

function distFiles(outDir) {
  return readdirSync(outDir)
    .filter((name) => name.endsWith(".tar.gz") || name.endsWith(".whl"))
    .map((name) => join(outDir, name));
}

const python = process.env.PYTHON ?? "python";

checkPythonModule(python, "build");
checkPythonModule(python, "twine");

rmSync(buildRoot, { recursive: true, force: true });
mkdirSync(buildRoot, { recursive: true });

for (const target of targets) {
  const packageDir = join(repoRoot, target.dir);
  const outDir = join(buildRoot, target.name);

  mkdirSync(outDir, { recursive: true });

  console.log(`Building ${target.name}...`);
  run(python, ["-m", "build", "--sdist", "--wheel", "--outdir", outDir, packageDir]);

  const files = distFiles(outDir);
  const hasSdist = files.some((file) => file.endsWith(".tar.gz"));
  const hasWheel = files.some((file) => file.endsWith(".whl"));

  if (!hasSdist || !hasWheel) {
    throw new Error(`Expected both sdist and wheel artifacts for ${target.name}`);
  }

  console.log(`Checking ${target.name} with twine...`);
  run(python, ["-m", "twine", "check", ...files]);

  console.log(`OK ${target.name}: ${files.length} artifacts checked.`);
}

console.log("All Python package artifacts built and checked successfully.");
