import { createHash, randomUUID } from "node:crypto";
import { link, mkdir, open, readFile, readdir, stat, unlink } from "node:fs/promises";
import { dirname, join } from "node:path";

export const CAPTURE_SCHEMA = "nollm_openclaw_durable_capture_v1";
export const LEGACY_CAPTURE_STATE_SCHEMA = "nollm_openclaw_capture_state_event_v1";
export const CAPTURE_STATE_SCHEMA = "nollm_openclaw_capture_state_event_v2";
export const CAPTURE_DIRECTIVE_SCHEMA = "nollm_openclaw_capture_absorption_directive_v1";
export const CAPTURE_PLUGIN_VERSION = "0.17.0";

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

export type MemoryToolAction = "surface" | "open_region" | "recall" | "expand" | "none";
export type AssistantRoleMode = "source" | "context_only" | "memory_derived";
export type CaptureAbsorptionDirective = {
  schema_version: typeof CAPTURE_DIRECTIVE_SCHEMA;
  directive_id: string;
  capture_id: string;
  main_run_id_sha256: string;
  user_role_mode: "source";
  assistant_role_mode: AssistantRoleMode;
  memory_tool_actions: MemoryToolAction[];
  selected_entry_id_sha256?: string;
  recalled_statement_ids: string[];
  directive_epoch_ms: number;
  sequence: number;
  finalized: boolean;
  finalization_reason: "hook" | "safe_default_missing" | "safe_default_timeout";
};

export type CaptureDirectiveInput = {
  captureId: string;
  mainRunIdentity: string;
  assistantRoleMode: AssistantRoleMode;
  memoryToolActions?: MemoryToolAction[];
  selectedEntryId?: string;
  recalledStatementIds?: string[];
  directiveEpochMs?: number;
  sequence: number;
  finalized: boolean;
  finalizationReason?: CaptureAbsorptionDirective["finalization_reason"];
};

export type CaptureStatus = "captured" | "processing" | "retryable_defer" | "retryable_defer_legacy" |
  "evaluated_no_new_propositions" | "evaluated_no_new_propositions_legacy" | "incomplete_continuation" |
  "structural_invalid" | "admitted" | "reused" | "revised";
export type CaptureEvaluationIdentity = {
  writer_schema: string;
  prompt_version: string;
  context_fingerprint: string;
  current_memory_fingerprint: string;
  source_coverage: string;
  evaluation_epoch_ms: number;
};
export type CaptureContinuation = {
  group_index: number;
  pass_index: number;
  total_groups: number;
  covered_ranges: Array<{ capture_id: string; role: "user" | "assistant"; start: number; end: number }>;
  uncovered_ranges: Array<{ capture_id: string; role: "user" | "assistant"; start: number; end: number }>;
};
export type CaptureStateEvent = {
  schema_version: typeof CAPTURE_STATE_SCHEMA | typeof LEGACY_CAPTURE_STATE_SCHEMA;
  event_id: string;
  capture_id: string;
  status: CaptureStatus;
  event_epoch_ms: number;
  attempt: number;
  batch_id?: string;
  statement_ids?: string[];
  error?: string;
  evaluation?: CaptureEvaluationIdentity;
  continuation?: CaptureContinuation;
};

export type PendingPolicy = { maxCaptures: number; maxChars: number; maxAgeMs: number };
export type AbsorptionResult = { captureId: string; status: Exclude<CaptureStatus, "captured" | "processing" | "retryable_defer_legacy" | "evaluated_no_new_propositions_legacy">; statementIds?: string[]; error?: string; evaluation?: CaptureEvaluationIdentity; continuation?: CaptureContinuation };
export type CaptureDiagnostic = { file: string; error: string };
export type CaptureQueueDiagnostic = {
  state_counts: Record<CaptureStatus, number>;
  pending_capture_count: number;
  oldest_pending_age_ms: number | null;
  next_retry_epoch_ms: number | null;
  stale_processing_count: number;
};

export type CaptureSourceWindow = {
  capture_id: string;
  role: "user" | "assistant";
  start: number;
  end: number;
  text_utf8: string;
  window_index: number;
  window_count: number;
};

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

export function buildCaptureSourceWindowGroups(
  records: CaptureRecord[],
  maxWindowBytes = 12000,
  maxGroupBytes = 32000,
  overlapCodepoints = 128,
): CaptureSourceWindow[][] {
  if (!records.length || !Number.isInteger(maxWindowBytes) || maxWindowBytes < 1024 ||
      !Number.isInteger(maxGroupBytes) || maxGroupBytes < maxWindowBytes ||
      !Number.isInteger(overlapCodepoints) || overlapCodepoints < 0) throw new TypeError("source window budgets are invalid");
  const windows: CaptureSourceWindow[] = [];
  for (const record of records) for (const role of ["user", "assistant"] as const) {
    const points = [...record[`${role}_utf8`]];
    if (!points.length) continue;
    const roleWindows: Omit<CaptureSourceWindow, "window_index" | "window_count">[] = [];
    let start = 0;
    while (start < points.length) {
      let end = start;
      let bytes = 0;
      while (end < points.length) {
        const pointBytes = Buffer.byteLength(points[end], "utf8");
        if (end > start && bytes + pointBytes > maxWindowBytes) break;
        bytes += pointBytes; end += 1;
      }
      roleWindows.push({ capture_id: record.capture_id, role, start, end, text_utf8: points.slice(start, end).join("") });
      if (end === points.length) break;
      const next = Math.max(start + 1, end - overlapCodepoints);
      start = next;
    }
    roleWindows.forEach((window, index) => windows.push({ ...window, window_index: index, window_count: roleWindows.length }));
  }
  const groups: CaptureSourceWindow[][] = [];
  let current: CaptureSourceWindow[] = [];
  let bytes = 0;
  for (const window of windows) {
    const size = Buffer.byteLength(window.text_utf8, "utf8");
    if (current.length && bytes + size > maxGroupBytes) { groups.push(current); current = []; bytes = 0; }
    current.push(window); bytes += size;
  }
  if (current.length) groups.push(current);
  return groups;
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
  const legacyStatuses = ["captured", "processing", "retry", "deferred", "no_memory", "admitted"];
  const currentStatuses: CaptureStatus[] = ["captured", "processing", "retryable_defer", "retryable_defer_legacy", "evaluated_no_new_propositions", "evaluated_no_new_propositions_legacy", "incomplete_continuation", "structural_invalid", "admitted", "reused", "revised"];
  if (![CAPTURE_STATE_SCHEMA, LEGACY_CAPTURE_STATE_SCHEMA].includes(value.schema_version) || typeof value.event_id !== "string" || typeof value.capture_id !== "string" ||
      !(value.schema_version === LEGACY_CAPTURE_STATE_SCHEMA ? legacyStatuses : currentStatuses).includes(value.status) ||
      typeof value.event_epoch_ms !== "number" || typeof value.attempt !== "number") throw new Error("invalid Capture state event");
  return value;
}

function parseDirective(text: string): CaptureAbsorptionDirective {
  const value = JSON.parse(text) as CaptureAbsorptionDirective;
  const actions = ["surface", "open_region", "recall", "expand", "none"];
  const sortedActions = [...(value.memory_tool_actions ?? [])].sort();
  const sortedStatements = [...(value.recalled_statement_ids ?? [])].sort();
  if (value.schema_version !== CAPTURE_DIRECTIVE_SCHEMA || typeof value.directive_id !== "string" ||
      typeof value.capture_id !== "string" || typeof value.main_run_id_sha256 !== "string" ||
      value.user_role_mode !== "source" || !["source", "context_only", "memory_derived"].includes(value.assistant_role_mode) ||
      !Array.isArray(value.memory_tool_actions) || value.memory_tool_actions.some(item => !actions.includes(item)) ||
      new Set(value.memory_tool_actions).size !== value.memory_tool_actions.length || value.memory_tool_actions.join("\0") !== sortedActions.join("\0") ||
      (value.selected_entry_id_sha256 !== undefined && typeof value.selected_entry_id_sha256 !== "string") ||
      !Array.isArray(value.recalled_statement_ids) || value.recalled_statement_ids.some(item => typeof item !== "string") ||
      new Set(value.recalled_statement_ids).size !== value.recalled_statement_ids.length || value.recalled_statement_ids.join("\0") !== sortedStatements.join("\0") ||
      !Number.isInteger(value.directive_epoch_ms) || !Number.isInteger(value.sequence) || value.sequence < 0 ||
      typeof value.finalized !== "boolean" || !["hook", "safe_default_missing", "safe_default_timeout"].includes(value.finalization_reason)) {
    throw new Error("invalid Capture absorption directive");
  }
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
  directiveDirectory(captureId: string): string { return join(this.root, "directives", captureId); }

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

  async publishDirective(input: CaptureDirectiveInput): Promise<{ directive: CaptureAbsorptionDirective; replayed: boolean }> {
    assertText(input.captureId, "captureId"); assertText(input.mainRunIdentity, "mainRunIdentity");
    if (!Number.isInteger(input.sequence) || input.sequence < 0) throw new TypeError("directive sequence is invalid");
    const record = await this.read(input.captureId);
    const runHash = sha256(input.mainRunIdentity);
    if (record.main_run_id_sha256 !== runHash) throw new Error("Capture directive run identity mismatch");
    const actions = [...new Set(input.memoryToolActions ?? [])].sort() as MemoryToolAction[];
    const statementIds = [...new Set(input.recalledStatementIds ?? [])].sort();
    const base = {
      capture_id: input.captureId, main_run_id_sha256: runHash, user_role_mode: "source" as const,
      assistant_role_mode: input.assistantRoleMode, memory_tool_actions: actions,
      selected_entry_id_sha256: input.selectedEntryId ? sha256(input.selectedEntryId) : undefined,
      recalled_statement_ids: statementIds, directive_epoch_ms: input.directiveEpochMs ?? Date.now(),
      sequence: input.sequence, finalized: input.finalized,
      finalization_reason: input.finalizationReason ?? "hook" as const,
    };
    const directiveId = `directive-${sha256(canonical(base))}`;
    const directive: CaptureAbsorptionDirective = { schema_version: CAPTURE_DIRECTIVE_SCHEMA, directive_id: directiveId, ...base };
    const result = await publishImmutable(join(this.directiveDirectory(input.captureId), `${directiveId}.json`), canonical(directive));
    return { directive, replayed: result === "replayed" };
  }

  async directives(captureId: string): Promise<CaptureAbsorptionDirective[]> {
    let names: string[];
    try { names = await readdir(this.directiveDirectory(captureId)); } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
      throw error;
    }
    const values = await Promise.all(names.filter(name => name.endsWith(".json")).map(async name =>
      parseDirective(await readFile(join(this.directiveDirectory(captureId), name), "utf8"))));
    return values.sort((left, right) => left.sequence - right.sequence || left.directive_epoch_ms - right.directive_epoch_ms || left.directive_id.localeCompare(right.directive_id));
  }

  async directive(captureId: string): Promise<CaptureAbsorptionDirective | undefined> {
    return (await this.directives(captureId)).at(-1);
  }

  async directiveForAbsorption(record: CaptureRecord, now: number, finalizationGraceMs: number): Promise<CaptureAbsorptionDirective | undefined> {
    const current = await this.directive(record.capture_id);
    if (current?.finalized) return current;
    if (current && now - record.captured_epoch_ms < finalizationGraceMs) return undefined;
    const fallback = await this.publishDirective({
      captureId: record.capture_id, mainRunIdentity: record.main_run_id_sha256,
      assistantRoleMode: "context_only", memoryToolActions: [], recalledStatementIds: [],
      directiveEpochMs: record.captured_epoch_ms + finalizationGraceMs,
      sequence: (current?.sequence ?? -1) + 1, finalized: true,
      finalizationReason: current ? "safe_default_timeout" : "safe_default_missing",
    }).catch(async error => {
      // Legacy records expose only the run digest. Build the same safe fallback without mutating the Raw Capture.
      if (!String(error).includes("run identity mismatch")) throw error;
      const base = {
        capture_id: record.capture_id, main_run_id_sha256: record.main_run_id_sha256, user_role_mode: "source" as const,
        assistant_role_mode: "context_only" as const, memory_tool_actions: [] as MemoryToolAction[],
        selected_entry_id_sha256: undefined, recalled_statement_ids: [] as string[],
        directive_epoch_ms: record.captured_epoch_ms + finalizationGraceMs, sequence: (current?.sequence ?? -1) + 1,
        finalized: true, finalization_reason: current ? "safe_default_timeout" as const : "safe_default_missing" as const,
      };
      const directiveId = `directive-${sha256(canonical(base))}`;
      const directive: CaptureAbsorptionDirective = { schema_version: CAPTURE_DIRECTIVE_SCHEMA, directive_id: directiveId, ...base };
      const result = await publishImmutable(join(this.directiveDirectory(record.capture_id), `${directiveId}.json`), canonical(directive));
      return { directive, replayed: result === "replayed" };
    });
    return fallback.directive;
  }

  async appendEvent(captureId: string, status: CaptureStatus, options: { attempt: number; eventEpochMs?: number; batchId?: string; statementIds?: string[]; error?: string; evaluation?: CaptureEvaluationIdentity; continuation?: CaptureContinuation }): Promise<CaptureStateEvent> {
    const base = { capture_id: captureId, status, event_epoch_ms: options.eventEpochMs ?? Date.now(), attempt: options.attempt,
      batch_id: options.batchId, statement_ids: options.statementIds, error: options.error,
      evaluation: options.evaluation, continuation: options.continuation };
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
    const terminalRank = (status: string): number => status === "processing" ? 1 : status === "captured" ? 0 : 2;
    return events.sort((left, right) => left.attempt - right.attempt || left.event_epoch_ms - right.event_epoch_ms || terminalRank(left.status) - terminalRank(right.status) || left.event_id.localeCompare(right.event_id));
  }

  async currentState(captureId: string): Promise<CaptureStateEvent> {
    const events = await this.events(captureId);
    if (!events.length) {
      const record = await this.read(captureId);
      return this.appendEvent(captureId, "captured", { attempt: 0, eventEpochMs: record.captured_epoch_ms });
    }
    const current = events[events.length - 1];
    if (current.schema_version === LEGACY_CAPTURE_STATE_SCHEMA && (current.status as string) === "no_memory") {
      return this.appendEvent(captureId, "evaluated_no_new_propositions_legacy", {
        attempt: current.attempt, batchId: current.batch_id, statementIds: current.statement_ids,
        eventEpochMs: current.event_epoch_ms + 1,
        evaluation: {
          writer_schema: "legacy_no_memory", prompt_version: "legacy_unknown",
          context_fingerprint: sha256("legacy-context"), current_memory_fingerprint: sha256("legacy-memory-unobserved"),
          source_coverage: "legacy_unverified", evaluation_epoch_ms: current.event_epoch_ms,
        },
      });
    }
    if (current.schema_version === LEGACY_CAPTURE_STATE_SCHEMA && (current.status as string) === "deferred") {
      return this.appendEvent(captureId, "retryable_defer_legacy", {
        attempt: current.attempt, batchId: current.batch_id, statementIds: current.statement_ids,
        error: current.error ?? "legacy deferred outcome requires retry", eventEpochMs: current.event_epoch_ms + 1,
      });
    }
    if (current.schema_version === LEGACY_CAPTURE_STATE_SCHEMA && (current.status as string) === "retry") {
      return this.appendEvent(captureId, "retryable_defer", {
        attempt: current.attempt, batchId: current.batch_id, statementIds: current.statement_ids,
        error: current.error ?? "legacy retry", eventEpochMs: current.event_epoch_ms + 1,
      });
    }
    return current;
  }

  async requestReevaluation(captureId: string, reason: string, now = Date.now()): Promise<CaptureStateEvent> {
    assertText(reason, "reevaluation reason");
    const current = await this.currentState(captureId);
    return this.appendEvent(captureId, "captured", {
      attempt: current.attempt, eventEpochMs: now, error: `re-evaluate:${reason}`,
    });
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

  async contextBefore(sources: CaptureRecord[], maxCaptures = 4, maxChars = 6000): Promise<CaptureRecord[]> {
    if (!sources.length || !Number.isInteger(maxCaptures) || maxCaptures < 0 || !Number.isInteger(maxChars) || maxChars < 0) {
      throw new TypeError("context source and budgets are invalid");
    }
    const anchor = sources[0];
    if (sources.some(record =>
      record.scope_id_sha256 !== anchor.scope_id_sha256 ||
      record.workspace_id_sha256 !== anchor.workspace_id_sha256 ||
      record.session_key_sha256 !== anchor.session_key_sha256 ||
      record.profile_id !== anchor.profile_id
    )) throw new Error("one absorption batch must belong to one session partition");
    const sourceIds = new Set(sources.map(record => record.capture_id));
    const firstSource = [...sources].sort((left, right) =>
      left.captured_epoch_ms - right.captured_epoch_ms || left.capture_id.localeCompare(right.capture_id)
    )[0];
    const candidates = (await this.allRecords()).filter(record =>
      !sourceIds.has(record.capture_id) &&
      record.scope_id_sha256 === anchor.scope_id_sha256 &&
      record.workspace_id_sha256 === anchor.workspace_id_sha256 &&
      record.session_key_sha256 === anchor.session_key_sha256 &&
      record.profile_id === anchor.profile_id &&
      (record.captured_epoch_ms < firstSource.captured_epoch_ms ||
        (record.captured_epoch_ms === firstSource.captured_epoch_ms && record.capture_id < firstSource.capture_id))
    );
    const selected: CaptureRecord[] = [];
    let chars = 0;
    for (const record of candidates.reverse()) {
      const size = record.user_utf8.length + record.assistant_utf8.length;
      if (selected.length >= maxCaptures || chars + size > maxChars) continue;
      selected.push(record); chars += size;
    }
    return selected.reverse();
  }

  async pending(scopeKey: string, policy: PendingPolicy, now = Date.now()): Promise<CaptureRecord[]> {
    assertText(scopeKey, "scopeKey");
    const scopeHash = sha256(scopeKey);
    const selected: CaptureRecord[] = [];
    let chars = 0;
    const records = (await this.allRecords()).filter(record => record.scope_id_sha256 === scopeHash && now - record.captured_epoch_ms <= policy.maxAgeMs).reverse();
    for (const record of records) {
      const state = await this.currentState(record.capture_id);
      if (["admitted", "reused", "revised", "evaluated_no_new_propositions", "evaluated_no_new_propositions_legacy", "structural_invalid"].includes(state.status)) continue;
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

  async diagnose(now = Date.now(), retryBackoffMs = 1000, staleClaimMs = 300000): Promise<CaptureQueueDiagnostic> {
    const records = await this.allRecords();
    const states = await Promise.all(records.map(record => this.currentState(record.capture_id)));
    const stateCounts = Object.fromEntries([
      "captured", "processing", "retryable_defer", "retryable_defer_legacy", "evaluated_no_new_propositions",
      "evaluated_no_new_propositions_legacy", "incomplete_continuation", "structural_invalid", "admitted", "reused", "revised",
    ].map(status => [status, 0])) as Record<CaptureStatus, number>;
    const pendingAges: number[] = [];
    const retryTimes: number[] = [];
    let staleProcessingCount = 0;
    for (let index = 0; index < records.length; index += 1) {
      const state = states[index];
      stateCounts[state.status] += 1;
      if (["captured", "processing", "retryable_defer", "retryable_defer_legacy", "incomplete_continuation"].includes(state.status)) pendingAges.push(Math.max(0, now - records[index].captured_epoch_ms));
      if (state.status === "processing" && now - state.event_epoch_ms > staleClaimMs) staleProcessingCount += 1;
      if (state.status === "retryable_defer" || state.status === "retryable_defer_legacy" || state.status === "incomplete_continuation") {
        const delay = Math.min(staleClaimMs, retryBackoffMs * (2 ** Math.max(0, state.attempt - 1)));
        retryTimes.push(state.event_epoch_ms + delay);
      }
    }
    return {
      state_counts: stateCounts,
      pending_capture_count: pendingAges.length,
      oldest_pending_age_ms: pendingAges.length ? Math.max(...pendingAges) : null,
      next_retry_epoch_ms: retryTimes.length ? Math.min(...retryTimes) : null,
      stale_processing_count: staleProcessingCount,
    };
  }
}

export class AbsorptionWorker {
  readonly store: CaptureStore;
  readonly batchMaxCaptures: number;
  readonly batchMaxChars: number;
  readonly staleClaimMs: number;
  readonly retryBackoffMs: number;
  readonly directiveFinalizationMs: number;
  readonly reevaluationNeeded: (record: CaptureRecord, state: CaptureStateEvent) => Promise<boolean>;
  readonly absorb: (batchId: string, records: CaptureRecord[], executionId: string) => Promise<AbsorptionResult[]>;
  private active = false;

  constructor(store: CaptureStore, options: { batchMaxCaptures: number; batchMaxChars: number; staleClaimMs: number; retryBackoffMs?: number; directiveFinalizationMs?: number; reevaluationNeeded?: (record: CaptureRecord, state: CaptureStateEvent) => Promise<boolean> }, absorb: (batchId: string, records: CaptureRecord[], executionId: string) => Promise<AbsorptionResult[]>) {
    this.store = store; this.batchMaxCaptures = options.batchMaxCaptures; this.batchMaxChars = options.batchMaxChars; this.staleClaimMs = options.staleClaimMs; this.retryBackoffMs = options.retryBackoffMs ?? 1000; this.directiveFinalizationMs = options.directiveFinalizationMs ?? 30000; this.reevaluationNeeded = options.reevaluationNeeded ?? (async () => false); this.absorb = absorb;
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
      const available = (await Promise.all((await this.store.allRecords()).map(async record => ({
        record, state: await this.store.currentState(record.capture_id),
        directive: await this.store.directiveForAbsorption(record, now, this.directiveFinalizationMs),
        reevaluation: false,
      }))));
      for (const item of available) if (["evaluated_no_new_propositions", "evaluated_no_new_propositions_legacy"].includes(item.state.status)) {
        item.reevaluation = await this.reevaluationNeeded(item.record, item.state);
      }
      const ready = available.filter(item => item.directive?.finalized === true);
      const retryReady = ({ state }: { state: CaptureStateEvent }): boolean => {
        if (!["retryable_defer", "retryable_defer_legacy", "incomplete_continuation"].includes(state.status)) return false;
        if (state.status === "incomplete_continuation") return true;
        const delay = Math.min(this.staleClaimMs, this.retryBackoffMs * (2 ** Math.max(0, state.attempt - 1)));
        return now - state.event_epoch_ms >= delay;
      };
      const staleProcessing = ({ state }: { state: CaptureStateEvent }): boolean => state.status === "processing" && now - state.event_epoch_ms > this.staleClaimMs;
      const recoveryBatchId = ready.find(item => (retryReady(item) || staleProcessing(item)) && item.state.batch_id)?.state.batch_id;
      const freshAnchor = recoveryBatchId ? undefined : ready.find(({ state, reevaluation }) => state.status === "captured" || reevaluation);
      const candidates: CaptureRecord[] = [];
      let chars = 0;
      for (const { record, state, reevaluation } of ready) {
        const recoverable = recoveryBatchId
          ? (retryReady({ state }) || staleProcessing({ state })) && state.batch_id === recoveryBatchId
          : state.status === "captured" || reevaluation;
        if (freshAnchor && (record.scope_id_sha256 !== freshAnchor.record.scope_id_sha256 || record.workspace_id_sha256 !== freshAnchor.record.workspace_id_sha256 || record.session_key_sha256 !== freshAnchor.record.session_key_sha256 || record.profile_id !== freshAnchor.record.profile_id)) continue;
        const size = record.user_utf8.length + record.assistant_utf8.length;
        if (!recoverable || candidates.length >= this.batchMaxCaptures) continue;
        if (chars + size > this.batchMaxChars) {
          if (!candidates.length) { candidates.push(record); chars = size; }
          continue;
        }
        candidates.push(record); chars += size;
      }
      if (!candidates.length) return { status: "idle", captureCount: 0 };
      const batchId = recoveryBatchId ?? `batch-${sha256(canonical(candidates.map(record => record.capture_id)))}`;
      const attempts = new Map<string, number>();
      for (const record of candidates) {
        const state = await this.store.currentState(record.capture_id);
        const attempt = state.attempt + 1; attempts.set(record.capture_id, attempt);
        await this.store.appendEvent(record.capture_id, "processing", { attempt, batchId, eventEpochMs: now });
      }
      const executionId = sha256(canonical(candidates.map(record => [record.capture_id, attempts.get(record.capture_id)])));
      let results: AbsorptionResult[];
      try { results = await this.absorb(batchId, candidates, executionId); }
      catch (error) { results = candidates.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: String(error) })); }
      const byId = new Map(results.map(result => [result.captureId, result]));
      for (const record of candidates) {
        const result = byId.get(record.capture_id) ?? { captureId: record.capture_id, status: "retryable_defer" as const, error: "missing absorption result" };
        await this.store.appendEvent(record.capture_id, result.status, {
          attempt: attempts.get(record.capture_id)!, batchId, statementIds: result.statementIds,
          error: result.error, evaluation: result.evaluation, continuation: result.continuation, eventEpochMs: now,
        });
      }
      return { status: "completed", batchId, captureCount: candidates.length };
    } finally {
      await lock.close(); await unlink(lockPath).catch(() => undefined); this.active = false;
    }
  }
}
