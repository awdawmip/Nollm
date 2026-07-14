from __future__ import annotations

from dataclasses import dataclass, replace

from nollm_core import SurfaceOrderInfo


@dataclass(frozen=True)
class SurfaceBudgetProfile:
    page_size: int
    max_pages: int
    max_surface_cells: int
    page_overhead_units: int
    cell_preview_units: int
    max_projection_units: int
    selected_entries_limit: int
    max_descent_depth: int
    hard_max_order: int = 2
    max_calls: int = 12

    def __post_init__(self) -> None:
        values = (
            self.page_size,
            self.max_pages,
            self.max_surface_cells,
            self.page_overhead_units,
            self.cell_preview_units,
            self.max_projection_units,
            self.selected_entries_limit,
            self.max_descent_depth,
            self.max_calls,
        )
        if any(type(value) is not int or value <= 0 for value in values):
            raise ValueError("Surface budget values must be positive integers")
        if self.page_size > 8:
            raise ValueError("Surface page_size cannot exceed 8")
        if type(self.hard_max_order) is not int or not 0 <= self.hard_max_order <= 2:
            raise ValueError("hard_max_order must be between 0 and 2")
        if self.max_descent_depth > self.hard_max_order:
            raise ValueError("max_descent_depth cannot exceed hard_max_order")


@dataclass(frozen=True)
class ActiveSurfaceSelection:
    info: SurfaceOrderInfo
    estimated_pages: int
    projection_units: int
    overflow: bool


RECALL_SURFACE_BUDGET = SurfaceBudgetProfile(8, 4, 32, 8, 4, 160, 3, 2, 2, 12)
PLACEMENT_SURFACE_BUDGET = SurfaceBudgetProfile(8, 6, 48, 8, 4, 240, 1, 2, 2, 16)


def select_active_surface(
    infos: tuple[SurfaceOrderInfo, ...],
    budget: SurfaceBudgetProfile,
) -> ActiveSurfaceSelection:
    if type(infos) is not tuple or not infos or any(type(info) is not SurfaceOrderInfo for info in infos):
        raise TypeError("infos must be a non-empty SurfaceOrderInfo tuple")
    if type(budget) is not SurfaceBudgetProfile:
        raise TypeError("budget must be SurfaceBudgetProfile")
    eligible = tuple(info for info in infos if info.order <= budget.hard_max_order)
    if not eligible or tuple(info.order for info in eligible) != tuple(range(len(eligible))):
        raise ValueError("Surface order infos must be canonical and contiguous")
    if any(info.plane != eligible[0].plane for info in eligible):
        raise ValueError("Surface order infos must describe one plane")
    for info in eligible:
        pages, units = _cost(info, budget)
        if pages <= budget.max_pages and info.occupied_cell_count <= budget.max_surface_cells and units <= budget.max_projection_units:
            return ActiveSurfaceSelection(info, pages, units, False)
    fallback = eligible[-1]
    pages, units = _cost(fallback, budget)
    return ActiveSurfaceSelection(replace(fallback, overflow=True), pages, units, True)


def _cost(info: SurfaceOrderInfo, budget: SurfaceBudgetProfile) -> tuple[int, int]:
    pages = (info.occupied_cell_count + budget.page_size - 1) // budget.page_size
    units = pages * budget.page_overhead_units + info.occupied_cell_count * budget.cell_preview_units
    return pages, units
