import { createInterface } from "node:readline";
import { stdin as input, stdout as output } from "node:process";
import { loadConfig } from "./config.js";
import { createToolDefinitions, type ToolContext, type ToolDefinition } from "./tools.js";

export interface JsonRpcRequest {
  jsonrpc?: "2.0";
  id?: string | number | null;
  method: string;
  params?: any;
}

export interface JsonRpcResponse {
  jsonrpc: "2.0";
  id: string | number | null;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

export interface McpServerOptions extends Partial<ToolContext> {
  protocolVersion?: string;
  serverName?: string;
  serverVersion?: string;
}

function publicTool(tool: ToolDefinition): Record<string, unknown> {
  const { name, description, inputSchema } = tool;
  return { name, description, inputSchema };
}

function textContent(value: unknown): { content: Array<{ type: "text"; text: string }>; isError?: boolean } {
  return { content: [{ type: "text", text: JSON.stringify(value, null, 2) }] };
}

export class OpenJobsMcpServer {
  private readonly protocolVersion: string;
  private readonly serverName: string;
  private readonly serverVersion: string;
  private readonly ctx: ToolContext;

  constructor(options: McpServerOptions = {}) {
    this.protocolVersion = options.protocolVersion ?? "2024-11-05";
    this.serverName = options.serverName ?? "openjobs-mcp";
    this.serverVersion = options.serverVersion ?? "3.2.0";
    this.ctx = {
      config: options.config ?? loadConfig(),
      clientFactory: options.clientFactory,
    };
  }

  tools(): ToolDefinition[] {
    return createToolDefinitions(this.ctx);
  }

  async handle(request: JsonRpcRequest): Promise<JsonRpcResponse | undefined> {
    if (request.id === undefined && request.method === "notifications/initialized") return undefined;
    const id = request.id ?? null;
    try {
      switch (request.method) {
        case "initialize":
          return {
            jsonrpc: "2.0",
            id,
            result: {
              protocolVersion: this.protocolVersion,
              capabilities: { tools: {} },
              serverInfo: { name: this.serverName, version: this.serverVersion },
            },
          };
        case "tools/list":
          return { jsonrpc: "2.0", id, result: { tools: this.tools().map(publicTool) } };
        case "tools/call": {
          const name = request.params?.name;
          const args = request.params?.arguments ?? {};
          if (typeof name !== "string") throw new Error("tools/call requires params.name");
          const tool = this.tools().find((item) => item.name === name);
          if (!tool) {
            return { jsonrpc: "2.0", id, result: { ...textContent({ ok: false, error: { code: "OPENJOBS_TOOL_NOT_FOUND", message: `Unknown tool: ${name}`, retryable: false }, warnings: [], nextActions: ["openjobs_setup_status"] }), isError: true } };
          }
          const result = await tool.handler(args);
          return { jsonrpc: "2.0", id, result: { ...textContent(result), isError: !result.ok } };
        }
        case "resources/list":
          return { jsonrpc: "2.0", id, result: { resources: [] } };
        case "prompts/list":
          return { jsonrpc: "2.0", id, result: { prompts: [] } };
        default:
          return { jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${request.method}` } };
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { jsonrpc: "2.0", id, error: { code: -32603, message } };
    }
  }
}

export async function runStdioServer(server = new OpenJobsMcpServer()): Promise<void> {
  const rl = createInterface({ input, crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line.trim()) continue;
    let request: JsonRpcRequest;
    try {
      request = JSON.parse(line) as JsonRpcRequest;
    } catch (err) {
      output.write(`${JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } })}\n`);
      continue;
    }
    const response = await server.handle(request);
    if (response) output.write(`${JSON.stringify(response)}\n`);
  }
}
