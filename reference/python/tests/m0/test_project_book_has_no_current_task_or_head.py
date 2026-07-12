from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_project_book_has_no_current_task_or_head() -> None:
    book = (ROOT / "docs/project/NOLLM_PROJECT_BOOK_V3_1_CORE_PURITY_AND_EVOLVING_BASELINES_20260711.md").read_text(encoding="utf-8")
    for forbidden in ("HEAD", "current task", "当前任务", "当前阶段", "任务文件名", "c040915e"):
        assert forbidden not in book
