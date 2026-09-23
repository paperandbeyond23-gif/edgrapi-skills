#!/usr/bin/env node
"use strict";

/**
 * Smoke test: spawn the bridge, speak MCP to it over stdio, and check that the
 * hosted server answers. `initialize` and `tools/list` need no credential, so
 * this runs without a key. With EDGRAPI_API_KEY set it also calls a real tool.
 */

const { spawn } = require("child_process");
const path = require("path");

const BIN = path.join(__dirname, "..", "bin", "edgrapi-mcp.js");
const KEY = process.env.EDGRAPI_API_KEY || "";

const child = spawn(process.execPath, [BIN], {
  stdio: ["pipe", "pipe", "inherit"],
  env: process.env,
});

const replies = [];
let buf = "";
child.stdout.setEncoding("utf8");
child.stdout.on("data", (c) => {
  buf += c;
  let nl;
  while ((nl = buf.indexOf("\n")) !== -1) {
    const line = buf.slice(0, nl).trim();
    buf = buf.slice(nl + 1);
    if (line) replies.push(JSON.parse(line));
  }
});

const write = (o) => child.stdin.write(JSON.stringify(o) + "\n");

function waitFor(id, ms = 30000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const tick = () => {
      const hit = replies.find((r) => r.id === id);
      if (hit) return resolve(hit);
      if (Date.now() - started > ms) return reject(new Error("timed out waiting for id " + id));
      setTimeout(tick, 50);
    };
    tick();
  });
}

let failures = 0;
function check(name, cond, detail) {
  if (cond) {
    console.log("  ok   " + name);
  } else {
    failures++;
    console.log("  FAIL " + name + (detail ? " — " + detail : ""));
  }
}

(async () => {
  console.log("edgrapi-mcp smoke test");

  write({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "smoke", version: "0" } },
  });
  const init = await waitFor(1);
  check("initialize returns a result", !!init.result, JSON.stringify(init).slice(0, 200));
  check("serverInfo has a name", !!(init.result && init.result.serverInfo && init.result.serverInfo.name));

  // A notification must produce no reply at all.
  const before = replies.length;
  write({ jsonrpc: "2.0", method: "notifications/initialized" });
  await new Promise((r) => setTimeout(r, 1500));
  check("notification produces no reply", replies.length === before);

  write({ jsonrpc: "2.0", id: 2, method: "tools/list" });
  const list = await waitFor(2);
  const tools = (list.result && list.result.tools) || [];
  check("tools/list returns tools", tools.length > 0, "got " + tools.length);
  const names = tools.map((t) => t.name);
  for (const t of ["get_opportunities", "get_awards", "get_grants", "get_congress"]) {
    check("gov tool present: " + t, names.includes(t));
  }
  console.log("  info " + tools.length + " tools: " + names.join(", "));

  if (KEY) {
    write({
      jsonrpc: "2.0",
      id: 3,
      method: "tools/call",
      params: { name: "get_grants", arguments: { limit: 2 } },
    });
    const call = await waitFor(3);
    check("authenticated tools/call succeeds", !!call.result && !call.error, JSON.stringify(call).slice(0, 300));
  } else {
    write({ jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "get_grants", arguments: { limit: 1 } } });
    const call = await waitFor(4);
    check("unauthenticated tools/call returns a clean 401 error", !!call.error, JSON.stringify(call).slice(0, 200));
    console.log("  info set EDGRAPI_API_KEY to also test a real tool call");
  }

  child.stdin.end();
  console.log(failures ? "\n" + failures + " check(s) failed" : "\nall checks passed");
  process.exit(failures ? 1 : 0);
})().catch((e) => {
  console.error("smoke test error:", e.message);
  process.exit(1);
});
