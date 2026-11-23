"""Page-local binding reuse with real native Surface projections."""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from nollm_access import (
    AccessDecision, AccessRuntime, AccessSurfaceNavigator,
    EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, FileHandleStore, FileStatementStore,
    MemoryStatement, RECALL_SURFACE_BUDGET, SurfaceTraversalState,
)
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, PhysicalFieldScope


def cell(layer=0, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def decision(identity, action, **kwargs):
    return AccessDecision(
        f"page:{identity}:{action}", identity, action, reason_text="Host-authored test placement.",
        decided_by="fixture", write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, **kwargs,
    )


@contextmanager
def opened(root):
    with CoreRuntime(root) as core, AccessRuntime(
        core, FileStatementStore(root), FileHandleStore(root),
    ) as access:
        yield access, core


def put(access, identity, target, text=None):
    access.capture(MemoryStatement(identity, identity if text is None else text, "fixture:source"))
    return access.apply(decision(identity, "new", target_cell=target))


@contextmanager
def observed_reads(root):
    counts = {"bindings": [], "statements": []}
    read_bytes, get = Path.read_bytes, FileStatementStore.get

    def read(path):
        data = read_bytes(path)
        if path == root / "access" / "bindings.json":
            counts["bindings"].append(len(data))
        return data

    def statement(store, identity):
        counts["statements"].append(identity)
        return get(store, identity)

    with patch.object(Path, "read_bytes", read), patch.object(FileStatementStore, "get", statement):
        yield counts


class SurfacePageContentReadTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(prefix="nollm-surface-page-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.navigator = AccessSurfaceNavigator(self.root)

    def state(self, layers=(0,), page_size=8):
        return SurfaceTraversalState(
            "current-page", PhysicalFieldScope("default_dream_v1", "default", layers, layers[0]),
            replace(RECALL_SURFACE_BUDGET, page_size=page_size), 0,
        )

    def test_eight_cell_page_loads_bindings_once(self):
        with opened(self.root) as (access, _core):
            for index in range(8):
                put(access, f"short-{index}", cell(q=index), f"短判断 {index}")
        with observed_reads(self.root) as reads:
            page = self.navigator.page(self.state())
        self.assertEqual(len(page.cells), 8)
        self.assertEqual(len(reads["bindings"]), 1)
        self.assertEqual(reads["statements"], [f"short-{index}" for index in range(8)])
        self.assertEqual([view.statements[0].content_utf8 for view in page.cells],
                         [f"短判断 {index}" for index in range(8)])
        self.assertFalse(page.has_more)

    def test_new_request_reads_current_revision_without_stale_page_cache(self):
        with opened(self.root) as (access, _core):
            handle = put(access, "before", cell(), "原判断")
        state = self.state()
        first = self.navigator.page(state)
        with opened(self.root) as (access, _core):
            access.capture(MemoryStatement("after", "修订后的判断", "fixture:revision"))
            access.apply(decision("after", "revision_current", existing_handle=handle))
        with observed_reads(self.root) as reads:
            second = self.navigator.page(state)
        self.assertEqual(first.cells[0].statements[0].statement_id, "before")
        self.assertEqual(second.cells[0].statements[0].statement_id, "after")
        self.assertEqual(second.cells[0].statements[0].content_utf8, "修订后的判断")
        self.assertEqual(reads["statements"], ["after"])
        self.assertEqual(len(reads["bindings"]), 1)

    def test_shared_source_body_is_read_once_for_overlapping_surface_cells(self):
        with opened(self.root) as (access, _core):
            put(access, "shared-lower", cell(1, 1, 0))
        with observed_reads(self.root) as reads:
            page = self.navigator.page(self.state(layers=(0, 1)))
        # One real lower cell projects to several Order-0 observation cells.
        self.assertGreater(len(page.cells), 1)
        self.assertEqual({item.statement_id for view in page.cells for item in view.statements},
                         {"shared-lower"})
        self.assertEqual(reads["statements"], ["shared-lower"])
        self.assertEqual(len(reads["bindings"]), 1)

    def test_physical_pages_read_only_shown_candidate_bodies(self):
        positions = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 0, 1), (1, -1, 0), (1, 0, -1)]
        ids = {cell(*position): f"body-{index}" for index, position in enumerate(positions)}
        with opened(self.root) as (access, _core):
            for address, identity in ids.items():
                put(access, identity, address)
        page = self.navigator.page(self.state(layers=(0, 1), page_size=2))
        target = None
        while target is None:
            target = next((view for view in page.cells if (view.address.q, view.address.r) == (0, 0)), None)
            if target is None:
                page = self.navigator.continue_page(page)
        with observed_reads(self.root) as first_reads:
            first = self.navigator.open_physical_entries(page, target.candidate_id)
        self.assertEqual(first.total_candidate_count, 6)
        self.assertTrue(first.has_more)
        self.assertEqual(len(first.candidates), 2)
        self.assertEqual(first_reads["statements"], [ids[item.address] for item in first.candidates])
        self.assertEqual(len(first_reads["bindings"]), 1)
        with observed_reads(self.root) as second_reads:
            second = self.navigator.continue_physical_entries(first)
        self.assertEqual(second.total_candidate_count, 6)
        self.assertEqual(second_reads["statements"], [ids[item.address] for item in second.candidates])
        self.assertEqual(len(second_reads["bindings"]), 1)
        self.assertFalse(set(first_reads["statements"]) & set(second_reads["statements"]))
        with observed_reads(self.root) as last_reads:
            last = self.navigator.continue_physical_entries(second)
        self.assertFalse(last.has_more)
        self.assertIsNone(last.next_after)
        self.assertEqual(set(first_reads["statements"] + second_reads["statements"] + last_reads["statements"]),
                         set(ids.values()))

    def test_missing_binding_and_missing_body_keep_existing_preview_semantics(self):
        with opened(self.root) as (access, core):
            put(access, "missing-body", cell())
            put(access, "valid", cell(), "x" * 300)
            core.put(MemoryAtom("orphan", "no canonical binding"), cell())
            access.statement_store._path("missing-body").unlink()
        with observed_reads(self.root) as reads:
            page = self.navigator.page(self.state())
        view = page.cells[0]
        self.assertEqual(view.native_atom_count, 3)
        self.assertEqual(len(view.statements), 1)
        self.assertEqual(view.statements[0].statement_id, "valid")
        self.assertEqual(view.statements[0].content_utf8, "x" * 256)
        self.assertTrue(view.statements[0].text_truncated)
        self.assertFalse(view.truncated)
        self.assertEqual(view.remaining_count, 0)
        self.assertEqual(len(reads["bindings"]), 1)


if __name__ == "__main__":
    unittest.main()
