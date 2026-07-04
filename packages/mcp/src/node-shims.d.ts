declare const process: {
  env: Record<string, string | undefined>;
  argv: string[];
  exitCode?: number;
  stdin: unknown;
  stdout: { write(chunk: string): void };
};

declare module "node:fs" {
  export function chmodSync(path: string, mode: number): void;
  export function existsSync(path: string): boolean;
  export function mkdirSync(path: string, options?: { recursive?: boolean; mode?: number }): void;
  export function mkdtempSync(prefix: string): string;
  export function readFileSync(path: string, encoding: string): string;
  export function rmSync(path: string, options?: { force?: boolean }): void;
  export function writeFileSync(path: string, data: string, options?: { mode?: number }): void;
}

declare module "node:path" {
  export function dirname(path: string): string;
  export function join(...paths: string[]): string;
}

declare module "node:os" {
  export function homedir(): string;
  export function tmpdir(): string;
}

declare module "node:process" {
  export const stdin: unknown;
  export const stdout: { write(chunk: string): void };
}

declare module "node:readline" {
  export function createInterface(options: { input: unknown; crlfDelay?: number }): AsyncIterable<string>;
}

declare module "node:assert/strict" {
  const assert: any;
  export default assert;
}

declare module "node:test" {
  const test: any;
  export default test;
}
