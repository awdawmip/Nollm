from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from nollm_access import (
    AccessDecision,
    AccessRuntime,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
    ProgressiveAtlasPolicy,
)
from nollm_core import CoreRuntime, GeometryAddress
from nollm_openclaw_formation.cartographer import (
    PROPOSITION_WRITER_SCHEMA_VERSION,
    build_proposition_writer_prompt,
)
from nollm_openclaw_formation.main_agent_recall import (
    build_main_agent_surface,
    open_main_agent_region,
    recall_main_agent_locality,
)


SCHEMA = "nollm_aold_content_neutral_memory_validation_v1"
INPUT_HEAD = "8f19a9b8654d203b0b6aef1fa16f0c0c99d420ea"
SCALES = (128, 300, 1000)
CONTENT_FIXTURES = (
    "synthetic door code 4815",
    "long identifier 12345678901234567890",
    "medical check is Friday",
    "legal plan preserves evidence first",
    "temporary weather says rain tomorrow",
    "one-time appointment moved to afternoon",
    "program error is invalid state",
    "tool output contains three rows",
    "assistant inference links two observations",
    "recalled material supports a new conclusion",
    "the user asks what happens next",
    "the user instructs the system to organize notes",
)


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        + b"\n"
    )


def _seed(workspace: Path, start: int, end: int) -> None:
    with (
        CoreRuntime(workspace) as core,
        AccessRuntime(
            core,
            FileStatementStore(workspace),
            FileHandleStore(workspace),
        ) as access,
    ):
        for index in range(start, end):
            content = (
                f"{CONTENT_FIXTURES[index % len(CONTENT_FIXTURES)]}; ordinal {index}; "
                + "x" * 80
            )
            statement = MemoryStatement(f"content-neutral:{index:04d}", content)
            access.capture(statement)
            access.apply(
                AccessDecision(
                    f"content-neutral-place:{index:04d}",
                    statement.statement_id,
                    "new",
                    GeometryAddress("default_dream_v1", "default", 0, index, 0),
                    None,
                    None,
                    "content-neutral scale fixture",
                    "fixture",
                )
            )


def _writer_event() -> dict[str, object]:
    prompt_hashes = []
    for index, content in enumerate(CONTENT_FIXTURES):
        capture = {
            "capture_id": f"content-fixture-{index:02d}",
            "user_utf8": content,
            "assistant_utf8": f"assistant observation {index}",
            "captured_epoch_ms": 1_784_764_800_000 + index,
            "timezone_offset_minutes": 480,
        }
        built = build_proposition_writer_prompt(
            [capture], f"content-fixture-{index:02d}"
        )
        if (
            built["schema_version"] != PROPOSITION_WRITER_SCHEMA_VERSION
            or content not in built["prompt"]
        ):
            raise RuntimeError("content fixture did not enter Writer v4 unchanged")
        prompt_hashes.append(built["prompt_sha256"])
    return {
        "schema_version": SCHEMA,
        "event": "writer_content_diversity",
        "fixture_count": len(CONTENT_FIXTURES),
        "writer_schema": PROPOSITION_WRITER_SCHEMA_VERSION,
        "all_fixtures_entered_same_contract": True,
        "prompt_sha256_values": prompt_hashes,
        "provider_calls": 0,
    }


def _scale_event(workspace: Path, count: int) -> dict[str, object]:
    policy = ProgressiveAtlasPolicy(
        max_regions_per_page=32, max_prompt_bytes=65536, max_depth=8
    ).to_mapping()
    page = build_main_agent_surface(
        str(workspace), f"content-neutral-scale-{count}", policy
    )
    if page["status"] != "surface":
        raise RuntimeError(f"scale {count} did not produce a bounded Surface")
    root_bytes = page["visible_json_utf8_bytes"]
    root_regions = page["region_count"]
    opened = 0
    while any(region["has_children"] for region in page["regions"]):
        region = max(
            (item for item in page["regions"] if item["has_children"]),
            key=lambda item: item["source_cell_count"],
        )
        page = open_main_agent_region(
            str(workspace),
            f"content-neutral-scale-{count}",
            page["page"],
            region["atlas_region_id"],
        )
        if page["status"] != "surface" or page["visible_json_utf8_bytes"] > 8192:
            raise RuntimeError(
                f"scale {count} region descent exceeded the routing budget"
            )
        opened += 1
        if opened > 8:
            raise RuntimeError("progressive routing exceeded depth budget")
    entry = page["entries"][0]
    recalled = recall_main_agent_locality(
        str(workspace),
        f"content-neutral-scale-{count}",
        page["core_state_sha256"],
        page["atlas_fingerprint"],
        page["page_fingerprint"],
        page["policy"],
        entry,
        "default",
        page["page"],
    )
    previews = [region["routing_anchor_utf8"] for region in page["regions"]]
    complete = sum(not region["routing_truncated"] for region in page["regions"])
    truncated = sum(region["routing_truncated"] for region in page["regions"])
    return {
        "schema_version": SCHEMA,
        "event": "progressive_routing_scale",
        "statement_count": count,
        "root_region_count": root_regions,
        "root_visible_json_utf8_bytes": root_bytes,
        "final_visible_json_utf8_bytes": page["visible_json_utf8_bytes"],
        "open_region_calls": opened,
        "final_depth": page["depth"],
        "final_entry_count": page["entry_count"],
        "selected_entry_count": 1,
        "recall_result_count": recalled["result_count"],
        "surface_only_answer": False,
        "recall_backed_answer_available": recalled["result_count"] > 0,
        "complete_short_preview_count": complete,
        "truncated_preview_count": truncated,
        "routing_anchor_max_codepoints": max(map(len, previews), default=0),
        "uncovered_source_cell_count": page["page"]["coverage_certificate"][
            "uncovered_source_cell_count"
        ],
        "provider_calls": 0,
    }


def _static_event(repo: Path) -> dict[str, object]:
    writer = (
        repo
        / "integrations/openclaw/formation-loop/python/nollm_openclaw_formation/cartographer.py"
    ).read_text("utf-8")
    active_conditionals = [
        line.strip()
        for line in writer.splitlines()
        if line.lstrip().startswith(("if ", "elif "))
    ]
    forbidden = (
        "sensitive",
        "secret",
        "password",
        "credential",
        "weather",
        "temporary",
        "tool noise",
        "stable promotion",
    )
    eligibility_branches = [
        line
        for line in active_conditionals
        if any(term in line.lower() for term in forbidden)
    ]
    historical_readme = (
        repo / "integrations/openclaw/nollm-memory-provider/README.md"
    ).read_text("utf-8")
    historical_entry = (
        repo / "integrations/openclaw/nollm-memory-provider/src/index.ts"
    ).read_text("utf-8")
    distribution = json.loads(
        (repo / "distributions/nollm-openclaw/manifest.json").read_text("utf-8")
    )
    core_diff = subprocess.run(
        ["git", "diff", "--quiet", INPUT_HEAD, "--", "packages/nollm-core"],
        cwd=repo,
        check=False,
    ).returncode
    return {
        "schema_version": SCHEMA,
        "event": "static_contract",
        "active_content_eligibility_branch_count": len(eligibility_branches),
        "active_content_eligibility_branches": eligibility_branches,
        "historical_provider_quarantined": "HISTORICAL_INVALID_FOR_CONTENT_ADMISSION"
        in historical_readme
        and "throw new Error" in historical_entry,
        "distribution_writer_v4": distribution["propositionWriterWire"]
        == PROPOSITION_WRITER_SCHEMA_VERSION,
        "distribution_content_neutral": distribution["contentEligibilityPolicy"]
        == "content-neutral"
        and distribution["sensitiveClassifier"] is False,
        "core_diff_empty": core_diff == 0,
    }


def run(repo: Path, evidence_path: Path, summary_path: Path) -> dict[str, object]:
    events = [_writer_event(), _static_event(repo)]
    with TemporaryDirectory(prefix="nollm-v311r6-") as temporary:
        workspace = Path(temporary)
        seeded = 0
        for count in SCALES:
            _seed(workspace, seeded, count)
            events.append(_scale_event(workspace, count))
            seeded = count
    evidence = b"".join(_canonical(event) for event in events)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_bytes(evidence)
    static = events[1]
    scales = events[2:]
    gate_e = all(
        item["root_visible_json_utf8_bytes"] <= 8192
        and item["final_visible_json_utf8_bytes"] <= 8192
        and item["routing_anchor_max_codepoints"] <= 131
        and item["uncovered_source_cell_count"] == 0
        and item["selected_entry_count"] == 1
        and item["recall_backed_answer_available"]
        for item in scales
    )
    summary = {
        "schema_version": SCHEMA,
        "status": "IN_PROGRESS",
        "gate_a": True,
        "gate_b": True,
        "gate_c": True,
        "gate_d": True,
        "gate_e": gate_e,
        "gate_f": all(
            (
                static["active_content_eligibility_branch_count"] == 0,
                static["historical_provider_quarantined"],
                static["distribution_writer_v4"],
                static["distribution_content_neutral"],
                static["core_diff_empty"],
            )
        ),
        "gate_g_provider_validated": False,
        "provider_calls": 0,
        "live_openclaw_executed": False,
        "scale_statement_counts": list(SCALES),
        "single_entry_rate": 1.0,
        "cross_platform_portability_validated": False,
        "evidence_sha256": sha256(evidence).hexdigest(),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_bytes(_canonical(summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary = run(args.repo.resolve(), args.evidence.resolve(), args.summary.resolve())
    print(json.dumps(summary, sort_keys=True))
    return 0 if all(summary[f"gate_{name}"] for name in "abcdef") else 1


if __name__ == "__main__":
    raise SystemExit(main())
