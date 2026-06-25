import { randomBytes } from "node:crypto";

interface RegistryEntry {
  agentId: string;
  managerScope: string;
  managerGeneration: number;
  fieldId: string;
  fieldRevisionId: string;
  shardId: string;
  boundedExcerpt: string;
  expiresAt: number;
  queryHash: string;
}

const REF_PREFIX = "nollm://compat/v1/";
const REF_TTL_MS = 5 * 60 * 1000;

export class NollmCompatibilityReferenceRegistry {
  private entries = new Map<string, RegistryEntry>();
  private generation = 0;

  nextGeneration(): number {
    this.generation++;
    return this.generation;
  }

  issueRef(params: {
    agentId: string;
    managerScope: string;
    managerGeneration: number;
    fieldId: string;
    fieldRevisionId: string;
    shardId: string;
    boundedExcerpt: string;
    queryHash: string;
  }): string {
    const nonce = randomBytes(16).toString("hex");
    const ref = REF_PREFIX + nonce;
    this.entries.set(nonce, {
      agentId: params.agentId,
      managerScope: params.managerScope,
      managerGeneration: params.managerGeneration ?? 0,
      fieldId: params.fieldId,
      fieldRevisionId: params.fieldRevisionId,
      shardId: params.shardId,
      boundedExcerpt: params.boundedExcerpt.slice(0, 240),
      expiresAt: Date.now() + REF_TTL_MS,
      queryHash: params.queryHash,
    });
    return ref;
  }

  resolveRef(ref: string, opts: {
    agentId: string;
    managerScope: string;
    managerGeneration: number;
    fieldRevisionId: string;
  }): { excerpt: string; shardId: string } | null {
    if (!ref.startsWith(REF_PREFIX)) return null;
    const nonce = ref.slice(REF_PREFIX.length);
    const entry = this.entries.get(nonce);
    if (!entry) return null;
    if (entry.agentId !== opts.agentId) return null;
    if (entry.managerScope !== opts.managerScope) return null;
    if (entry.managerGeneration !== (opts.managerGeneration ?? 0)) return null;
    if (entry.fieldRevisionId !== opts.fieldRevisionId) return null;
    if (Date.now() > entry.expiresAt) {
      this.entries.delete(nonce);
      return null;
    }
    return { excerpt: entry.boundedExcerpt, shardId: entry.shardId };
  }

  isIssuedRef(ref: string): boolean {
    if (!ref.startsWith(REF_PREFIX)) return false;
    const nonce = ref.slice(REF_PREFIX.length);
    return this.entries.has(nonce);
  }

  clear(): void {
    this.entries.clear();
    this.generation = 0;
  }
}
