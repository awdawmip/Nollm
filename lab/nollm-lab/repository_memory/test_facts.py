import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from facts import compile_tree


class GitFacts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.run_git("init", "-q")

    def run_git(self, *args):
        return subprocess.check_output(["git", "-c", "user.name=Tester", "-c", "user.email=fixture@invalid",
                                        "-C", str(self.repo), *args])

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def snapshot(self):
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "fixture")
        return self.run_git("rev-parse", "HEAD").decode().strip()

    def rows(self, out, name):
        return [json.loads(l) for l in (out / (name + ".jsonl")).read_bytes().splitlines()]

    def test_arrow_candidates_bind_commit_blob_and_exclude_callbacks(self):
        path = "web/score.js"
        self.write(path, "const factor = 3,\n  score = (value) => value * factor;\nconst observed = items.map(x => x + 1);\n")
        pinned = self.snapshot()
        self.write(path, "const fromWorktree = x => x;\n")
        out = self.root / "js-compiled"
        compile_tree(self.repo, pinned, out)
        rows = self.rows(out, "symbols")
        self.assertEqual(len(rows), 1)
        symbol = rows[0]
        self.assertEqual((symbol["kind"], symbol["name"], symbol["path"], symbol["line"]),
                         ("js_arrow_binding_candidate", "score", path, 2))
        self.assertEqual(symbol["blob"], self.run_git("rev-parse", pinned + ":" + path).decode().strip())

    def test_python_evidence_scope_shadowing_and_versions(self):
        self.write("src/demo/__init__.py", "from . import sibling\n")
        self.write("src/demo/sibling.py", "class C:\n    async def run(self):\n        return 4\n")
        self.write("src/demo/main.py", 'from .sibling import C\nfrom elsewhere import never\nimport ambiguous\n"from foo import false_match"\n')
        self.write("ambiguous.py", "")
        self.write("src/ambiguous.py", "")
        self.write("broken.py", "class (\n# do not put this comment in diagnostics\n")
        self.write("data.bin", "test")
        os.symlink("sibling.py", self.repo / "src/demo/link.py")
        rev = self.snapshot()
        self.write("src/demo/sibling.py", "DELETED_FROM_WORKTREE = True\n")
        out = self.root / "tables"
        first = compile_tree(self.repo, rev, out)
        self.assertEqual(first, compile_tree(self.repo, rev, out))
        self.assertEqual(first["commit"], rev)
        files = {r["path"]:r for r in self.rows(out, "files")}
        self.assertEqual(len(files), 8)
        self.assertEqual(files["src/demo/link.py"]["parse"], "inventory_only")
        self.assertEqual(files["broken.py"]["parse"], "syntax_error")
        symbols = self.rows(out, "symbols")
        self.assertEqual([(r["qualname"], r["line"], r["end"]) for r in symbols], [("C",1,3),("C.run",2,3)])
        edges = self.rows(out,"edges")
        main = [r for r in edges if r["src"].endswith("/main.py")]
        self.assertEqual([(r["line"],r["dst"],r["confidence"]) for r in main],
                         [(1,"src/demo/sibling.py","exact"),(3,"ambiguous.py","candidate"),(3,"src/ambiguous.py","candidate")])
        self.assertTrue(any(r["rel"] == "py_from_member" and r["confidence"] == "candidate" for r in edges))
        for edge in edges:
            self.assertEqual(edge["src_blob"], files[edge["src"]]["blob"])
            self.assertEqual(edge["dst_blob"], files[edge["dst"]]["blob"])
        self.assertNotIn("do not put", (out/"diagnostics.jsonl").read_text())
        next_rev = self.snapshot()
        with self.assertRaises(FileExistsError):
            compile_tree(self.repo, next_rev, out)
        self.assertEqual(first, json.loads((out/"manifest.json").read_text()))

    def test_native_direct_includes_and_literal_cmake_paths(self):
        self.write("pkg/driver.cpp", '/*\n#include "phantom.h"\n*/\n#include "local.h"\n#include <detail/shared.h>\nconst char *s=R"tag(\n#include "phantom.h"\n)tag";\n')
        self.write("pkg/local.h", "struct Node {};\n")
        self.write("pkg/phantom.h", "")
        self.write("a/detail/shared.h", "")
        self.write("b/detail/shared.h", "")
        self.write("pkg/CMakeLists.txt", '# add_library(fake phantom.h)\nadd_library(core STATIC\n  "driver.cpp"\n  ${GENERATED}\n)\n#[=[\nadd_executable(wrong phantom.h)\n]=]\n')
        rev = self.snapshot()
        out = self.root / "facts"
        compile_tree(self.repo, rev, out)
        edges = self.rows(out, "edges")
        self.assertEqual({(r["rel"],r["line"],r["dst"],r["confidence"]) for r in edges}, {
            ("c_include",4,"pkg/local.h","exact"), ("c_include",5,"a/detail/shared.h","candidate"),
            ("c_include",5,"b/detail/shared.h","candidate"), ("cmake_source",3,"pkg/driver.cpp","exact"),
        })
        self.assertEqual({r["name"] for r in self.rows(out,"symbols")},{"core","Node"})

    def test_header_statements_and_attributed_type_names(self):
        self.write("api.hpp", """struct alignas(alignof(double)) Aligned final {};
struct [[nodiscard]] Item {};
typedef struct __attribute__((packed)) Wire {} Wire;
enum class State { yes, no };
inline int measure(int arg) {
    return int(arg);
    throw ContractError(arg);
}
EXPORT int compute(int value);
EXPORT const char* version(void);
EXPORT const Point &lookup(int id);
""")
        self.write("CMakeLists.txt", "add_library(alias ALIAS implementation)\n")
        self.write("implementation", "not a source argument\n")
        out = self.root / "facts"
        compile_tree(self.repo, self.snapshot(), out)
        symbols = self.rows(out, "symbols")
        self.assertEqual({row["name"] for row in symbols if row["kind"] == "c_type_candidate"},
                         {"Aligned", "Item", "Wire", "State"})
        self.assertEqual({row["name"] for row in symbols if row["kind"] == "c_function_candidate"},
                         {"measure", "compute", "version", "lookup"})
        self.assertEqual(self.rows(out, "edges"), [])


if __name__ == "__main__":
    unittest.main()
