"""Deterministic synthetic scale fixtures for GRF validation."""

from __future__ import annotations

from .validation_bench import ValidationItem

SCALE_VALIDATION_SEED = "grf1lm_scale_seed_v1"


def generate_scale_validation_items(concentrated_count: int = 1500, scattered_count: int = 2000, false_decoy_count: int = 1500) -> tuple[ValidationItem, ...]:
    items: list[ValidationItem] = []
    items.extend(_concentrated(concentrated_count))
    items.extend(_scattered(scattered_count))
    items.extend(_false_decoys(false_decoy_count))
    return tuple(items)


def _concentrated(count: int) -> tuple[ValidationItem, ...]:
    groups = tuple(f"cluster_{index:03d}" for index in range(max(1, count // 6)))
    items = []
    counter = 1
    for group in groups:
        for slot in range(6):
            if len(items) >= count:
                return tuple(items)
            items.append(ValidationItem(f"A{counter:03d}", f"{group} concentrated fact {slot} shares bounded kernel and source trail", group, f"source:scale:concentrated:{counter % 10}"))
            counter += 1
    return tuple(items)


def _scattered(count: int) -> tuple[ValidationItem, ...]:
    groups = tuple(f"scattered_{index:03d}" for index in range(max(1, count // 4)))
    items = []
    counter = 1
    for group in groups:
        for slot in range(4):
            if len(items) >= count:
                return tuple(items)
            items.append(ValidationItem(f"B{counter:03d}", f"{group} scattered fact {slot} links delayed window exact replay source", group, f"source:scale:scattered:{slot}"))
            counter += 1
    return tuple(items)


def _false_decoys(count: int) -> tuple[ValidationItem, ...]:
    families = (
        ("apple_company", "Apple company release policy", "apple_fruit", "apple fruit storage condition"),
        ("java_language", "Java language compiler type rule", "java_island", "Java island travel route"),
        ("java_coffee", "Java coffee roast profile", "java_language", "Java language runtime classpath"),
        ("mercury_planet", "Mercury planet orbit observation", "mercury_element", "Mercury element safety handling"),
        ("mercury_messenger", "Mercury messenger myth archive", "mercury_planet", "Mercury planet transit note"),
        ("python_language", "Python language package import rule", "python_snake", "python snake habitat marker"),
        ("python_package", "Python package release metadata", "python_language", "Python language syntax note"),
        ("saturn_planet", "Saturn planet ring observation", "saturn_car", "Saturn car service manual"),
        ("saturn_myth", "Saturn myth archive entry", "saturn_planet", "Saturn planet moon catalog"),
        ("opposite_hot", "opposite hot raises temperature", "opposite_cold", "opposite cold lowers temperature"),
        ("opposite_allow", "opposite allow grants access", "opposite_deny", "opposite deny blocks access"),
        ("opposite_increase", "opposite increase expands quota", "opposite_decrease", "opposite decrease shrinks quota"),
        ("bank_finance", "bank finance deposit rule", "bank_river", "river bank erosion marker"),
        ("stitch_chain_alpha", "stitch chain alpha hop one", "stitch_chain_alpha", "stitch chain alpha hop two"),
        ("spring_framework", "Spring framework dependency rule", "spring_season", "spring season pollen note"),
        ("ruby_language", "Ruby language gem install", "ruby_gemstone", "ruby gemstone clarity note"),
        ("go_language", "Go language module path", "go_game", "go game board position"),
        ("rust_language", "Rust language borrow rule", "rust_corrosion", "rust corrosion treatment"),
        ("swift_language", "Swift language package index", "swift_bird", "swift bird migration note"),
        ("scala_language", "Scala language typeclass note", "scala_music", "scala music interval note"),
        ("elm_language", "Elm language architecture update", "elm_tree", "elm tree disease note"),
        ("phoenix_framework", "Phoenix framework endpoint rule", "phoenix_myth", "phoenix myth rebirth story"),
        ("mars_planet", "Mars planet rover note", "mars_candy", "Mars candy packaging note"),
        ("pluto_dwarf_planet", "Pluto dwarf planet orbit note", "pluto_cartoon", "Pluto cartoon archive note"),
        ("jaguar_car", "Jaguar car service recall", "jaguar_animal", "jaguar animal habitat note"),
    )
    items = []
    counter = 1
    slot = 0
    while len(items) < count:
        family = families[slot % len(families)]
        round_index = slot // len(families)
        for _ in range(1):
            if len(items) >= count:
                break
            items.append(ValidationItem(f"C{counter:03d}", f"{family[1]} fixture {round_index} same name false friend guard", family[0], f"source:scale:false:{counter}"))
            counter += 1
            if len(items) >= count:
                break
            items.append(ValidationItem(f"C{counter:03d}", f"{family[3]} fixture {round_index} same name false friend guard", family[2], f"source:scale:false:{counter}"))
            counter += 1
        slot += 1
    return tuple(items)
