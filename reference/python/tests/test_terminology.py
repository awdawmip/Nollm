from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TERMINOLOGY_PATH = ROOT / "protocol" / "TERMINOLOGY.md"
TERMINOLOGY_TEST_PATH = Path(__file__).resolve()
IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    ".venv",
    "venv",
}
IGNORED_SUFFIXES = {
    ".egg-info",
    ".pyc",
    ".pyo",
    ".zip",
    ".gz",
    ".tar",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
}


class TerminologyTests(unittest.TestCase):
    def test_openclaw_is_classified_as_migration_asset_and_obsolete_namespace_is_absent(self) -> None:
        forbidden_terms = forbidden_terms_from_contract()

        openclaw_boundary = ROOT / "docs" / "history" / "OPENCLAW_V2_MIGRATION_ASSET_BOUNDARY.md"
        layer_constitution = ROOT / "protocol" / "v2" / "LAYER_CONSTITUTION.md"
        self.assertTrue(openclaw_boundary.is_file())
        self.assertTrue(layer_constitution.is_file())
        self.assertFalse((ROOT / "examples" / ("lob" + "ster")).exists())

        docs_or_protocol_hits = []
        forbidden_hits = collect_forbidden_hits(text_files(ROOT), forbidden_terms)
        boundary_text = openclaw_boundary.read_text(encoding="utf-8")
        constitution_text = layer_constitution.read_text(encoding="utf-8")

        self.assertIn("OpenClaw legacy is a frozen L5/L6 migration asset", boundary_text)
        self.assertIn("not the current Nollm runtime path", boundary_text)
        self.assertIn("L5 Host Adapter or L6 Terminal", constitution_text + "\n" + boundary_text)

        for path in text_files(ROOT):
            text = path.read_text(encoding="utf-8", errors="ignore")
            lower_text = text.lower()
            if "openclaw" in lower_text:
                if is_doc_or_protocol(path):
                    docs_or_protocol_hits.append(path)
            if "protocol/terminology.md" in lower_text and is_doc_or_protocol(path):
                docs_or_protocol_hits.append(path)

        self.assertTrue(docs_or_protocol_hits, "expected documentation to mention OpenClaw or terminology")
        self.assertEqual(forbidden_hits, [])

    def test_forbidden_terms_are_detected_outside_terminology_contract(self) -> None:
        forbidden_terms = forbidden_terms_from_contract()
        with tempfile.TemporaryDirectory() as tmp:
            ordinary_doc = Path(tmp) / "ordinary.md"
            ordinary_doc.write_text("\n".join(forbidden_terms), encoding="utf-8")

            hits = collect_forbidden_hits([ordinary_doc], forbidden_terms)

        self.assertEqual(hits, [str(ordinary_doc)])

    def test_actual_chinese_forbidden_terms_are_detected(self) -> None:
        forbidden_terms = forbidden_terms_from_contract()
        with tempfile.TemporaryDirectory() as tmp:
            ordinary_doc = Path(tmp) / "ordinary.md"
            ordinary_doc.write_text("榫欒櫨\n榫嶈潶\n", encoding="utf-8")

            hits = collect_forbidden_hits([ordinary_doc], forbidden_terms)

        self.assertEqual(hits, [str(ordinary_doc)])

    def test_openclaw_terms_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ordinary_doc = Path(tmp) / "ordinary.md"
            ordinary_doc.write_text("OpenClaw uses the openclaw namespace.", encoding="utf-8")

            hits = collect_forbidden_hits([ordinary_doc], forbidden_terms_from_contract())

        self.assertEqual(hits, [])


def forbidden_terms_from_contract() -> tuple[str, ...]:
    text = TERMINOLOGY_PATH.read_text(encoding="utf-8")
    section = forbidden_section(text)
    terms = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- `") and stripped.endswith("`"):
            terms.append(stripped.removeprefix("- `").removesuffix("`"))
    return tuple(terms)


def forbidden_section(text: str) -> str:
    marker = "## Forbidden Terms"
    if marker not in text:
        return ""
    section = text.split(marker, 1)[1]
    next_heading = section.find("\n## ")
    return section if next_heading == -1 else section[:next_heading]


def collect_forbidden_hits(paths, forbidden_terms: tuple[str, ...]) -> list[str]:
    hits = []
    for path in paths:
        if path.resolve() == TERMINOLOGY_TEST_PATH:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.resolve() == TERMINOLOGY_PATH.resolve():
            text = text.replace(forbidden_section(text), "")
        if any(term in text for term in forbidden_terms):
            hits.append(str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path))
    return hits


def text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        yield path


def is_doc_or_protocol(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return relative.parts[0] in {"docs", "protocol"} or relative.name == "README.md"


if __name__ == "__main__":
    unittest.main()
