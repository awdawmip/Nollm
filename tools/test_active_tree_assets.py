"""Regression cases for retained research evidence and tracked directory links."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import check_active_tree_assets as assets


class ActiveTreeAssetsTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        override = patch.object(assets, "ROOT", self.root)
        override.start()
        self.addCleanup(override.stop)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return relative

    def test_followup_report_directory_links_resolve_to_tracked_contents(self):
        prefix = "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/"
        directories = ("answers", "reads", "clean/reads", "clean/answers",
                       "continuation/answers", "continuation/reads")
        readme = self.write(prefix + "README.md", "\n".join(
            f"[evidence]({directory}/)" for directory in directories))
        paths = [readme]
        for directory in directories:
            paths.append(self.write(prefix + directory + "/N.txt", "recorded evidence\n"))
        self.assertEqual(assets.local_markdown_link_errors(paths), [])

    def test_missing_target_and_only_untracked_directory_stay_broken(self):
        readme = self.write("README.md", "[missing](missing.md)\n[untracked](drafts/)\n")
        self.write("drafts/note.md", "This file is outside the tracked inventory.\n")
        self.assertEqual(assets.local_markdown_link_errors([readme]), [
            "README.md: broken tracked Markdown link missing.md",
            "README.md: broken tracked Markdown link drafts/",
        ])

    def test_retained_research_log_does_not_allow_a_new_sibling(self):
        agents = self.write("AGENTS.md", "Read the current project entry.\n")
        prefix = "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/reads/"
        retained = self.write(prefix + "L.jsonl", "{}\n")
        later = self.write(prefix + "later.jsonl", "{}\n")
        self.assertEqual(assets.validate([agents, retained]), [])
        self.assertEqual(assets.validate([agents, retained, later]), [
            f"{later}: JSONL is not an allowlisted fixture or retained research evidence",
        ])


if __name__ == "__main__":
    unittest.main()
