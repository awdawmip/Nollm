"""Native project writes, pressure feedback, and portable CLI continuation.

All placements are fixture Host choices from the shown locality. The tests
choose lower material through actual coverage, then observe persisted Access
and Core state; no pressure result or geometric relationship is mocked.
"""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from install_skill import install
from nollm_access.write_policy import (
    ACTIVE_SEMANTIC_WRITE_POLICY_ID,
    EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
    ActiveSemanticWritePolicyError,
)
from nollm_core import CoreRuntime, GeometryAddress, expand_physical_coverage
from project_memory import decide, describe, encounter, save_statement


SOURCE = "fixture:pressure-source/original"
UPDATED = "fixture:pressure-source/revised"
LAYERS = (0, 1, 2)
ROOT = Path(__file__).resolve().parent


def address(coords):
    return GeometryAddress("default_dream_v1", "default", *coords)


def coordinates(cell):
    return [cell.layer, cell.q, cell.r]


def candidate_at(locality, coords):
    return next(candidate for candidate in locality["cells"] if candidate["cell"] == list(coords))


def supporting_child(locality, parent):
    """Choose a shown child with actual up support and one-step down reachability."""
    shown = {tuple(item["cell"]): item for item in locality["cells"]}
    candidates = []
    for down in expand_physical_coverage(parent, "coverage_down").members:
        key = tuple(coordinates(down.target))
        if key not in shown:
            continue
        for up in expand_physical_coverage(down.target, "coverage_up").members:
            if up.target == parent:
                candidates.append((up.weight_q16, down.target.stable_key(), shown[key]))
    if not candidates:
        raise AssertionError("the actual local geometry has no shown mutually reachable child")
    weight, _, selected = max(candidates, key=lambda value: (value[0], value[1]))
    return selected, weight


def choose_page_candidate(page, preferred=(0, 0, 0)):
    return next((candidate for candidate in page["candidates"]
                 if candidate.get("physical_cell") == list(preferred)), page["candidates"][0])


class ProjectPressureTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="nollm-project-pressure-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.field = self.root / "field"

    def enter(self, *, layers=LAYERS, preferred=(0, 0, 0)):
        options = {"steps": 1, "beam": 32, "limit": 20, "via": "vertical", "pressure": True}
        if layers is not None:
            options["layers"] = layers
        page = encounter(self.field, **options)
        while page["kind"] != "locality":
            selected = choose_page_candidate(page, preferred)
            page = encounter(self.field, [selected["id"]], cursor=page["cursor"])
        return page

    def test_empty_entry_shows_scored_lower_candidates_and_keeps_scope_in_cursor(self):
        page = encounter(self.field, layers=LAYERS, pressure=True)
        self.assertEqual(page["kind"], "physical")
        self.assertNotIn("entry", page)
        origin, = page["candidates"]
        self.assertEqual(origin["physical_cell"], [0, 0, 0])
        local = encounter(self.field, [origin["id"]], cursor=page["cursor"])
        self.assertEqual(local["entry"], [0, 0, 0])
        self.assertEqual(local["physical_layers"], list(LAYERS))
        self.assertEqual(local["write_policy_id"], EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        lower = [item for item in local["cells"] if item["cell"][0] == 1]
        self.assertTrue(lower)
        for item in lower:
            pressure = item["write_pressure"]
            self.assertEqual(pressure["demand_units"], 1)
            self.assertEqual(pressure["support_q16"], 0)
            self.assertEqual(pressure["pressure"], 51)
            self.assertTrue(pressure["advisory"])
        reopened = encounter(self.field, cursor=local["cursor"])
        self.assertEqual(reopened["entry"], local["entry"])
        self.assertEqual(reopened["physical_layers"], list(LAYERS))
        self.assertEqual(reopened["cells"], local["cells"])
        with self.assertRaisesRegex(ValueError, "restart"):
            encounter(self.field, cursor=local["cursor"], layers=(0, 1))

    def test_high_pressure_same_layer_write_and_real_lower_support_feedback(self):
        local = self.enter()
        cursor = local["cursor"]
        parent = address(local["entry"])
        target = candidate_at(local, local["entry"])["id"]
        for index in range(4):
            decide(self.field, cursor, "new", target, note_id=f"upper-{index}",
                   body=f"Distinct upper fixture material {index}", sources=[SOURCE])
        before = candidate_at(encounter(self.field, cursor=cursor), local["entry"])["write_pressure"]
        self.assertGreaterEqual(before["pressure"], 80)
        # Advisory pressure does not redirect or reject this explicit same-cell choice.
        saved = decide(self.field, cursor, "new", target, note_id="upper-4",
                       body="A further upper fixture material", sources=[SOURCE])
        self.assertEqual(saved["cell"], local["entry"])
        after_upper = encounter(self.field, cursor=cursor)
        upper_pressure = candidate_at(after_upper, local["entry"])["write_pressure"]
        self.assertEqual(upper_pressure["current_units"], 5)
        self.assertGreaterEqual(upper_pressure["pressure"], before["pressure"])

        child, share = supporting_child(after_upper, parent)
        written = decide(self.field, cursor, "new", child["id"], note_id="lower.v1",
                         body="A lower observation supporting the same physical locality.", sources=[SOURCE])
        self.assertEqual(written["cell"], child["cell"])
        self.assertEqual(written["cell"][0], 1)
        after_lower = encounter(self.field, cursor=cursor)
        pressure = candidate_at(after_lower, local["entry"])["write_pressure"]
        self.assertEqual(pressure["demand_units"], upper_pressure["demand_units"])
        self.assertEqual(pressure["support_q16"], share)
        self.assertTrue(pressure["support_complete"])
        self.assertLess(pressure["pressure"], upper_pressure["pressure"])
        found = next(item for item in after_lower["items"] if item["id"] == "lower.v1")
        self.assertEqual(found["sources"], [SOURCE])
        self.assertIn("coverage_down", found["via"])
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.placement_count(), 6)
            self.assertEqual(core.bridges(), ())

    def test_reobservation_reuse_revision_and_reopen_do_not_multiply_support(self):
        local = self.enter()
        cursor = local["cursor"]
        origin = local["entry"]
        decide(self.field, cursor, "new", candidate_at(local, origin)["id"], note_id="upper",
               body="Upper fixture judgment", sources=[SOURCE])
        child, share = supporting_child(local, address(origin))
        decide(self.field, cursor, "new", child["id"], note_id="lower.v1",
               body="First lower value", sources=[SOURCE])
        state_path = self.field / "core/current_state.json"
        initial_state = state_path.read_bytes()
        expected = candidate_at(encounter(self.field, cursor=cursor), origin)["write_pressure"]
        self.assertEqual(expected["support_q16"], share)

        for _ in range(3):
            repeated = encounter(self.field, cursor=cursor)
            self.assertEqual(candidate_at(repeated, origin)["write_pressure"], expected)
        self.assertEqual(state_path.read_bytes(), initial_state)

        reused = decide(self.field, cursor, "reuse", "lower.v1", note_id="lower.support",
                        body="Another expression of the existing lower observation.", sources=[UPDATED])
        self.assertEqual(reused["cell"], child["cell"])
        self.assertEqual(state_path.read_bytes(), initial_state)
        self.assertEqual(candidate_at(encounter(self.field, cursor=cursor), origin)["write_pressure"], expected)

        revised = decide(self.field, cursor, "revision", "lower.v1", note_id="lower.v2",
                         body="Corrected lower value", sources=[UPDATED])
        self.assertEqual(revised["cell"], child["cell"])
        revised_locality = encounter(self.field, cursor=cursor)
        self.assertEqual(candidate_at(revised_locality, origin)["write_pressure"], expected)
        current = decide(self.field, cursor, "recall", "lower.v2")["item"]
        self.assertEqual(current["sources"], [UPDATED])
        self.assertEqual(current["text"], "Corrected lower value")
        self.assertFalse(describe(self.field, "lower.v1")["current"])
        self.assertEqual(describe(self.field, "lower.v1")["sources"], [SOURCE])
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.placement_count(), 2)
            self.assertEqual(core.bridges(), ())

        # Opening a new encounter reconstructs observations from the persisted field.
        fresh = self.enter()
        self.assertEqual(candidate_at(fresh, origin)["write_pressure"], expected)
        self.assertEqual(next(item for item in fresh["items"] if item["id"] == "lower.v2")["cell"],
                         child["cell"])

    def test_complete_incoming_child_is_shown_even_when_parent_down_omits_it(self):
        parent = address((0, 67, 5))
        missing = address((1, 94, -30))
        down = {member.target for member in expand_physical_coverage(parent, "coverage_down").members}
        self.assertNotIn(missing, down)
        self.assertIn(parent, {member.target for member in expand_physical_coverage(missing, "coverage_up").members})
        save_statement(self.field, "witness", "Upper coverage witness", [SOURCE], (67, 5), None)
        local = self.enter(layers=(0, 1), preferred=(0, 67, 5))
        self.assertEqual(local["entry"], [0, 67, 5])
        candidate = candidate_at(local, coordinates(missing))
        self.assertEqual(candidate["write_pressure"]["current_units"], 0)
        self.assertEqual(candidate["write_pressure"]["pressure"], 51)

    def test_default_scope_stays_layer_zero_and_direct_save_requires_opt_in(self):
        local = self.enter(layers=None)
        self.assertEqual(local["physical_layers"], [0])
        self.assertEqual(local["write_policy_id"], ACTIVE_SEMANTIC_WRITE_POLICY_ID)
        self.assertEqual({candidate["cell"][0] for candidate in local["cells"]}, {0})
        with self.assertRaises(ActiveSemanticWritePolicyError):
            save_statement(self.field, "not-selected", "No opt-in", [SOURCE], (0, 0), None, layer=1)
        saved = save_statement(
            self.field, "selected", "Explicit lower placement", [SOURCE], (0, 0), None,
            layer=1, write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
        )
        self.assertEqual(saved["cell"], [1, 0, 0])
        self.assertEqual(describe(self.field, "selected")["sources"], [SOURCE])
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(core.bridges(), ())

    def make_source_repository(self):
        repo = self.root / "evidence source"
        repo.mkdir()
        git = ["git", "-C", str(repo), "-c", "user.name=Test",
               "-c", "user.email=test@example.invalid", "-c", "commit.gpgSign=false"]
        subprocess.run([*git, "init", "-q"], check=True, capture_output=True)
        (repo / "material.py").write_text("def observation():\n    return 42\n", encoding="utf-8")
        subprocess.run([*git, "add", "material.py"], check=True, capture_output=True)
        subprocess.run([*git, "commit", "-qm", "fixture evidence"], check=True, capture_output=True)
        commit = subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True,
                                text=True).stdout.strip()
        return repo, commit

    def run_cli(self, cli, *args, body=None, check=True):
        result = subprocess.run(
            [sys.executable, "-I", str(cli), "project", "--field", str(self.field), *map(str, args)],
            cwd=self.root, input=body, capture_output=True, text=True,
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_checkout_cli_save_requires_explicit_nonzero_layer_policy(self):
        cli = ROOT / "skills/nollm-repository-memory/scripts/memory.py"
        repo, commit = self.make_source_repository()
        cite = ("--repo", repo, "--cite", "material.py#L1-L2")
        denied = self.run_cli(cli, "save", "implicit", "--at", 0, 0, "--layer", 1,
                              *cite, body="Implicit lower writing", check=False)
        self.assertNotEqual(denied.returncode, 0)
        self.assertIn("layer", denied.stderr)
        saved = json.loads(self.run_cli(
            cli, "save", "explicit", "--at", 0, 0, "--layer", 1,
            "--experimental-multilayer", *cite, body="Explicit lower writing",
        ).stdout)
        self.assertEqual(saved["cell"], [1, 0, 0])
        shown = json.loads(self.run_cli(cli, "show", "explicit").stdout)
        self.assertEqual(shown["sources"], [f"{commit}:material.py#L1-L2"])
        source = self.run_cli(cli, "source", "--id", "explicit", "--repo", repo).stdout
        self.assertIn("2\t    return 42", source)
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(core.bridges(), ())

    def test_installed_cli_carries_policy_across_processes_and_terminal_choices(self):
        cli = install(self.root / "installed runtime") / "scripts/memory.py"
        repo, commit = self.make_source_repository()
        cite = ("--repo", repo, "--cite", "material.py#L1-L2")
        cursor = self.root / "encounter.json"

        def meet(*args, body=None):
            return json.loads(self.run_cli(cli, "encounter", "--cursor-file", cursor,
                                          *args, body=body).stdout)

        def enter():
            page = meet("--via", "vertical", "--beam", 32, "--limit", 20,
                        "--layers", *LAYERS, "--pressure")
            while page["kind"] != "locality":
                page = meet(choose_page_candidate(page)["id"])
            self.assertEqual(page["write_policy_id"], EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
            self.assertEqual(page["physical_layers"], list(LAYERS))
            return page

        local = enter()
        origin = local["entry"]
        created = meet("--new", candidate_at(local, origin)["id"], "--id", "upper",
                       *cite, body="Upper fixture result")
        self.assertEqual(created["cell"], origin)
        self.assertFalse(cursor.exists())

        local = enter()
        child, _ = supporting_child(local, address(origin))
        created = meet("--new", child["id"], "--id", "lower.v1", *cite,
                       body="Lower fixture evidence")
        self.assertEqual(created["cell"], child["cell"])
        self.assertEqual(created["cell"][0], 1)
        self.assertFalse(cursor.exists())
        state_path = self.field / "core/current_state.json"
        initial = state_path.read_bytes()

        local = enter()
        lower = next(item for item in local["items"] if item["id"] == "lower.v1")
        self.assertEqual(lower["sources"], [f"{commit}:material.py#L1-L2"])
        pressure = candidate_at(local, origin)["write_pressure"]
        reused = meet("--reuse", "lower.v1", "--id", "lower.support", *cite,
                      body="Another expression of the same lower evidence")
        self.assertEqual(reused["cell"], child["cell"])
        self.assertFalse(cursor.exists())
        self.assertEqual(state_path.read_bytes(), initial)

        local = enter()
        self.assertEqual(candidate_at(local, origin)["write_pressure"], pressure)
        revised = meet("--revise", "lower.v1", "--id", "lower.v2", *cite,
                       body="Revised lower interpretation")
        self.assertEqual(revised["cell"], child["cell"])
        self.assertFalse(cursor.exists())

        local = enter()
        self.assertEqual(candidate_at(local, origin)["write_pressure"], pressure)
        recalled = meet("--recall", "lower.v2")
        self.assertEqual(recalled["item"]["text"], "Revised lower interpretation")
        self.assertEqual(recalled["item"]["sources"], [f"{commit}:material.py#L1-L2"])
        self.assertFalse(cursor.exists())
        self.assertIn("2\t    return 42", self.run_cli(
            cli, "source", "--id", "lower.v1", "--repo", repo,
        ).stdout)
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.placement_count(), 2)
            self.assertEqual(core.bridges(), ())


if __name__ == "__main__":
    unittest.main()
