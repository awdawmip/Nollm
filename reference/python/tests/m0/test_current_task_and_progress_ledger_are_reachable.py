from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_current_task_and_progress_ledger_are_reachable() -> None:
    active = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    for relative in (
        "docs/project/tasks/NOLLM_CSTALD_BASELINE_CORRECTION_TASK_20260711.md",
        "docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md",
    ):
        path = ROOT / relative
        assert path.is_file()
        assert path.name in active
