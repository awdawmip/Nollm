import { createHash, randomUUID } from "node:crypto";
import { link, mkdir, open, readFile, readdir, stat, unlink } from "node:fs/promises";
import { dirname, join } from "node:path";

export const CAPTURE_SCHEMA = "nollm_openclaw_durable_capture_v1";
export const CAPTURE_STATE_SCHEMA = "nollm_openclaw_capture_state_event_v1";
export const CAPTURE_PLUGIN_VERSION = "0.15.0";

export type CaptureInput = {
  scopeKey: string;
  workspaceKey?: string;
  sessionKey: string;
  turnIdentity: string;
  userUtf8: string;
  assistantUtf8: string;
  modelRef?: string;
  capturedEpochMs?: number;
  profileId?: string;
  mainRunIdentity?: string;
  endpointKind?: string;
  visibleEpochMs?: number;
  hostVersion?: string;
  pluginVersion?: string;
  timezoneOffsetMinutes?: number;
};

export type CaptureRecord = {
  schema_version: typeof CAPTURE_SCHEMA;
  capture_id: string;
  scope_id_sha256: string;
  workspace_id_sha256: string;
  session_key_sha256: string;
  turn_identity_sha256: string;
  main_run_id_sha256: string;
  profile_id: string;
  visible_endpoint_kind: string;
  visible_epoch_ms: number;
  captured_epoch_ms: number;
  content_sha256: string;
  user_role: "user";
  assistant_role: "assistant";
  turn_order: ["user", "assistant"];
  user_utf8: string;
  assistant_utf8: string;
  user_utf8_bytes: number;
  assistant_utf8_bytes: number;
  host_version: string;
  plugin_version: string;
  model_ref?: string;
  reference_timezone_offset_minutes?: number;
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
export type CaptureDiagnostic = { file: string; error: string };

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
  if (value.schema_version !== CAPTURE_SCHEMA || typeof value.capture_id !== "string" || typeof value.scope_id_sha256 !== "string" || typeof value.workspace_id_sha256 !== "string" ||
      typeof value.session_key_sha256 !== "string" || typeof value.turn_identity_sha256 !== "string" ||
      typeof value.main_run_id_sha256 !== "string" || typeof value.profile_id !== "string" ||
      typeof value.visible_endpoint_kind !== "string" || typeof value.visible_epoch_ms !== "number" ||
      typeof value.captured_epoch_ms !== "number" || typeof value.content_sha256 !== "string" ||
      value.user_role !== "user" || value.assistant_role !== "assistant" || !Array.isArray(value.turn_order) || value.turn_order.join("\0") !== "user\0assistant" ||
      typeof value.user_utf8 !== "string" || typeof value.assistant_utf8 !== "string" ||
      value.user_utf8_bytes !== Buffer.byteLength(value.user_utf8, "utf8") || value.assistant_utf8_bytes !== Buffer.byteLength(value.assistant_utf8, "utf8") ||
      typeof value.host_version !== "string" || typeof value.plugin_version !== "string" ||
      (value.model_ref !== undefined && typeof value.model_ref !== "string") ||
      (value.reference_timezone_offset_minutes !== undefined && (!Number.isInteger(value.reference_timezone_offset_minutes) || value.reference_timezone_offset_minutes < -840 || value.reference_timezone_offset_minutes > 840))) throw new Error("invalid Capture record");
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
    const profileId = input.profileId ?? "default";
    const mainRunIdentity = input.mainRunIdentity ?? input.turnIdentity;
    const endpointKind = input.endpointKind ?? "visible_assistant_delivery";
    const hostVersion = input.hostVersion ?? "unknown";
    const pluginVersion = input.pluginVersion ?? CAPTURE_PLUGIN_VERSION;
    assertText(profileId, "profileId"); assertText(mainRunIdentity, "mainRunIdentity"); assertText(endpointKind, "endpointKind");
    assertText(hostVersion, "hostVersion"); assertText(pluginVersion, "pluginVersion");
    const scopeHash = sha256(input.scopeKey);
    const workspaceHash = sha256(input.workspaceKey ?? input.scopeKey);
    const sessionHash = sha256(input.sessionKey);
    const turnHash = sha256(input.turnIdentity);
    const contentHash = sha256(canonical({ user_utf8: input.userUtf8, assistant_utf8: input.assistantUtf8 }));
    const captureId = `capture-${sha256(canonical({ scope_id_sha256: scopeHash, workspace_id_sha256: workspaceHash, turn_identity_sha256: turnHash }))}`;
    try {
      const existing = await this.read(captureId);
      if (existing.scope_id_sha256 !== scopeHash || existing.workspace_id_sha256 !== workspaceHash || existing.session_key_sha256 !== sessionHash || existing.turn_identity_sha256 !== turnHash || existing.content_sha256 !== contentHash || existing.user_utf8 !== input.userUtf8 || existing.assistant_utf8 !== input.assistantUtf8) {
        throw new Error(`immutable Capture conflict: ${captureId}`);
      }
      return { record: existing, replayed: true, publish_ms: performance.now() - started };
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
    const record: CaptureRecord = {
      schema_version: CAPTURE_SCHEMA, capture_id: captureId, scope_id_sha256: scopeHash, workspace_id_sha256: workspaceHash,
      session_key_sha256: sessionHash, turn_identity_sha256: turnHash,
      main_run_id_sha256: sha256(mainRunIdentity), profile_id: profileId,
      visible_endpoint_kind: endpointKind, visible_epoch_ms: input.visibleEpochMs ?? input.capturedEpochMs ?? Date.now(),
      captured_epoch_ms: input.capturedEpochMs ?? Date.now(), content_sha256: contentHash,
      user_role: "user", assistant_role: "assistant", turn_order: ["user", "assistant"],
      user_utf8: input.userUtf8, assistant_utf8: input.assistantUtf8,
      user_utf8_bytes: Buffer.byteLength(input.userUtf8, "utf8"), assistant_utf8_bytes: Buffer.byteLength(input.assistantUtf8, "utf8"),
      host_version: hostVersion, plugin_version: pluginVersion, model_ref: input.modelRef,
      reference_timezone_offset_minutes: input.timezoneOffsetMinutes ?? -new Date(input.capturedEpochMs ?? Date.now()).getTimezoneOffset(),
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

  async scanRecords(): Promise<{ records: CaptureRecord[]; diagnostics: CaptureDiagnostic[] }> {
    let names: string[];
    try { names = await readdir(join(this.root, "captures")); } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return { records: [], diagnostics: [] };
      throw error;
    }
    const records: CaptureRecord[] = [];
    const diagnostics: CaptureDiagnostic[] = [];
    for (const name of names.filter(name => name.endsWith(".json")).sort()) {
      try { records.push(parseRecord(await readFile(join(this.root, "captures", name), "utf8"))); }
      catch (error) { diagnostics.push({ file: name, error: String(error) }); }
    }
    records.sort((left, right) => left.captured_epoch_ms - right.captured_epoch_ms || left.capture_id.localeCompare(right.capture_id));
    return { records, diagnostics };
  }

  async allRecords(): Promise<CaptureRecord[]> {
    return (await this.scanRecords()).records;
  }

  async pending(scopeKey: string, policy: PendingPolicy, now = Date.now()): Promise<CaptureRecord[]> {
    assertText(scopeKey, "scopeKey");
    const scopeHash = sha256(scopeKey);
    const selected: CaptureRecord[] = [];
    let chars = 0;
    const records = (await this.allRecords()).filter(record => record.scope_id_sha256 === scopeHash && now - record.captured_epoch_ms <= policy.maxAgeMs).reverse();
    for (const record of records) {
      const state = await this.currentState(record.capture_id);
      if (state.status === "admitted" || state.status === "no_memory" || state.status === "deferred") continue;
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
  readonly retryBackoffMs: number;
  readonly absorb: (batchId: string, records: CaptureRecord[], executionId: string) => Promise<AbsorptionResult[]>;
  private active = false;

  constructor(store: CaptureStore, options: { batchMaxCaptures: number; batchMaxChars: number; staleClaimMs: number; retryBackoffMs?: number }, absorb: (batchId: string, records: CaptureRecord[], executionId: string) => Promise<AbsorptionResult[]>) {
    this.store = store; this.batchMaxCaptures = options.batchMaxCaptures; this.batchMaxChars = options.batchMaxChars; this.staleClaimMs = options.staleClaimMs; this.retryBackoffMs = options.retryBackoffMs ?? 1000; this.absorb = absorb;
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
      const available = await Promise.all((await this.store.allRecords()).map(async record => ({ record, state: await this.store.currentState(record.capture_id) })));
      const retryReady = ({ state }: typeof available[number]): boolean => {
        if (state.status !== "retry") return false;
        const delay = Math.min(this.staleClaimMs, this.retryBackoffMs * (2 ** Math.max(0, state.attempt - 1)));
        return now - state.event_epoch_ms >= delay;
      };
      const retryBatchId = available.find(item => retryReady(item) && item.state.batch_id)?.state.batch_id;
      const freshAnchor = retryBatchId ? undefined : available.find(({ state }) => state.status === "captured" || (state.status === "processing" && now - state.event_epoch_ms > this.staleClaimMs));
      const candidates: CaptureRecord[] = [];
      let chars = 0;
      for (const { record, state } of available) {
        const recoverable = retryBatchId
          ? retryReady({ record, state }) && state.batch_id === retryBatchId
          : state.status === "captured" || (state.status === "processing" && now - state.event_epoch_ms > this.staleClaimMs);
        if (freshAnchor && (record.scope_id_sha256 !== freshAnchor.record.scope_id_sha256 || record.workspace_id_sha256 !== freshAnchor.record.workspace_id_sha256 || record.profile_id !== freshAnchor.record.profile_id)) continue;
        const size = record.user_utf8.length + record.assistant_utf8.length;
        if (!recoverable || candidates.length >= this.batchMaxCaptures || chars + size > this.batchMaxChars) continue;
        candidates.push(record); chars += size;
      }
      if (!candidates.length) return { status: "idle", captureCount: 0 };
      const batchId = retryBatchId ?? `batch-${sha256(canonical(candidates.map(record => record.capture_id)))}`;
      const attempts = new Map<string, number>();
      for (const record of candidates) {
        const state = await this.store.currentState(record.capture_id);
        const attempt = state.attempt + 1; attempts.set(record.capture_id, attempt);
        await this.store.appendEvent(record.capture_id, "processing", { attempt, batchId, eventEpochMs: now });
      }
      const executionId = sha256(canonical(candidates.map(record => [record.capture_id, attempts.get(record.capture_id)])));
      let results: AbsorptionResult[];
      try { results = await this.absorb(batchId, candidates, executionId); }
      catch (error) { results = candidates.map(record => ({ captureId: record.capture_id, status: "retry", error: String(error) })); }
      const byId = new Map(results.map(result => [result.captureId, result]));
      for (const record of candidates) {
        const result = byId.get(record.capture_id) ?? { captureId: record.capture_id, status: "retry" as const, error: "missing absorption result" };
        await this.store.appendEvent(record.capture_id, result.status, { attempt: attempts.get(record.capture_id)!, batchId, statementIds: result.statementIds, error: result.error, eventEpochMs: now });
      }
      return { status: "completed", batchId, captureCount: candidates.length };
    } finally {
      await lock.close(); await unlink(lockPath).catch(() => undefined); this.active = false;
    }
  }
}
