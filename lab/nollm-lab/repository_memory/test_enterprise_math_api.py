"""Use the research API with source windows supplied by an existing reader."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from install_skill import install


class ResearchApiTest(unittest.TestCase):
    def test_source_reader_save_revision_and_reopen_without_git_checkout(self):
        # These are fixture source references, supplied as an MCP source reader would.
        original = "0123456789abcdef0123456789abcdef01234567:lemma.md#L2-L4"
        updated = "89abcdef0123456789abcdef0123456789abcdef:lemma.md#L5-L8"
        review = "89abcdef0123456789abcdef0123456789abcdef:review.md#L1-L3"
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = install(root / "skill") / "scripts/runtime"
            field = root / "field"

            def call(operation, *args):
                # Every API call starts with fresh runtime objects, outside any Git checkout.
                code = (
                    "import json,sys; from pathlib import Path; "
                    "sys.path.insert(0,sys.argv[1]); "
                    "from enterprise_math import research; "
                    "result=getattr(research,sys.argv[3])(Path(sys.argv[2]),"
                    "*json.loads(sys.argv[4])); print(json.dumps(result))"
                )
                output = subprocess.run(
                    [sys.executable, "-I", "-c", code, str(runtime), str(field),
                     operation, json.dumps(args)], cwd=root,
                    check=True, capture_output=True, text=True,
                )
                return json.loads(output.stdout)

            old_body = "Original bound\nOnly odd moduli were covered by this source."
            new_body = "Extended bound\nThe later source covers the stated even cases too."
            first = call("save_statement", "bound.v1", old_body, [original], (0, 0), None)
            self.assertEqual(first["cell"], [0, 0, 0])
            self.assertTrue(call("describe", "bound.v1")["current"])
            with self.assertRaises(subprocess.CalledProcessError):
                call("save_statement", "bound.v1", old_body, [original], (0, 0), None)
            with self.assertRaises(subprocess.CalledProcessError):
                call("save_statement", "bound.v1", "Different content", [original], (1, 0), None)
            self.assertEqual(call("describe", "bound.v1")["text"], old_body)
            support_body = "Independent expression\nAnother source confirms the original odd-modulus bound."
            support = call("save_statement", "bound.support", support_body, [review], None, None, "bound.v1")
            self.assertEqual(support["cell"], first["cell"])
            supporting = call("describe", "bound.support")
            self.assertFalse(supporting["current"])
            self.assertEqual(supporting["sources"], [review])
            self.assertEqual(supporting["text"], support_body)
            self.assertTrue(call("describe", "bound.v1")["current"])
            second = call("save_statement", "bound.v2", new_body, [updated, review], None, "bound.v1")
            self.assertEqual(second, {"id": "bound.v2", "cell": [0, 0, 0], "revises": "bound.v1"})
            with self.assertRaises(subprocess.CalledProcessError):
                call("save_statement", "bound.v2", new_body, [updated, review], None, "bound.v1")

            previous = call("describe", "bound.v1")
            self.assertEqual(previous["text"], old_body)
            self.assertEqual(previous["sources"], [original])
            self.assertFalse(previous["current"])
            self.assertEqual(call("describe", "bound.support"), supporting)

            current = call("describe", "bound.v2")
            self.assertEqual(current["text"], new_body)
            self.assertEqual(current["sources"], [updated, review])
            self.assertEqual(current["revises"], "bound.v1")
            self.assertTrue(current["current"])

            call("save_statement", "other", "A second proposition", [original], (40, 0), None)
            self.assertEqual(call("links"), [])
            call("stitch", "bound-to-other", "bound.v2", "other")
            state_file = field / "core" / "current_state.json"
            before_read = state_file.read_bytes()
            link, = call("links", "bound-to-other")
            self.assertEqual(link["bridge_id"], "bound-to-other")
            self.assertEqual(link["from_anchor"]["cells"][0]["q"], 0)
            self.assertEqual(link["to_anchor"]["cells"][0]["q"], 40)
            self.assertEqual(call("links"), [link])
            self.assertEqual(call("links", "absent-link"), [])
            self.assertEqual(state_file.read_bytes(), before_read)
            call("unstitch", "bound-to-other")
            self.assertEqual(call("links", "bound-to-other"), [])
            self.assertTrue(call("describe", "bound.v2")["current"])


if __name__ == "__main__":
    unittest.main()
