from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/recall_lens/run_provider_causal_writer_field_reader_validation.py"


def _module():
    spec = importlib.util.spec_from_file_location("provider_causal_writer_field_reader", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_background_fixture_is_durable_and_target_free(tmp_path: Path) -> None:
    module = _module()
    scenario = module.SCENARIOS[0]
    fixture = module._seed_background(tmp_path, 1, scenario)

    assert [item["handle"]["geometry_address"]["q"] for item in fixture["placements"]] == [0, -4, -4]
    assert [item["handle"]["geometry_address"]["r"] for item in fixture["placements"]] == [0, 0, 4]
    assert all(item["durable_commit"]["reopen_verified"] for item in fixture["placements"])
    assert scenario[3] not in {scenario[1], scenario[2], scenario[5]}


def test_same_field_ablation_changes_realized_junction(tmp_path: Path) -> None:
    module = _module()
    scenario = module.SCENARIOS[0]
    fixture = module._seed_background(tmp_path, 1, scenario)
    left = fixture["placements"][0]["handle"]["geometry_address"]
    right = fixture["placements"][1]["handle"]["geometry_address"]
    plan = {"relation_groups": [[left], [right]]}

    result = module._ablation(tmp_path, plan, fixture["placements"][2]["handle"]["geometry_address"])

    assert result["relation_group_count"] == 2
    assert result["original_candidates"][0]["all_groups_realized"]
    assert result["original_candidates"][0]["cell"]["q"] == -2
    assert result["effect_observed"]
    assert result["reason_text_not_supplied_to_core"]


def test_prepared_case_freezes_field_complete_certificate(tmp_path: Path) -> None:
    module = _module()

    case = module._prepare_case(tmp_path, 1, module.SCENARIOS[0])

    assert case["atlas_certificate"] == case["writer"]["atlas"]["coverage_certificate"]
    assert case["atlas_certificate"]["occupied_field_cell_count"] == 3
    assert case["atlas_certificate"]["uncovered_field_cell_count"] == 0
    assert not case["atlas_certificate"]["overflow"]
