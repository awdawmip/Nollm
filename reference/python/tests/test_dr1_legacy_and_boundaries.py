import ast
from pathlib import Path

from nollm.dream_geometry.recall import RecallPolicy, resolve_recall

from fixtures.dr1_recall.fixture import build_fixture, query_probe, relative_time_resolution, with_legacy_proposal_only


def test_dr1_legacy_dc1_records_are_context_only_not_seeds(tmp_path) -> None:
    store, _, universe = build_fixture(tmp_path)
    legacy = with_legacy_proposal_only(universe)
    digest = resolve_recall(query_probe(), legacy, store, runtime_time=relative_time_resolution(), policy=RecallPolicy(include_legacy_context=True))
    assert digest.items == ()
    assert "DR1_LEGACY_PROPOSALS_CONTEXT_ONLY" in digest.warnings


def test_dr1_recall_package_has_no_forbidden_runtime_imports() -> None:
    root = Path(__file__).resolve().parents[1] / "nollm" / "dream_geometry" / "recall"
    forbidden = {"subprocess", "socket", "requests", "urllib", "sqlite3"}
    forbidden_prefixes = ("nollm.cli", "nollm.openclaw", "nollm.adapters")
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name for alias in node.names}
                assert names.isdisjoint(forbidden)
                assert all(not name.startswith(forbidden_prefixes) for name in names)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden
                assert not node.module.startswith(forbidden_prefixes)
