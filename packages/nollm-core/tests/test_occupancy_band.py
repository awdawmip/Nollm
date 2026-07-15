from __future__ import annotations

from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, PutCommand


CELL = GeometryAddress("default_dream_v1", "default", 0, 0, 0)


def test_occupancy_band_is_an_exact_atom_count_policy(tmp_path) -> None:
    with CoreRuntime(tmp_path) as runtime:
        assert runtime.occupancy_band(CELL) == "normal"
        runtime.apply_batch(tuple(PutCommand(MemoryAtom(f"a{i}", str(i)), CELL) for i in range(8)))
        assert runtime.occupancy_band(CELL) == "dense"
        runtime.apply_batch(tuple(PutCommand(MemoryAtom(f"a{i}", str(i)), CELL) for i in range(8, 32)))
        assert runtime.occupancy_band(CELL) == "overloaded"
        assert not hasattr(runtime, "density_state")
