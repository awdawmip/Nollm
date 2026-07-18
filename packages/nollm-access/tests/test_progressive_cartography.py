from nollm_access import AccessDecision, AccessMemoryLoop, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement, ProgressiveAtlasPolicy
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom


def _seed_line(workspace, count: int) -> None:
    with CoreRuntime(workspace) as core:
        for q in range(count):
            core.put(
                MemoryAtom(f"atom-{q}", str(q)),
                GeometryAddress("default_dream_v1", "default", 0, q, 0),
            )


def test_progressive_root_is_complete_bounded_and_not_a_stable_prefix(tmp_path) -> None:
    _seed_line(tmp_path, 40)
    policy = ProgressiveAtlasPolicy(max_regions_per_page=32, max_prompt_bytes=65536)
    with AccessMemoryLoop(tmp_path) as loop:
        root = loop.build_progressive_atlas("root", policy)

    assert root.overflow is False
    assert root.occupied_field_cell_count == root.covered_source_cell_count == 40
    assert root.uncovered_source_cell_count == 0
    assert 1 <= len(root.regions) <= 32
    assert root.serialized_utf8_bytes <= 65536
    assert any(
        entry["entry_cell"]["q"] == 39
        for region in root.regions
        for entry in region.support_entries
    )


def test_300_cell_cartography_descends_by_complete_bounded_pages(tmp_path) -> None:
    _seed_line(tmp_path, 300)
    policy = ProgressiveAtlasPolicy(max_regions_per_page=32, max_prompt_bytes=65536, max_depth=8)
    with AccessMemoryLoop(tmp_path) as loop:
        page = loop.build_progressive_atlas("root", policy)
        visited_depth = 0
        while any(not region.leaf for region in page.regions) and visited_depth < policy.max_depth:
            region = max(page.regions, key=lambda item: item.source_cell_count)
            page = loop.open_progressive_region(page, region.region_id, f"depth:{visited_depth}")
            assert page.overflow is False
            assert page.uncovered_source_cell_count == 0
            assert len(page.regions) <= 32
            assert page.serialized_utf8_bytes <= 65536
            visited_depth += 1
    assert all(region.leaf for region in page.regions)


def test_1027_cell_root_remains_complete_and_under_64k(tmp_path) -> None:
    _seed_line(tmp_path, 1027)
    with AccessMemoryLoop(tmp_path) as loop:
        root = loop.build_progressive_atlas("root")

    assert root.overflow is False
    assert root.occupied_field_cell_count == root.covered_source_cell_count == 1027
    assert root.uncovered_source_cell_count == 0
    assert len(root.regions) == 32
    assert root.serialized_utf8_bytes <= 65536


def test_progressive_page_fails_stale_after_mutation(tmp_path) -> None:
    _seed_line(tmp_path, 40)
    with AccessMemoryLoop(tmp_path) as loop:
        root = loop.build_progressive_atlas("root")
    with CoreRuntime(tmp_path) as core:
        core.put(MemoryAtom("mutation", "mutation"), GeometryAddress("default_dream_v1", "default", 0, 100, 0))
    with AccessMemoryLoop(tmp_path) as loop:
        region = next(item for item in root.regions if not item.leaf)
        try:
            loop.open_progressive_region(root, region.region_id, "stale")
        except ValueError as error:
            assert "changed" in str(error)
        else:
            raise AssertionError("stale progressive page was accepted")


def test_local_detail_exposes_statements_hidden_beyond_region_representatives(tmp_path) -> None:
    cell = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    with CoreRuntime(tmp_path) as core:
        with AccessRuntime(core, FileStatementStore(tmp_path), FileHandleStore(tmp_path)) as access:
            for index in range(5):
                statement = MemoryStatement(f"statement-{index}", f"value {index}")
                access.capture(statement)
                access.apply(AccessDecision(
                    f"decision-{index}", statement.statement_id, "new", cell, None, None, "fixture", "llm",
                ))
    with AccessMemoryLoop(tmp_path) as loop:
        page = loop.build_progressive_atlas("root")
        region = page.regions[0]
        detail = loop.local_detail_page(page, region.region_id, "detail", limit=16)

    assert len(region.representative_statements) == 3
    assert detail.total_statement_count == 5
    assert [item["statement_id"] for item in detail.statements] == [f"statement-{index}" for index in range(5)]
    assert detail.has_more is False
