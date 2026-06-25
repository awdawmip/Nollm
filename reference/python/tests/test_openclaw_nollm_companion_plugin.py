from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "integrations/openclaw/nollm-memory-companion"


def test_companion_plugin_package_files_exist() -> None:
    for relative in [
        "README.md",
        "package.json",
        "tsconfig.json",
        "openclaw.plugin.json",
        "src/index.ts",
        "src/sidecar.ts",
        "src/schemas.ts",
        "src/types.ts",
        "skill/SKILL.md",
        "examples/openclaw.config.example.json5",
        "tests/plugin-contract.test.mjs",
        "package-lock.json",
    ]:
        assert (PACKAGE / relative).exists(), relative


def test_package_json_declares_openclaw_extension_and_runtime_entry() -> None:
    package = json.loads((PACKAGE / "package.json").read_text(encoding="utf-8"))

    assert package["type"] == "module"
    assert package["main"] == "./dist/index.js"
    assert package["exports"]["."] == "./dist/index.js"
    assert package["openclaw"]["extensions"] == ["./dist/index.js"]
    assert package["scripts"]["plugin:build"] == "npm run build && openclaw plugins build --entry ./dist/index.js"
    assert package["scripts"]["plugin:check"] == (
        "npm run build && openclaw plugins build --entry ./dist/index.js --check && "
        "openclaw plugins validate --entry ./dist/index.js"
    )
    assert package["scripts"]["test"] == "npm run build && node --test tests/*.test.mjs"
    assert package["dependencies"]["typebox"]
    assert package["devDependencies"]["openclaw"]


def test_manifest_is_tool_plugin_not_active_memory_slot() -> None:
    manifest_text = (PACKAGE / "openclaw.plugin.json").read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)

    assert "kind" not in manifest
    assert "entry" not in manifest
    assert "tools" not in manifest
    assert "plugins.slots.memory" not in manifest_text
    assert "memory slot" not in manifest_text.lower()
    assert manifest["activation"]["onStartup"] is False
    assert manifest["skills"] == ["skill"]
    assert manifest["configSchema"]["type"] == "object"
    assert manifest["configSchema"]["additionalProperties"] is False
    assert manifest["contracts"]["tools"] == [
        "nollm_memory_status",
        "nollm_field_overview",
        "nollm_open_well",
        "nollm_surface",
        "nollm_focus",
        "nollm_drift",
        "nollm_read",
        "nollm_recall_trace",
        "nollm_memory_remember",
        "nollm_memory_recall",
        "nollm_memory_get",
    ]
    assert "toolMetadata" not in manifest


def test_typescript_declares_exact_static_tool_names_and_optional_write() -> None:
    source = (PACKAGE / "src/index.ts").read_text(encoding="utf-8")
    expected = [
        "nollm_field_overview",
        "nollm_open_well",
        "nollm_surface",
        "nollm_focus",
        "nollm_drift",
        "nollm_read",
        "nollm_recall_trace",
        "nollm_memory_status",
        "nollm_memory_remember",
        "nollm_memory_recall",
        "nollm_memory_get",
    ]

    for tool in expected:
        assert source.count(f'name: "{tool}"') == 1
    for tool in ["nollm_memory_search", "nollm_memory_write_candidate", "nollm_memory_commit_candidate"]:
        assert f'name: "{tool}"' not in source
    assert 'name: "nollm_memory_write_candidate"' not in source
    assert 'name: "nollm_memory_commit_candidate"' not in source
    assert "tools: (tool) =>" in source
    assert "parameters:" in source
    assert "inputSchema" not in source
    assert "context.signal?.throwIfAborted()" in source


def test_config_docs_contain_absolute_path_and_timeout_boundaries() -> None:
    corpus = "\n".join(
        [
            (PACKAGE / "README.md").read_text(encoding="utf-8"),
            (PACKAGE / "src/schemas.ts").read_text(encoding="utf-8"),
            (PACKAGE / "src/sidecar.ts").read_text(encoding="utf-8"),
        ]
    )

    assert "absolute path" in corpus
    assert "1000" in corpus
    assert "60000" in corpus
    assert "1..20" in corpus
    assert "sidecarScript" in corpus
    assert "nollmRepoRoot" in corpus
    assert "sidecarOutDir" in corpus
    assert "workspaceRoot" in corpus


def test_skill_teaches_required_workflow_and_gravity_trust_distinction() -> None:
    skill = (PACKAGE / "skill/SKILL.md").read_text(encoding="utf-8")

    for phrase in [
        "Use `nollm_field_overview`",
        "Use `nollm_open_well`",
        "Use `nollm_surface`",
        "Use `nollm_focus`",
        "Use `nollm_drift`",
        "Use `nollm_recall_trace`",
        "true honeycomb neighbors",
        "Cortex, write the compact `NOLLM_RECALL_DIGEST` envelope",
        "lateral",
        "Do not use `memory_search` / `memory_get` as the Nollm internal model",
        "Gravity report = instrumentation, not permission.",
        "Drift class = orientation, not trust.",
        "Use `nollm_memory_remember`",
        "Use `nollm_memory_recall`",
        "Use `nollm_memory_get`",
    ]:
        assert phrase in skill


def test_config_example_does_not_set_memory_slot_and_marks_active_memory_experiment_optional() -> None:
    example = (PACKAGE / "examples/openclaw.config.example.json5").read_text(encoding="utf-8")

    assert "plugins.slots.memory" not in example
    assert "plugins: {" in example
    assert "entries: {" in example
    assert '"nollm-memory-companion"' in example
    assert "activeMemoryExperiment" not in example
    assert "nollm_field_overview" in example
    assert "nollm_open_well" in example
    assert "nollm_recall_trace" in example
    assert "nollm_memory_write_candidate" not in example
    assert "nollm_memory_commit_candidate" not in example
    assert "nollm_memory_search" not in example
    assert "nollm_memory_remember" in example
    assert "nollm_memory_recall" in example
    assert "nollm_memory_get" in example
    assert "do not replace source verification" in example


def test_forbidden_implementation_claims_are_absent() -> None:
    corpus = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            PACKAGE / "README.md",
            PACKAGE / "openclaw.plugin.json",
            PACKAGE / "skill/SKILL.md",
            PACKAGE / "examples/openclaw.config.example.json5",
        ]
    ).lower()

    forbidden = [
        "kind: \"memory\"",
        "plugins.slots.memory",
        "replaces memory-core",
        "calls a real llm",
        "writes durable openclaw memory",
        "maps drift_class to trust",
        "maps drift_class to status",
        "provides a stable public recall api",
        "implements a stable public recall api",
        "gateway load test verified",
    ]
    for phrase in forbidden:
        assert phrase not in corpus


def test_sidecar_bridge_uses_safe_process_boundaries() -> None:
    sidecar = (PACKAGE / "src/sidecar.ts").read_text(encoding="utf-8")

    assert 'from "node:child_process"' in sidecar
    assert "spawn(" in sidecar
    assert "shell: false" in sidecar
    assert "executable" in sidecar
    assert "pythonArgs" in sidecar
    assert "setTimeout" in sidecar
    assert "fs.realpathSync.native" in sidecar
    assert "signal?.addEventListener" in sidecar
    assert "MAX_CAPTURE_BYTES" in sidecar
    assert "JSON.parse" in sidecar
    assert "sidecar_timeout" in sidecar
    assert "sidecar_failed" in sidecar
    assert "sidecar_invalid_json" in sidecar
    assert "configuration_error" in sidecar
    assert "exec(" not in sidecar
    assert "execFile(" not in sidecar
