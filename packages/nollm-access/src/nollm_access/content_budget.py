"""Write-time limits on current native content, independent of display paging.

The Host chooses the text and physical placement. A policy limits current Core
atoms and their UTF-8 bodies; stored history and supporting Evidence are separate
material. The optional file is read when AccessRuntime opens the field.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from nollm_core import AtomHandle, CoreRuntime, GeometryAddress

from .statement_store import _atomic_write


CONTENT_BUDGET_SCHEMA_VERSION = "nollm_access_content_budget_v1"


@dataclass(frozen=True)
class LayerContentBudget:
    max_cell_atoms: int | None = None
    max_cell_utf8_bytes: int | None = None
    max_layer_cells: int | None = None
    max_layer_utf8_bytes: int | None = None

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{name} must be a nonnegative integer or null")


class ContentBudgetExceeded(ValueError):
    def __init__(self, address: GeometryAddress, metric: str,
                 limit: int, before: int, after: int) -> None:
        self.address = address
        self.metric = metric
        self.limit = limit
        self.before = before
        self.after = after
        super().__init__(
            f"content budget exceeded at L{address.layer}({address.q},{address.r}): "
            f"{metric} {before} -> {after}, limit {limit}; "
            "Host must reform the content or choose another observed placement"
        )


@dataclass(frozen=True)
class ContentBudgetPolicy:
    layers: dict[int, LayerContentBudget]
    profile_id: str = "default_dream_v1"
    chart_id: str = "default"

    def __post_init__(self) -> None:
        if not isinstance(self.layers, dict):
            raise TypeError("content budget layers must be a dict")
        if any(not isinstance(value, str) or not value for value in (self.profile_id, self.chart_id)):
            raise ValueError("content budget profile_id and chart_id must be nonempty strings")
        for layer, limits in self.layers.items():
            if type(layer) is not int or not isinstance(limits, LayerContentBudget):
                raise TypeError("content budget layers map integers to LayerContentBudget")

    def limits_for(self, cell: GeometryAddress) -> LayerContentBudget | None:
        if (cell.profile_id, cell.chart_id) != (self.profile_id, self.chart_id):
            return None
        return self.layers.get(cell.layer)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": CONTENT_BUDGET_SCHEMA_VERSION,
            "profile_id": self.profile_id,
            "chart_id": self.chart_id,
            "layers": {str(layer): {key: value for key, value in asdict(limits).items()
                                      if value is not None}
                       for layer, limits in sorted(self.layers.items())},
        }

    @classmethod
    def from_mapping(cls, value: dict[str, object]) -> ContentBudgetPolicy:
        allowed = {"schema_version", "profile_id", "chart_id", "layers"}
        if (not isinstance(value, dict) or set(value) - allowed
                or value.get("schema_version") != CONTENT_BUDGET_SCHEMA_VERSION
                or not isinstance(value.get("layers"), dict)):
            raise ValueError("invalid content budget policy")
        layers = {}
        for key, limits in value["layers"].items():
            layer = int(key)
            if str(layer) != key or not isinstance(limits, dict):
                raise ValueError("content budget layer keys must be canonical integer strings")
            layers[layer] = LayerContentBudget(**limits)
        return cls(layers, value.get("profile_id", "default_dream_v1"),
                   value.get("chart_id", "default"))

    @classmethod
    def load(cls, workspace: Path) -> ContentBudgetPolicy | None:
        path = Path(workspace) / "access" / "content_budget.json"
        try:
            data = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        return cls.from_mapping(json.loads(data))

    def save(self, workspace: Path) -> None:
        payload = json.dumps(self.to_mapping(), ensure_ascii=False, indent=2) + "\n"
        _atomic_write(Path(workspace) / "access" / "content_budget.json", payload.encode("utf-8"))


def validate_content_change(
    core: CoreRuntime,
    policy: ContentBudgetPolicy | None,
    target: GeometryAddress,
    payload_utf8: str,
    *,
    removing: AtomHandle | None = None,
) -> None:
    """Check the proposed current occupancy under the caller's operation lease.

    Existing over-budget fields remain readable and can be progressively reduced:
    a metric already over its limit may stay equal or decrease, but cannot grow.
    This permits re-formation without dropping stored Evidence or history.
    """
    if policy is None or (limits := policy.limits_for(target)) is None:
        return
    previous = core.get(removing) if removing is not None else None
    old_cell = removing.geometry_address if removing is not None else None
    old_bytes = len(previous.payload_utf8.encode("utf-8")) if previous is not None else 0
    new_bytes = len(payload_utf8.encode("utf-8"))
    target_atoms = core.atoms_at(target)
    cell_atoms_before = len(target_atoms)
    cell_bytes_before = sum(len(atom.payload_utf8.encode("utf-8")) for _, atom in target_atoms)
    same_cell = old_cell == target
    cell_atoms_after = cell_atoms_before + 1 - int(same_cell)
    cell_bytes_after = cell_bytes_before + new_bytes - (old_bytes if same_cell else 0)

    def check(metric: str, before: int, after: int) -> None:
        limit = getattr(limits, "max_" + metric)
        if limit is not None and after > limit and after > before:
            raise ContentBudgetExceeded(target, metric, limit, before, after)

    check("cell_atoms", cell_atoms_before, cell_atoms_after)
    check("cell_utf8_bytes", cell_bytes_before, cell_bytes_after)
    if limits.max_layer_cells is None and limits.max_layer_utf8_bytes is None:
        return

    def in_layer(cell: GeometryAddress) -> bool:
        return (cell.profile_id, cell.chart_id, cell.layer) == (
            target.profile_id, target.chart_id, target.layer,
        )

    # A whole-layer limit measures this declared layer, not all descendant text.
    # The current Core already holds a state snapshot; no relationship index is
    # introduced. Per-cell-only policies skip this traversal altogether.
    layer_cells = tuple(cell for cell in core.occupied_cells() if in_layer(cell))
    layer_cells_before = len(layer_cells)
    layer_cells_after = layer_cells_before + int(cell_atoms_after > 0) - int(cell_atoms_before > 0)
    removed_in_layer = old_cell is not None and in_layer(old_cell)
    if removed_in_layer and not same_cell and len(core.atoms_at(old_cell)) == 1:
        layer_cells_after -= 1
    check("layer_cells", layer_cells_before, layer_cells_after)
    if limits.max_layer_utf8_bytes is not None:
        layer_bytes_before = sum(
            len(atom.payload_utf8.encode("utf-8"))
            for cell in layer_cells for _, atom in core.atoms_at(cell)
        )
        layer_bytes_after = layer_bytes_before + new_bytes - (old_bytes if removed_in_layer else 0)
        check("layer_utf8_bytes", layer_bytes_before, layer_bytes_after)
