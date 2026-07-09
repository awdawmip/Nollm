"""GRF kernel registry and compression estimates."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .coverage_template import COVERAGE_DOWN, COVERAGE_UP, LATERAL, CoverageTemplate, CoverageTemplateCompiler, KernelEntry
from .json_canonical import canonical_dumps

KERNEL_DIRECTIONS = (COVERAGE_UP, COVERAGE_DOWN, LATERAL, "bridge", "return")


@dataclass(frozen=True)
class KernelKey:
    profile_id: str
    direction: str
    layer_phase: str
    kernel_type: str

    def stable_key(self) -> tuple[str, str, str, str]:
        return (self.profile_id, self.direction, self.layer_phase, self.kernel_type)


@dataclass(frozen=True)
class KernelCompressionReport:
    kernel_count: int
    raw_entries: int
    json_size: int
    binary_size: int
    csr_size: int
    delta_size: int
    compressed_size: int
    compression_ratio: str
    reconstruction_error: int
    shard_count_assumption: int

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


class KernelRegistry:
    def __init__(self) -> None:
        self._templates: dict[KernelKey, tuple[KernelEntry, ...]] = {}

    def register_template(self, key: KernelKey, entries: tuple[KernelEntry, ...]) -> None:
        if not entries:
            raise ValueError("kernel entries cannot be empty")
        self._templates[key] = tuple(sorted(entries, key=lambda item: (item.layer_delta, item.dq, item.dr, item.weight_q16, item.kernel_type, item.flags)))

    def compile_profiles(self, profile_ids: tuple[str, ...]) -> None:
        compiler = CoverageTemplateCompiler()
        for profile_id in profile_ids:
            for direction in (COVERAGE_UP, COVERAGE_DOWN, LATERAL):
                template = compiler.compile(profile_id, direction)
                self.register_template(KernelKey(profile_id, direction, "phase:any", "coverage_template"), template.entries)
            self.register_template(KernelKey(profile_id, "return", "phase:any", "return"), (KernelEntry(0, 0, 0, 65536, "return", ("return",)),))
            self.register_template(KernelKey(profile_id, "bridge", "phase:any", "bridge"), (KernelEntry(0, 0, 0, 32768, "bridge", ("bridge_placeholder",)),))

    def templates(self) -> tuple[tuple[KernelKey, tuple[KernelEntry, ...]], ...]:
        return tuple((key, self._templates[key]) for key in sorted(self._templates, key=lambda item: item.stable_key()))

    def coverage_templates(self) -> tuple[CoverageTemplate, ...]:
        compiler = CoverageTemplateCompiler()
        out = []
        for key, _entries in self.templates():
            if key.direction in (COVERAGE_UP, COVERAGE_DOWN, LATERAL):
                out.append(compiler.compile(key.profile_id, key.direction))
        return tuple(out)

    def compression_report(self, shard_count_assumption: int) -> KernelCompressionReport:
        payload = tuple((key.stable_key(), tuple(entry.__dict__.copy() for entry in entries)) for key, entries in self.templates())
        json_size = len(canonical_dumps(payload))
        raw_entries = sum(len(entries) for _key, entries in self.templates())
        binary_size = raw_entries * 24
        csr_size = raw_entries * 16 + len(self._templates) * 8
        delta_size = raw_entries * 12 + len(self._templates) * 4
        compressed_size = min(binary_size, csr_size, delta_size)
        return KernelCompressionReport(len(self._templates), raw_entries, json_size, binary_size, csr_size, delta_size, compressed_size, f"{compressed_size}/{json_size}", 0, shard_count_assumption)

    def digest(self) -> str:
        return sha256(canonical_dumps(tuple((key.stable_key(), tuple(entry.__dict__.copy() for entry in entries)) for key, entries in self.templates()))).hexdigest()
