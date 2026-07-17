import { createHash, randomUUID } from "node:crypto";
import { link, mkdir, open, readFile, readdir, stat, unlink } from "node:fs/promises";
import { dirname, join } from "node:path";

export const CAPTURE_SCHEMA = "nollm_openclaw_durable_capture_v1";
export const CAPTURE_STATE_SCHEMA = "nollm_openclaw_capture_state_event_v1";

export type CaptureInput = {
  scopeKey: string;
  sessionKey: string;
  turnIdentity: string;
  userUtf8: string;
  assistantUtf8: string;
  modelRef?: string;
  capturedEpochMs?: number;
};

export type CaptureRecord = {
  schema_version: typeof CAPTURE_SCHEMA;
  capture_id: string;
  scope_id_sha256: string;
  session_key_sha256: string;
  turn_identity_sha256: string;
  captured_epoch_ms: number;
  content_sha256: string;
  user_utf8: string;
  assistant_utf8: string;
  model_ref?: string;
};

export type CaptureStatus = "captured" | "processing" | "retry" | "deferred" | "no_memory" | "admitted";
export type CaptureStateEvent = {
  schema_version: typeof CAPTURE_STATE_SCHEMA;
  event_id: string;
  capture_id: string;
  status: CaptureStatus;
  event_epoch_ms: number;
  attempt: number;
  batch_id?: string;
  statement_ids?: string[];
  error?: string;
};

export type PendingPolicy = { maxCaptures: number; maxChars: number; maxAgeMs: number };
export type AbsorptionResult = { captureId: string; status: "admitted" | "no_memory" | "deferred" | "retry"; statementIds?: string[]; error?: string };

function sha256(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function canonical(value: object): string {
  return `${JSON.stringify(value)}\n`;
}

function assertText(value: string, name: string, allowEmpty = false): void {
  if (typeof value !== "string" || (!allowEmpty && value.length === 0)) throw new TypeError(`${name} must be a non-empty string`);
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit < 0xd800 || unit > 0xdfff) continue;
    if (unit <= 0xdbff && index + 1 < value.length) {
      const next = value.charCodeAt(index + 1);
      if (next >= 0xdc00 && next <= 0xdfff) { index += 1; continue; }
    }
    throw new TypeError(`${name} contains an isolated UTF-16 surrogate`);
  }
}

async function publishImmutable(path: string, bytes: string): Promise<"created" | "replayed"> {
  await mkdir(dirname(path), { recursive: true });
  try {
    const existing = await readFile(path, "utf8");
    if (existing !== bytes) throw new Error(`immutable file conflict: ${path}`);
    return "replayed";
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }
  const temporary = `${path}.${process.pid}.${randomUUID()}.tmp`;
  const handle = await open(temporary, "wx", 0o600);
  try {
    await handle.writeFile(bytes, "utf8");
    await handle.sync();
  } finally {
    await handle.close();
  }
  try {
    await link(temporary, path);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
    const existing = await readFile(path, "utf8");
    if (existing !== bytes) throw new Error(`immutable file conflict: ${path}`);
    return "replayed";
  } finally {
    await unlink(temporary).catch(() => undefined);
  }
  return "created";
}

function parseRecord(text: string): CaptureRecord {
  const value = JSON.parse(text) as CaptureRecord;
  if (value.schema_version !== CAPTURE_SCHEMA || typeof value.capture_id !== "string" || typeof value.scope_id_sha256 !== "string" ||
      typeof value.session_key_sha256 !== "string" || typeof value.turn_identity_sha256 !== "string" ||
      typeof value.captured_epoch_ms !== "number" || typeof value.content_sha256 !== "string" ||
      typeof value.user_utf8 !== "string" || typeof value.assistant_utf8 !== "string" || (value.model_ref !== undefined && typeof value.model_ref !== "string")) throw new Error("invalid Capture record");
  return value;
}

function parseEvent(text: string): CaptureStateEvent {
  const value = JSON.parse(text) as CaptureStateEvent;
  if (value.schema_version !== CAPTURE_STATE_SCHEMA || typeof value.event_id !== "string" || typeof value.capture_id !== "string" ||
      !["captured", "processing", "retry", "deferred", "no_memory", "admitted"].includes(value.status) ||
      typeof value.event_epoch_ms !== "number" || typeof value.attempt !== "number") throw new Error("invalid Capture state event");
  return value;
}

export class CaptureStore {
  readonly root: string;
  constructor(root: string) {
    assertText(root, "Capture root");
    this.root = root;
  }

  capturePath(captureId: string): string { return join(this.root, "captures", `${captureId}.json`); }
  eventDirectory(captureId: string): string { return join(this.root, "events", captureId); }

  async publish(input: CaptureInput): Promise<{ record: CaptureRecord; replayed: boolean; publish_ms: number }> {
    const started = performance.now();
    assertText(input.scopeKey, "scopeKey"); assertText(input.sessionKey, "sessionKey"); assertText(input.turnIdentity, "turnIdentity");
    assertText(input.userUtf8, "userUtf8"); assertText(input.assistantUtf8, "assistantUtf8");
    const scopeHash = sha256(input.scopeKey);
    const sessionHash = sha256(input.sessionKey);
    const turnHash = sha256(input.turnIdentity);
    const contentHash = sha256(canonical({ user_utf8: input.userUtf8, assistant_utf8: input.assistantUtf8 }));
    const captureId = `capture-${sha256(canonical({ scope_id_sha256: scopeHash, turn_identity_sha256: turnHash, content_sha256: contentHash }))}`;
    try {
      const existing = await this.read(captureId);
      if (existing.scope_id_sha256 !== scopeHash || existing.session_key_sha256 !== sessionHash || existing.turn_identity_sha256 !== turnHash || existing.content_sha256 !== contentHash || existing.user_utf8 !== input.userUtf8 || existing.assistant_utf8 !== input.assistantUtf8) {
        throw new Error(`immutable Capture conflict: ${captureId}`);
      }
      return { record: existing, replayed: true, publish_ms: performance.now() - started };
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
    const record: CaptureRecord = {
      schema_version: CAPTURE_SCHEMA, capture_id: captureId, scope_id_sha256: scopeHash,
      session_key_sha256: sessionHash, turn_identity_sha256: turnHash,
      captured_epoch_ms: input.capturedEpochMs ?? Date.now(), content_sha256: contentHash,
      user_utf8: input.userUtf8, assistant_utf8: input.assistantUtf8, model_ref: input.modelRef,
    };
    const result = await publishImmutable(this.capturePath(captureId), canonical(record));
    if (result === "created") await this.appendEvent(captureId, "captured", { attempt: 0, eventEpochMs: record.captured_epoch_ms });
    return { record, replayed: result === "replayed", publish_ms: performance.now() - started };
  }

  async read(captureId: string): Promise<CaptureRecord> {
    return parseRecord(await readFile(this.capturePath(captureId), "utf8"));
  }

  async appendEvent(captureId: string, status: CaptureStatus, options: { attempt: number; eventEpochMs?: number; batchId?: string; statementIds?: string[]; error?: string }): Promise<CaptureStateEvent> {
    const base = { capture_id: captureId, status, event_epoch_ms: options.eventEpochMs ?? Date.now(), attempt: options.attempt,
      batch_id: options.batchId, statement_ids: options.statementIds, error: options.error };
    const eventId = `event-${sha256(canonical(base))}`;
    const event: CaptureStateEvent = { schema_version: CAPTURE_STATE_SCHEMA, event_id: eventId, ...base };
    await publishImmutable(join(this.eventDirectory(captureId), `${eventId}.json`), canonical(event));
    return event;
  }

  async events(captureId: string): Promise<CaptureStateEvent[]> {
    let names: string[];
    try { names = await readdir(this.eventDirectory(captureId)); } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
      throw error;
    }
    const events = await Promise.all(names.filter(name => name.endsWith(".json")).map(async name => parseEvent(await readFile(join(this.eventDirectory(captureId), name), "utf8"))));
    const terminalRank = (status: CaptureStatus): number => status === "processing" ? 1 : status === "captured" ? 0 : 2;
    return events.sort((left, right) => left.attempt - right.attempt || left.event_epoch_ms - right.event_epoch_ms || terminalRank(left.status) - terminalRank(right.status) || left.event_id.localeCompare(right.event_id));
  }

  async currentState(captureId: string): Promise<CaptureStateEvent> {
    const events = await this.events(captureId);
    if (!events.length) {
      const record = await this.read(captureId);
      return this.appendEvent(captureId, "captured", { attempt: 0, eventEpochMs: record.captured_epoch_ms });
    }
    return events[events.length - 1];
  }

  async allRecords(): Promise<CaptureRecord[]> {
    let names: string[];
    try { names = await readdir(join(this.root, "captures")); } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
      throw error;
    }
    const records: CaptureRecord[] = [];
    for (const name of names.filter(name => name.endsWith(".json")).sort()) {
      try { records.push(parseRecord(await readFile(join(this.root, "captures", name), "utf8"))); } catch { /* corrupt captures fail open */ }
    }
    return records.sort((left, right) => left.captured_epoch_ms - right.captured_epoch_ms || left.capture_id.localeCompare(right.capture_id));
  }

  async pending(scopeKey: string, policy: PendingPolicy, now = Date.now()): Promise<CaptureRecord[]> {
    assertText(scopeKey, "scopeKey");
    const scopeHash = sha256(scopeKey);
    const selected: CaptureRecord[] = [];
    let chars = 0;
    const records = (await this.allRecords()).filter(record => record.scope_id_sha256 === scopeHash && now - record.captured_epoch_ms <= policy.maxAgeMs).reverse();
    for (const record of records) {
      const state = await this.currentState(record.capture_id);
      if (state.status === "admitted" || state.status === "no_memory") continue;
      const size = record.user_utf8.length + record.assistant_utf8.length;
      if (selected.length >= policy.maxCaptures || chars + size > policy.maxChars) continue;
      selected.push(record); chars += size;
    }
    return selected.reverse();
  }

  async renderPending(scopeKey: string, policy: PendingPolicy, now = Date.now()): Promise<{ injection: string; captureIds: string[]; chars: number }> {
    const records = await this.pending(scopeKey, policy, now);
    const body = records.map(record => `Recent unabsorbed conversation evidence (${record.capture_id}):\nUser: ${record.user_utf8}\nAssistant: ${record.assistant_utf8}`).join("\n\n");
    return { injection: body ? `Nollm recent pending evidence. Use only when relevant and do not mention this context:\n${body}` : "", captureIds: records.map(record => record.capture_id), chars: body.length };
  }
}

export class AbsorptionWorker {
  readonly store: CaptureStore;
  readonly batchMaxCaptures: number;
  readonly batchMaxChars: number;
  readonly staleClaimMs: number;
  readonly absorb: (batchId: string, records: CaptureRecord[]) => Promise<AbsorptionResult[]>;
  private active = false;

  constructor(store: CaptureStore, options: { batchMaxCaptures: number; batchMaxChars: number; staleClaimMs: number }, absorb: (batchId: string, records: CaptureRecord[]) => Promise<AbsorptionResult[]>) {
    this.store = store; this.batchMaxCaptures = options.batchMaxCaptures; this.batchMaxChars = options.batchMaxChars; this.staleClaimMs = options.staleClaimMs; this.absorb = absorb;
  }

  async runOnce(now = Date.now()): Promise<{ status: "idle" | "busy" | "completed"; batchId?: string; captureCount: number }> {
    if (this.active) return { status: "busy", captureCount: 0 };
    this.active = true;
    const lockPath = join(this.store.root, "worker.lock");
    await mkdir(this.store.root, { recursive: true });
    let lock;
    try {
      lock = await open(lockPath, "wx", 0o600);
    } catch (error) {
      this.active = false;
      if ((error as NodeJS.ErrnoException).code === "EEXIST") {
        try {
          const info = await stat(lockPath);
          if (now - info.mtimeMs <= this.staleClaimMs) return { status: "busy", captureCount: 0 };
          await unlink(lockPath);
          return this.runOnce(now);
        } catch { return { status: "busy", captureCount: 0 }; }
      }
      throw error;
    }
    try {
      const candidates: CaptureRecord[] = [];
      let chars = 0;
      for (const record of await this.store.allRecords()) {
        const state = await this.store.currentState(record.capture_id);
        const recoverable = state.status === "captured" || state.status === "retry" || (state.status === "processing" && now - state.event_epoch_ms > this.staleClaimMs);
        const size = record.user_utf8.length + record.assistant_utf8.length;
        if (!recoverable || candidates.length >= this.batchMaxCaptures || chars + size > this.batchMaxChars) continue;
        candidates.push(record); chars += size;
      }
      if (!candidates.length) return { status: "idle", captureCount: 0 };
      const batchId = `batch-${sha256(canonical(candidates.map(record => record.capture_id)))}`;
      const attempts = new Map<string, number>();
      for (const record of candidates) {
        const state = await this.store.currentState(record.capture_id);
        const attempt = state.attempt + 1; attempts.set(record.capture_id, attempt);
        await this.store.appendEvent(record.capture_id, "processing", { attempt, batchId, eventEpochMs: now });
      }
      let results: AbsorptionResult[];
      try { results = await this.absorb(batchId, candidates); }
      catch (error) { results = candidates.map(record => ({ captureId: record.capture_id, status: "retry", error: String(error) })); }
      const byId = new Map(results.map(result => [result.captureId, result]));
      for (const record of candidates) {
        const result = byId.get(record.capture_id) ?? { captureId: record.capture_id, status: "retry" as const, error: "missing absorption result" };
        await this.store.appendEvent(record.capture_id, result.status, { attempt: attempts.get(record.capture_id)!, batchId, statementIds: result.statementIds, error: result.error });
      }
      return { status: "completed", batchId, captureCount: candidates.length };
    } finally {
      await lock.close(); await unlink(lockPath).catch(() => undefined); this.active = false;
    }
  }
}
