#!/usr/bin/env node
"use strict";

/**
 * Edgrapi MCP — stdio bridge to the hosted server at https://api.edgrapi.com/mcp
 *
 * MCP clients that only speak stdio (and registries that want an install command)
 * can run this instead of pointing at the URL directly. It reads newline-delimited
 * JSON-RPC on stdin, POSTs each message to the hosted endpoint, and writes the
 * reply back on stdout. Nothing is cached, rewritten or interpreted here — the
 * hosted server remains the only source of tools and data.
 *
 * Auth: set EDGRAPI_API_KEY (or pass --key). Get a free key at https://edgrapi.com/app.
 * If you would rather use OAuth, point your client straight at the URL instead;
 * this bridge deliberately does not run a browser sign-in flow.
 *
 * Zero dependencies. Node 18+ (needs global fetch).
 */

const DEFAULT_URL = "https://api.edgrapi.com/mcp";

// stdout is reserved for protocol traffic; everything else goes to stderr.
const log = (...a) => process.stderr.write(a.join(" ") + "\n");

function parseArgs(argv) {
  const out = { key: null, url: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--key" || a === "-k") out.key = argv[++i];
    else if (a.startsWith("--key=")) out.key = a.slice(6);
    else if (a === "--url" || a === "-u") out.url = argv[++i];
    else if (a.startsWith("--url=")) out.url = a.slice(6);
    else if (a === "--version" || a === "-v") {
      console.log(require("../package.json").version);
      process.exit(0);
    } else if (a === "--help" || a === "-h") {
      log(
        "edgrapi-mcp — stdio bridge to https://api.edgrapi.com/mcp\n\n" +
          "  --key,  -k <key>   Edgrapi API key (or set EDGRAPI_API_KEY)\n" +
          "  --url,  -u <url>   override the endpoint (default " + DEFAULT_URL + ")\n" +
          "  --version, -v      print the bridge version\n\n" +
          "Free key: https://edgrapi.com/app"
      );
      process.exit(0);
    }
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const API_KEY = args.key || process.env.EDGRAPI_API_KEY || "";
const URL_ENDPOINT = args.url || process.env.EDGRAPI_MCP_URL || DEFAULT_URL;

if (!API_KEY) {
  log(
    "edgrapi-mcp: no API key. Set EDGRAPI_API_KEY or pass --key.\n" +
      "Requests will go out unauthenticated and the server will answer 401.\n" +
      "Free key (100 credits/month, no card): https://edgrapi.com/app"
  );
}

const UA = "edgrapi-mcp/" + require("../package.json").version + " (+https://edgrapi.com)";

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function rpcError(id, code, message) {
  // A notification (no id) gets no reply, per JSON-RPC.
  if (id === undefined || id === null) return;
  send({ jsonrpc: "2.0", id, error: { code, message } });
}

/** Forward one JSON-RPC message and relay whatever comes back. */
async function forward(msg) {
  const id = msg && typeof msg === "object" ? msg.id : undefined;
  let res;
  try {
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
      "User-Agent": UA,
    };
    if (API_KEY) headers.Authorization = "Bearer " + API_KEY;
    res = await fetch(URL_ENDPOINT, {
      method: "POST",
      headers,
      body: JSON.stringify(msg),
    });
  } catch (e) {
    rpcError(id, -32603, "Cannot reach " + URL_ENDPOINT + ": " + (e && e.message ? e.message : e));
    return;
  }

  // 204 is how the server acknowledges notifications — nothing to relay.
  if (res.status === 204) return;

  const text = await res.text();
  if (!text) {
    if (!res.ok) rpcError(id, -32603, "HTTP " + res.status + " with an empty body");
    return;
  }

  let body;
  try {
    body = JSON.parse(text);
  } catch (_) {
    rpcError(id, -32603, "HTTP " + res.status + ": response was not JSON: " + text.slice(0, 300));
    return;
  }

  // The server answers 401 with a JSON-RPC error body; pass it through so the
  // client shows the real message instead of a transport failure.
  send(body);
}

// MCP stdio framing is one JSON message per line.
let buf = "";
const queue = [];
let draining = false;

async function drain() {
  if (draining) return;
  draining = true;
  while (queue.length) await forward(queue.shift());
  draining = false;
}

process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buf += chunk;
  let nl;
  while ((nl = buf.indexOf("\n")) !== -1) {
    const line = buf.slice(0, nl).trim();
    buf = buf.slice(nl + 1);
    if (!line) continue;
    let msg;
    try {
      msg = JSON.parse(line);
    } catch (_) {
      send({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } });
      continue;
    }
    queue.push(msg);
  }
  drain();
});

process.stdin.on("end", () => {
  // Let anything still in flight finish before the process goes away.
  const wait = () => (queue.length || draining ? setTimeout(wait, 25) : process.exit(0));
  wait();
});

process.on("SIGINT", () => process.exit(0));
process.on("SIGTERM", () => process.exit(0));
