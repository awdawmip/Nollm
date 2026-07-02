"""DF1 validation fixture helpers."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = REPO_ROOT / "reference" / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from tests.fixtures.df1_assembly.fixture import build_df1_environment, finite_projected_set, finite_set, tree_manifest  # noqa: E402


def build_baseline(root: Path):
    specs = (
        ("adm_df1_alpha", "shard:df1:alpha", "gp_df1_alpha", "Kunming rain alpha."),
        ("adm_df1_beta", "shard:df1:beta", "gp_df1_beta", "Kunming rain beta."),
        ("adm_df1_gamma", "shard:df1:gamma", "gp_df1_gamma", "Kunming rain gamma."),
    )
    return build_df1_environment(root, specs)


__all__ = ["build_baseline", "finite_projected_set", "finite_set", "tree_manifest"]
