import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const jsExample = path.join(rootDir, "examples", "js-agent-tool.mjs");
const pythonExample = path.join(rootDir, "examples", "python-agent-tool.py");
const sdkPythonPath = path.join(rootDir, "packages", "sdk-python");
const pythonCmd = process.platform === "win32" ? "python" : "python3";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: rootDir,
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

function withPythonPath(extraPath) {
  const separator = process.platform === "win32" ? ";" : ":";
  const current = process.env.PYTHONPATH;
  return {
    ...process.env,
    PYTHONPATH: current ? `${extraPath}${separator}${current}` : extraPath,
  };
}

console.log("Checking JavaScript example syntax...");
run(process.execPath, ["--check", jsExample]);

console.log("Checking Python example syntax...");
run(pythonCmd, ["-m", "py_compile", pythonExample]);

console.log("Checking Python SDK import path used by the example...");
run(pythonCmd, ["-c", "from openjobs import OpenJobsClient; assert OpenJobsClient"], {
  env: withPythonPath(sdkPythonPath),
});

console.log("OK example smoke checks passed.");
