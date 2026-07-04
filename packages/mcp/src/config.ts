import { chmodSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { homedir } from "node:os";

export interface OpenJobsMcpConfig {
  apiKey?: string;
  apiUrl: string;
  mode: "worker" | "poster";
  readOnly: boolean;
  requireConfirmation: boolean;
  allowRegister: boolean;
  configPath: string;
}

export interface StoredOpenJobsConfig {
  apiKey?: string;
  apiUrl?: string;
  agent?: unknown;
  mcp?: {
    mode?: "worker" | "poster";
  };
}

const DEFAULT_API_URL = "https://openjobs.bot/api";

export function defaultConfigPath(): string {
  return join(homedir(), ".openjobs", "config.json");
}

function truthy(value: string | undefined): boolean {
  return value === "1" || value === "true" || value === "yes";
}

export function readStoredConfig(configPath: string): StoredOpenJobsConfig {
  if (!existsSync(configPath)) return {};
  try {
    return JSON.parse(readFileSync(configPath, "utf8")) as StoredOpenJobsConfig;
  } catch {
    return {};
  }
}

export function loadConfig(env: Record<string, string | undefined> = process.env): OpenJobsMcpConfig {
  const configPath = env.OPENJOBS_MCP_CONFIG_PATH || defaultConfigPath();
  const stored = readStoredConfig(configPath);
  const mode = (env.OPENJOBS_MCP_MODE || stored.mcp?.mode) === "poster" ? "poster" : "worker";
  return {
    apiKey: env.OPENJOBS_API_KEY || stored.apiKey,
    apiUrl: env.OPENJOBS_API_URL || stored.apiUrl || DEFAULT_API_URL,
    mode,
    readOnly: truthy(env.OPENJOBS_MCP_READ_ONLY),
    requireConfirmation: truthy(env.OPENJOBS_MCP_REQUIRE_CONFIRMATION),
    allowRegister: env.OPENJOBS_MCP_ALLOW_REGISTER === undefined ? true : truthy(env.OPENJOBS_MCP_ALLOW_REGISTER),
    configPath,
  };
}

export function apiBaseUrl(apiUrl: string): string {
  return apiUrl.replace(/\/api\/?$/, "");
}

export function saveCredentials(configPath: string, input: { apiKey: string; apiUrl?: string; agent?: unknown; mode?: "worker" | "poster" }): StoredOpenJobsConfig {
  const existing = readStoredConfig(configPath);
  const next: StoredOpenJobsConfig = {
    ...existing,
    apiKey: input.apiKey,
    apiUrl: input.apiUrl || existing.apiUrl || DEFAULT_API_URL,
    agent: input.agent ?? existing.agent,
    mcp: { ...(existing.mcp || {}), ...(input.mode ? { mode: input.mode } : {}) },
  };
  mkdirSync(dirname(configPath), { recursive: true, mode: 0o700 });
  writeFileSync(configPath, `${JSON.stringify(next, null, 2)}\n`, { mode: 0o600 });
  try { chmodSync(configPath, 0o600); } catch { /* best effort on non-POSIX filesystems */ }
  return next;
}

export function clearCredentials(configPath: string): void {
  if (!existsSync(configPath)) return;
  const existing = readStoredConfig(configPath);
  delete existing.apiKey;
  delete existing.agent;
  if (Object.keys(existing).length === 0 || (Object.keys(existing).length === 1 && existing.mcp)) {
    rmSync(configPath, { force: true });
    return;
  }
  writeFileSync(configPath, `${JSON.stringify(existing, null, 2)}\n`, { mode: 0o600 });
}

export function redactSecret(value: string | undefined): string | undefined {
  if (!value) return undefined;
  if (value.length <= 8) return "********";
  return `${value.slice(0, 4)}…${value.slice(-4)}`;
}

export function redactDeep<T>(input: T): T {
  if (Array.isArray(input)) return input.map((item) => redactDeep(item)) as T;
  if (input && typeof input === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(input as Record<string, unknown>)) {
      if (/api[-_]?key|token|secret|signature|signedTransaction/i.test(key)) {
        out[key] = typeof value === "string" ? redactSecret(value) : "[redacted]";
      } else {
        out[key] = redactDeep(value);
      }
    }
    return out as T;
  }
  return input;
}
