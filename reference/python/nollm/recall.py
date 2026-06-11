from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .filesystem import card_address, notebook_name, read_card, read_yaml_file, recall_address
from .ids import next_recall_id
from .models import RECALL_KEYS


def deterministic_recall(path: Path, query_or_task: str) -> tuple[dict[str, Any], Path, Path]:
    notebook = notebook_name(path)
    anchors_doc = read_yaml_file(path / "anchors.yaml")
    aliases_doc = read_yaml_file(path / "aliases.yaml")
    query = query_or_task.lower()

    anchors_used: list[str] = []
    for anchor in anchors_doc.get("anchors", []) or []:
        values = [
            anchor.get("id", ""),
            anchor.get("label", ""),
            anchor.get("definition", ""),
            *list(anchor.get("aliases", []) or []),
        ]
        if any(str(value).lower() in query for value in values if value):
            anchors_used.append(str(anchor.get("id")))

    aliases = aliases_doc.get("aliases", {})
    if isinstance(aliases, dict):
        for alias, value in aliases.items():
            target = value.get("anchor") if isinstance(value, dict) else value
            if str(alias).lower() in query and target and target not in anchors_used:
                anchors_used.append(str(target))

    matches: list[tuple[int, int, dict[str, Any], str]] = []
    terms = [term for term in query.replace("_", " ").split() if term]
    for card_path in (path / "cards").rglob("*.md"):
        front, body, _ = read_card(path, card_path.stem)
        status = front.get("status")
        if status == "archived":
            continue
        haystack = " ".join(
            str(value)
            for value in [
                front.get("title", ""),
                front.get("claim", ""),
                " ".join(front.get("anchors", []) or []),
                body,
            ]
        ).lower()
        score = sum(1 for term in terms if term in haystack)
        if anchors_used and set(front.get("anchors", []) or []).intersection(anchors_used):
            score += 3
        if score:
            priority = 2 if status == "confirmed" else 1 if status == "candidate" else 0
            matches.append((priority, score, front, body))

    matches.sort(key=lambda item: (item[0], item[1], item[2].get("id", "")), reverse=True)
    selected = matches[:5]
    cards_read = [card_address(notebook, str(front.get("id"))) for _priority, _score, front, _body in selected]
    warnings = [
        f"Candidate card included: {front.get('id')}"
        for _priority, _score, front, _body in selected
        if front.get("status") == "candidate"
    ]
    open_questions = [
        str(front.get("claim"))
        for _priority, _score, front, _body in selected
        if front.get("type") == "question" and front.get("claim")
    ]

    digest = {
        "query_or_task": query_or_task,
        "memory_intent": "focus",
        "anchors_used": anchors_used,
        "cards_read": cards_read,
        "recalled_points": [str(front.get("claim")) for _priority, _score, front, _body in selected if front.get("claim")],
        "warnings": warnings,
        "do_not_assume": sorted(
            {
                item
                for _priority, _score, front, _body in selected
                for item in (front.get("do_not_infer", []) or [])
            }
        ),
        "source_addresses": cards_read,
        "open_questions": open_questions,
    }
    for key in RECALL_KEYS:
        digest.setdefault(key, [] if key != "query_or_task" and key != "memory_intent" else "")

    recalls_dir = path / "recalls"
    recalls_dir.mkdir(exist_ok=True)
    recall_id = next_recall_id(recalls_dir)
    digest["address"] = recall_address(notebook, recall_id)
    json_path = recalls_dir / f"{recall_id}.json"
    md_path = recalls_dir / f"{recall_id}.md"
    json_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown_digest(digest), encoding="utf-8")
    return digest, json_path, md_path


def render_markdown_digest(digest: dict[str, Any]) -> str:
    lines = ["# Recall Digest", ""]
    for key in RECALL_KEYS:
        lines.append(f"## {key}")
        lines.append("")
        value = digest.get(key)
        if isinstance(value, list):
            if value:
                lines.extend(f"- `{item}`" if isinstance(item, str) and item.startswith("nollm://") else f"- {item}" for item in value)
            else:
                lines.append("- none")
        else:
            lines.append(str(value))
        lines.append("")
    return "\n".join(lines)

