from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs" / "architecture" / "D9_AUDIT_HISTORY_REEVALUATION.md"


class AuditHistoryReevaluationTests(unittest.TestCase):
    def test_d9_doc_records_support_role(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        for phrase in [
            "support organs",
            "not recall",
            "not source of truth",
            "not Dream Geometry center",
            "audit projection only",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
