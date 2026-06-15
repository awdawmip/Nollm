from __future__ import annotations

import ast
from pathlib import Path
import unittest

from nollm.chart_gluing import (
    GluingProposal,
    LocalChartSpec,
    parameter_signature,
    summarize_chart_overlap,
)
from nollm.geometry import (
    HexAddress,
    LayerSpec,
    SimilarityTransform,
    coverage_map,
)


ROOT = Path(__file__).resolve().parents[3]
CHART_GLUING_SOURCE = ROOT / "reference" / "python" / "nollm" / "chart_gluing.py"


def sample_rows():
    return tuple(
        coverage_map(
            HexAddress(0, 0, 0),
            LayerSpec(layer=0),
            LayerSpec(layer=1),
            search_radius=3,
        )
    )


class ChartGluingRecordTests(unittest.TestCase):
    def test_local_chart_spec_accepts_valid_bounded_spec(self) -> None:
        spec = LocalChartSpec(
            chart_id="chart-a",
            seed=HexAddress(0, 0, 0),
            source_radius=2,
            layer_ids=(0, 1),
            parameter_signature="params",
        )
        self.assertEqual(spec.chart_id, "chart-a")
        self.assertEqual(spec.layer_ids, (0, 1))

    def test_local_chart_spec_rejects_invalid_identity_and_bounds(self) -> None:
        valid = {
            "chart_id": "chart-a",
            "seed": HexAddress(0, 0, 0),
            "source_radius": 1,
            "layer_ids": (0, 1),
            "parameter_signature": "params",
        }
        invalids = [
            {"chart_id": ""},
            {"source_radius": -1},
            {"source_radius": True},
            {"layer_ids": ()},
            {"layer_ids": (0, True)},
            {"parameter_signature": ""},
        ]
        for override in invalids:
            with self.subTest(override=override):
                params = dict(valid)
                params.update(override)
                with self.assertRaises(ValueError):
                    LocalChartSpec(**params)

    def test_parameter_signature_is_deterministic_for_reordered_mapping(self) -> None:
        first = {
            0: LayerSpec(layer=0, origin=(1.0, 2.0)),
            1: LayerSpec(layer=1, origin=(1.0, 2.0), theta_deg=15.0),
        }
        second = {
            1: LayerSpec(layer=1, origin=(1.0, 2.0), theta_deg=15.0),
            0: LayerSpec(layer=0, origin=(1.0, 2.0)),
        }
        self.assertEqual(parameter_signature(first), parameter_signature(second))

    def test_summarize_chart_overlap_uses_source_denominator_by_default(self) -> None:
        rows = sample_rows()
        summary = summarize_chart_overlap("chart-a", "chart-b", rows)
        self.assertEqual(summary.coverage_denominator, "source")
        self.assertAlmostEqual(summary.coverage_sum, sum(row.weight_source for row in rows))

    def test_summarize_chart_overlap_supports_target_and_union_denominators(self) -> None:
        rows = sample_rows()
        target = summarize_chart_overlap("chart-a", "chart-b", rows, denominator="target")
        union = summarize_chart_overlap("chart-a", "chart-b", rows, denominator="union")
        self.assertAlmostEqual(target.coverage_sum, sum(row.weight_target for row in rows))
        self.assertAlmostEqual(union.coverage_sum, sum(row.jaccard for row in rows))

    def test_candidate_overlap_has_no_ownership_semantics(self) -> None:
        summary = summarize_chart_overlap("chart-a", "chart-b", sample_rows())
        for forbidden_attr in ("parent", "children", "owner", "folder", "belongs_to"):
            self.assertFalse(hasattr(summary, forbidden_attr))

    def test_gluing_proposal_defaults_to_candidate(self) -> None:
        rows = sample_rows()
        proposal = GluingProposal(
            proposal_id="proposal-a",
            source_chart_id="chart-a",
            target_chart_id="chart-b",
            similarity_candidate=SimilarityTransform(),
            residual=0.0,
            evidence_rows=rows,
        )
        self.assertEqual(proposal.status, "candidate")
        self.assertIsInstance(proposal.similarity_candidate, SimilarityTransform)

    def test_gluing_proposal_rejects_invalid_fields(self) -> None:
        rows = sample_rows()
        valid = {
            "proposal_id": "proposal-a",
            "source_chart_id": "chart-a",
            "target_chart_id": "chart-b",
            "similarity_candidate": SimilarityTransform(),
            "residual": 0.0,
            "evidence_rows": rows,
        }
        invalids = [
            {"proposal_id": ""},
            {"source_chart_id": ""},
            {"target_chart_id": ""},
            {"residual": -0.1},
            {"status": ""},
        ]
        for override in invalids:
            with self.subTest(override=override):
                params = dict(valid)
                params.update(override)
                with self.assertRaises(ValueError):
                    GluingProposal(**params)

    def test_d2_module_does_not_import_runtime_or_card_writing_layers(self) -> None:
        tree = ast.parse(CHART_GLUING_SOURCE.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        forbidden = {
            "annotation",
            "audit",
            "cli",
            "filesystem",
            "history",
            "models",
            "recall",
            "review",
            "tool_api",
            "validation",
        }
        self.assertTrue(imported_modules.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
