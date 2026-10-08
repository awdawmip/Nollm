import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { EventEmitter } from "node:events";
import { readFileSync } from "node:fs";
import path from "node:path";
import { StringDecoder } from "node:string_decoder";
import test from "node:test";
import vm from "node:vm";

const LIMIT = 1048576;
const source = readFileSync(new URL("../src/bridge-runtime.js", import.meta.url), "utf8");
const configSource = readFileSync(new URL("../src/config.js", import.meta.url), "utf8");
const envelope = { action: "synthetic" };

class FakeSignal {
  aborted = false;
  listeners = new Map();
  addEventListener(type, listener, options) {
    assert.equal(type, "abort");
    this.listeners.set(listener, options);
  }
  removeEventListener(type, listener) {
    assert.equal(type, "abort");
    this.listeners.delete(listener);
  }
  abort() {
    this.aborted = true;
    for (const [listener, options] of [...this.listeners]) {
      if (options?.once) this.listeners.delete(listener);
      listener();
    }
  }
}

async function harness({ signal = new FakeSignal(), mode = "packaged" } = {}) {
  const allocations = [], decoders = [], spawnCalls = [], timers = [], kills = [];
  const child = new EventEmitter();
  child.stdout = new EventEmitter();
  child.stderr = new EventEmitter();
  child.stdin = { end: (...args) => { child.input = args; } };
  child.kill = (...args) => { kills.push(args); return true; };
  const trackedBuffer = new Proxy(Buffer, {
    get(target, key) {
      if (key === "alloc") return (...args) => {
        const buffer = Buffer.alloc(...args);
        allocations.push(buffer);
        return buffer;
      };
      return Reflect.get(target, key);
    }
  });
  class ObservedDecoder extends StringDecoder {
    constructor(...args) { super(...args); this.writes = []; this.ends = []; decoders.push(this); }
    write(bytes) { const text = super.write(bytes); this.writes.push({ bytes: bytes.length, text }); return text; }
    end(...args) { const text = super.end(...args); this.ends.push(text); return text; }
  }
  const context = vm.createContext({
    process: { env: {}, platform: "linux" },
    setTimeout: (callback, milliseconds) => {
      const timer = { callback, milliseconds, active: true };
      timers.push(timer);
      return timer;
    },
    clearTimeout: (timer) => { timer.active = false; }
  });
  const synthetic = (exports) => new vm.SyntheticModule(Object.keys(exports), function () {
    for (const [name, value] of Object.entries(exports)) this.setExport(name, value);
  }, { context });
  const modules = {
    "node:child_process": synthetic({ spawn: (...args) => { spawnCalls.push(args); return child; } }),
    "node:buffer": synthetic({ Buffer: trackedBuffer }),
    "node:path": synthetic({ default: path }),
    "node:string_decoder": synthetic({ StringDecoder: ObservedDecoder }),
    "./config.js": new vm.SourceTextModule(configSource, { context, identifier: "copied-config.js" })
  };
  const module = new vm.SourceTextModule(source, { context, identifier: "candidate-bridge-runtime.js" });
  await module.link((specifier) => {
    assert.ok(Object.hasOwn(modules, specifier), `unexpected import: ${specifier}`);
    return modules[specifier];
  });
  await module.evaluate();
  const runtime = new module.namespace.NollmBridgeRuntime({
    runtimeMode: mode, runtimeExecutable: "/synthetic/sidecar", runtimeArgs: ["--fixture"],
    commandTimeoutMs: 25, dataRoot: "/synthetic/data"
  });
  const promise = runtime.call(envelope, signal);
  return {
    allocations, decoders, spawnCalls, timers, kills, signal, child,
    stdout: (bytes) => child.stdout.emit("data", bytes),
    stderr: (bytes) => child.stderr.emit("data", bytes),
    close: (code = 0) => child.emit("close", code),
    timeout: (queued = false) => { assert.ok(queued || timers[0].active); timers[0].callback(); },
    result: async () => JSON.parse(JSON.stringify(await promise))
  };
}

function paddedJson(bytes) {
  const buffer = Buffer.alloc(bytes, 0x20);
  Buffer.from('{"ok":true}').copy(buffer);
  return buffer;
}
function failure(result, error) {
  assert.equal(result.ok, false);
  assert.equal(result.error, error);
  assert.equal(result.retryable, true);
}
function noBrokenSurrogate(text) {
  for (let i = 0; i < text.length; i += 1) {
    const unit = text.charCodeAt(i);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = text.charCodeAt(++i);
      assert.ok(next >= 0xdc00 && next <= 0xdfff);
    } else assert.ok(unit < 0xdc00 || unit > 0xdfff);
  }
}

test("normal ASCII JSON preserves packaged framing and decodes only at close", async () => {
  const h = await harness();
  h.stdout(Buffer.from('{"ok":true,"text":"ASCII"}'));
  assert.equal(h.decoders.length, 0);
  h.close();
  assert.deepEqual(await h.result(), { ok: true, text: "ASCII" });
  const [command, args, options] = h.spawnCalls[0];
  assert.equal(command, "/synthetic/sidecar");
  assert.deepEqual(Array.from(args), ["--fixture", "bridge"]);
  assert.equal(options.shell, false);
  assert.deepEqual(JSON.parse(Buffer.from(h.child.input[0], "base64").toString("utf8")), envelope);
  assert.equal(h.child.input[1], "utf8");
  assert.equal(h.kills.length, 0);
});

test("Chinese and non-BMP JSON survive every byte split and one-byte chunks", async () => {
  const value = { ok: true, text: "中文💡𐐷" }, bytes = Buffer.from(JSON.stringify(value));
  for (let split = 0; split <= bytes.length; split += 1) {
    const h = await harness();
    h.stdout(bytes.subarray(0, split)); h.stdout(bytes.subarray(split));
    assert.equal(h.decoders.length, 0); h.close();
    assert.deepEqual(await h.result(), value, `split ${split}`);
  }
  const h = await harness();
  for (let i = 0; i < bytes.length; i += 1) h.stdout(bytes.subarray(i, i + 1));
  h.close(); assert.deepEqual(await h.result(), value);
});

test("stderr Chinese and non-BMP text survives every byte split", async () => {
  const text = "诊断💡𐐷", bytes = Buffer.from(text);
  for (let split = 0; split <= bytes.length; split += 1) {
    const h = await harness();
    h.stderr(bytes.subarray(0, split)); h.stderr(bytes.subarray(split)); h.close(1);
    const result = await h.result(); failure(result, "bridge_process_error");
    assert.equal(result.detail, text, `split ${split}`);
  }
});

test("valid JSON at one byte below and exactly the byte limit succeeds", async () => {
  for (const bytes of [LIMIT - 1, LIMIT]) {
    const h = await harness(); h.stdout(paddedJson(bytes)); h.stdout(Buffer.alloc(0)); h.close();
    assert.deepEqual(await h.result(), { ok: true });
  }
});

test("one excess stdout byte rejects valid JSON plus trailing whitespace without killing", async () => {
  const h = await harness(); h.stdout(paddedJson(LIMIT + 1)); h.close();
  const result = await h.result(); failure(result, "bridge_invalid_json");
  assert.equal(result.detail, `stdout exceeded ${LIMIT} bytes`);
  assert.equal(h.kills.length, 0);
});

test("stdout overflow reason and stderr marker fit the diagnostic cap without a broken surrogate", async () => {
  const prefix = `stdout exceeded ${LIMIT} bytes\n`, suffix = "\n[stderr truncated]";
  const h = await harness(); h.stdout(paddedJson(LIMIT + 1));
  h.stderr(Buffer.from("a".repeat(4000 - prefix.length - suffix.length - 1) + "💡" + "z".repeat(40)));
  h.close(); const result = await h.result(); failure(result, "bridge_invalid_json");
  assert.ok(result.detail.startsWith(prefix)); assert.ok(result.detail.endsWith(suffix));
  assert.ok(result.detail.length <= 4000); noBrokenSurrogate(result.detail);
});

test("many stdout chunks crossing the limit reject instead of parsing a valid prefix", async () => {
  const h = await harness(); h.stdout(paddedJson(LIMIT)); h.stdout(Buffer.from(" "));
  const saved = Buffer.from(h.allocations[0]); h.stdout(Buffer.alloc(LIMIT * 2, 0x78));
  assert.ok(h.allocations[0].equals(saved)); h.close();
  failure(await h.result(), "bridge_invalid_json");
});

test("a huge Chinese chunk is copied into two fixed independent owned buffers", async () => {
  const h = await harness(), bytes = Buffer.from("中".repeat(LIMIT));
  h.stdout(bytes); h.stderr(bytes);
  assert.equal(h.allocations.length, 2);
  for (const owned of h.allocations) {
    assert.equal(owned.length, LIMIT); assert.equal(owned.buffer.byteLength, LIMIT);
    assert.notEqual(owned.buffer, bytes.buffer);
  }
  bytes.fill(0x78);
  for (const owned of h.allocations) assert.equal(owned[0], 0xe4);
  assert.equal(h.decoders.length, 0); h.close(1);
  const result = await h.result(); failure(result, "bridge_process_error");
  assert.ok(result.detail.startsWith("中")); assert.ok(result.detail.endsWith("\n[stderr truncated]"));
  assert.ok(result.detail.length <= 4000);
});

test("independent full budgets and overflowed stderr preserve valid stdout success", async () => {
  for (const bytes of [LIMIT, LIMIT + 1]) {
    const h = await harness(); h.stdout(paddedJson(LIMIT)); h.stderr(Buffer.alloc(bytes, 0x61)); h.close();
    assert.deepEqual(await h.result(), { ok: true });
  }
});

test("overflowed stderr drops the unfinished UTF-8 tail and marks its diagnostic", async () => {
  for (const character of ["中", "💡"]) {
    const encoded = Buffer.from(character);
    for (let retained = 1; retained < encoded.length; retained += 1) {
      const h = await harness(), bytes = Buffer.alloc(LIMIT + encoded.length - retained, 0x61);
      encoded.copy(bytes, LIMIT - retained); h.stderr(bytes);
      assert.equal(h.decoders.length, 0); h.close(1);
      const result = await h.result(), decoder = h.decoders[0];
      failure(result, "bridge_process_error");
      assert.equal(decoder.ends.length, 0); assert.equal(decoder.lastNeed, encoded.length - retained);
      assert.equal(decoder.writes[0].text, "a".repeat(LIMIT - retained));
      assert.ok(result.detail.endsWith("\n[stderr truncated]")); assert.ok(result.detail.length <= 4000);
    }
  }
});

test("non-overflow stderr retains normal decoder end behavior for malformed EOF", async () => {
  const h = await harness(); h.stderr(Buffer.from([0xe4])); h.close(1);
  const result = await h.result(); failure(result, "bridge_process_error");
  assert.equal(result.detail, "\ufffd"); assert.equal(h.decoders[0].ends.length, 1);
});

test("diagnostic character truncation marks either stream without splitting a surrogate pair", async () => {
  for (const stream of ["stdout", "stderr"]) {
    const marker = `\n[${stream} truncated]`, h = await harness();
    h[stream](Buffer.from("a".repeat(4000 - marker.length - 1) + "💡" + "z".repeat(40))); h.close(1);
    const result = await h.result(); failure(result, "bridge_process_error");
    assert.ok(result.detail.endsWith(marker)); assert.ok(result.detail.length <= 4000);
    assert.equal(result.detail.includes("💡"), false); noBrokenSurrogate(result.detail);
  }
});

test("a diagnostic exactly 4000 characters is retained without a truncation marker", async () => {
  const h = await harness(); h.stderr(Buffer.alloc(4000, 0x61)); h.close(1);
  assert.equal((await h.result()).detail, "a".repeat(4000));
});

test("nonzero exit takes priority over stdout overflow and prefers stderr", async () => {
  const h = await harness(); h.stdout(paddedJson(LIMIT + 1)); h.stderr(Buffer.from("specific failure")); h.close(7);
  const result = await h.result(); failure(result, "bridge_process_error"); assert.equal(result.detail, "specific failure");
  const fallback = await harness(); fallback.stdout(paddedJson(LIMIT + 1)); fallback.close(1);
  const failed = await fallback.result(); failure(failed, "bridge_process_error");
  assert.ok(failed.detail.endsWith("\n[stdout truncated]")); assert.ok(failed.detail.length <= 4000);
});

test("null exit code remains process failure with stdout fallback", async () => {
  const h = await harness(); h.stdout(Buffer.from("fallback diagnostic")); h.close(null);
  const result = await h.result(); failure(result, "bridge_process_error"); assert.equal(result.detail, "fallback diagnostic");
});

test("invalid JSON preserves the existing retryable error and bounded stderr detail", async () => {
  const h = await harness(); h.stdout(Buffer.from("not JSON")); h.stderr(Buffer.from("parse diagnostic")); h.close();
  const result = await h.result(); failure(result, "bridge_invalid_json"); assert.equal(result.detail, "parse diagnostic");
});

test("process error before close preserves its code and detail even after overflow", async () => {
  const h = await harness(); h.stdout(paddedJson(LIMIT + 1)); h.child.emit("error", new Error("synthetic boom")); h.close();
  const result = await h.result(); failure(result, "bridge_process_error"); assert.equal(result.detail, "Error: synthetic boom");
});

test("already-aborted signal prevents spawn and collector allocation", async () => {
  const signal = new FakeSignal(); signal.abort(); const h = await harness({ signal });
  failure(await h.result(), "bridge_aborted"); assert.equal(h.spawnCalls.length, 0);
  assert.equal(h.allocations.length, 0); assert.equal(h.timers.length, 0);
});

test("overflow then abort beats an already-queued timeout and later close", async () => {
  const h = await harness(); h.stdout(paddedJson(LIMIT + 1)); h.signal.abort(); h.timeout(true); h.close();
  failure(await h.result(), "bridge_aborted"); assert.deepEqual(h.kills[0], ["SIGKILL"]);
  assert.equal(h.signal.listeners.size, 0); assert.equal(h.timers[0].active, false);
});

test("overflow then timeout beats subsequent abort and close", async () => {
  const h = await harness(); h.stdout(paddedJson(LIMIT + 1)); h.timeout(); h.signal.abort(); h.close();
  failure(await h.result(), "bridge_timeout"); assert.deepEqual(h.kills, [["SIGKILL"]]);
  assert.equal(h.signal.listeners.size, 0); assert.equal(h.timers[0].active, false);
});

test("abort before output and process error still settles only once", async () => {
  const h = await harness(); h.signal.abort(); h.stdout(paddedJson(LIMIT + 1));
  h.child.emit("error", new Error("later")); h.close(1); failure(await h.result(), "bridge_aborted");
});

test("timeout before process error still settles only once", async () => {
  const h = await harness(); h.timeout(); h.child.emit("error", new Error("later")); h.close(1);
  failure(await h.result(), "bridge_timeout");
});

test("successful close removes abort listener and clears the timer", async () => {
  const h = await harness(); h.stdout(Buffer.from('{"ok":true}')); h.close();
  assert.deepEqual(await h.result(), { ok: true }); assert.equal(h.signal.listeners.size, 0);
  assert.equal(h.timers[0].active, false); h.signal.abort(); h.close(1); assert.equal(h.kills.length, 0);
});

test("unavailable runtime preserves retryable false and avoids spawning", async () => {
  const h = await harness({ mode: "unavailable" });
  assert.deepEqual(await h.result(), { ok: false, error: "runtime_unavailable", retryable: false });
  assert.equal(h.spawnCalls.length, 0); assert.equal(h.allocations.length, 0);
});
