from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

from nollm.dream_geometry.validation.cx2.fixtures import dg7_correspondence_fixture, invalid_fixtures, valid_fixtures
from nollm.dream_geometry.validation.cx2.serialization import canonical_json, canonical_markdown
from nollm.dream_geometry.validation.cx2.types import CX2PlanValidationError
from nollm.dream_geometry.validation.cx2.validator import validate_cortex_action_plan


def build_report() -> str:
    valid_results = []
    invalid_results = []
    for name, plan in valid_fixtures():
        valid_results.append((name, validate_cortex_action_plan(plan)))
    for name, plan, expected in invalid_fixtures():
        try:
            validate_cortex_action_plan(plan)
        except CX2PlanValidationError as exc:
            if exc.reason_code != expected:
                raise RuntimeError(f"{name} reason mismatch: {exc.reason_code} != {expected}") from exc
            invalid_results.append((name, exc.reason_code))
        else:
            raise RuntimeError(f"{name} unexpectedly passed")

    valid_hash = sha256(canonical_json(tuple(summary for _name, summary in valid_results)).encode("utf-8")).hexdigest()
    invalid_hash = sha256(canonical_json(tuple(invalid_results)).encode("utf-8")).hexdigest()
    dg7_hash = sha256(canonical_json(dg7_correspondence_fixture()).encode("utf-8")).hexdigest()
    reason_codes = tuple(sorted({code for _name, code in invalid_results}))
    lines = [
        "# CX2 External Cortex Integration Conformance Report",
        "",
        "本报告是 CX2 validation-only conformance report。它证明固定 fixtures、validator 和报告生成可重放；不表示 CX2 已实现 runtime、OpenClaw 接入、自动 admission、global discovery 或真实 memory 写入。",
        "",
        "## Protocol",
        "",
        "- plan kind: `nollm_cortex_action_plan`",
        "- plan version: `1`",
        "- conformance package: validation-only, declaration-only, no runtime registration",
        "- fixture inventory: 4 valid plans, 10 invalid plans, 1 DG7 correspondence fixture",
        "",
        "## Valid Fixtures",
        "",
    ]
    for name, summary in valid_results:
        lines.append(
            f"- `{name}`: intent `{summary.intent}`, captures `{summary.capture_ref_count}`, "
            f"admission requests `{summary.admission_request_count}`, recall `{str(summary.has_recall_request).lower()}`"
        )
    lines.extend(["", "## Invalid Fixtures", ""])
    for name, code in invalid_results:
        lines.append(f"- `{name}` rejected with `{code}`")
    lines.extend(
        [
            "",
            "## Rejection Reason Codes",
            "",
            *[f"- `{code}`" for code in reason_codes],
            "",
            "## DG7 Correspondence",
            "",
            "- DG7 A/B/C/D is used only as an accepted finite positive-chain correspondence witness.",
            "- A/B correspond to host-declared admitted assembly IDs; C remains captured-only; D remains admitted but unassembled.",
            "- DG6 remains view-only and cannot filter, rank, replace, or influence DR1/DI1 recall.",
            "- CX2 does not expose DG7 as an external model runtime and does not run the DG7 runner.",
            "",
            "## Canonical Hashes",
            "",
            "- hash origin: canonical JSON emitted by CX2 serialization with sorted keys, compact separators, ASCII, and LF line endings",
            f"- valid fixture summary SHA-256: `{valid_hash}`",
            f"- invalid fixture result SHA-256: `{invalid_hash}`",
            f"- DG7 correspondence fixture SHA-256: `{dg7_hash}`",
            "",
            "## Explicit Non-Goals",
            "",
            "- no production runtime, session manager, daemon, scheduler, CLI registration, OpenClaw connection, network, database, or cache",
            "- no LLM/NLP, embedding, semantic search, automatic summary, automatic admission, automatic placement, automatic anchor, or global discovery",
            "- no durable FieldSnapshot, AdmissionRecord, RecallUniverse, ledger event, recall result, or true memory write",
            "- no DG6 recall influence and no DG7 runtime exposure",
        ]
    )
    return canonical_markdown(lines)


def main() -> None:
    output = None
    if "--output" in sys.argv:
        index = sys.argv.index("--output")
        output = Path(sys.argv[index + 1])
    report = build_report()
    if output is None:
        print(report, end="")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
