import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { normalizeConfig } from "../dist/config.js";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import {
  makeProviderConfig,
  makeTempDir,
  writeStubSidecar,
  STUB_STATUS,
} from "./helpers.mjs";

describe("E5 config segment-aware legacy path rejection", () => {
  it("/tmp/x/memory rejected", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    cfg.nollmDataRoot = path.join(os.tmpdir(), "test", "memory");
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    assert.throws(() => normalizeConfig(cfg), /legacy memory path/i);
  });

  it("/tmp/nollm-memory-alpha accepted", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    cfg.nollmDataRoot = path.join(os.tmpdir(), "nollm-memory-alpha-test");
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    fs.mkdirSync(cfg.nollmDataRoot, { recursive: true });
    assert.doesNotThrow(() => normalizeConfig(cfg));
  });

  it("MEMORY.md in path rejected", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    cfg.nollmDataRoot = path.join(os.tmpdir(), "MEMORY.md");
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    assert.throws(() => normalizeConfig(cfg), /legacy memory path/i);
  });

  it("no side effect before config validation", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    cfg.nollmRepoRoot = "relative/path";
    assert.throws(() => normalizeConfig(cfg));
  });

  it("D7: symlinked fixture escaping repo root is rejected (realpath containment)", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const outsideDir = path.join(tmp, "outside");
    const linkDir = path.join(cfg.nollmRepoRoot, "external-link");
    fs.mkdirSync(outsideDir, { recursive: true });
    const outsideFixture = path.join(outsideDir, "alpha-field.json");
    fs.copyFileSync(cfg.alphaFixturePath, outsideFixture);
    // Directory junction does not require admin privileges on Windows
    fs.symlinkSync(outsideDir, linkDir, "junction");
    cfg.alphaFixturePath = path.join(linkDir, "alpha-field.json");
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    assert.throws(() => normalizeConfig(cfg), /symlink-escaped path rejected|must resolve under/i);
  });

  it("D7: symlinked fixture staying inside repo root is accepted", () => {
    const tmp = makeTempDir();
    const cfg = makeProviderConfig(tmp);
    const insideDir = path.join(cfg.nollmRepoRoot, "fixtures2");
    const linkDir = path.join(cfg.nollmRepoRoot, "external-link-in");
    fs.mkdirSync(insideDir, { recursive: true });
    const insideFixture = path.join(insideDir, "alpha-field.json");
    fs.copyFileSync(cfg.alphaFixturePath, insideFixture);
    fs.symlinkSync(insideDir, linkDir, "junction");
    cfg.alphaFixturePath = path.join(linkDir, "alpha-field.json");
    writeStubSidecar(cfg.nollmRepoRoot, STUB_STATUS);
    assert.doesNotThrow(() => normalizeConfig(cfg));
  });
});