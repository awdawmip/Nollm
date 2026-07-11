from __future__ import annotations

from collections.abc import Mapping


def exact_mapping(value: object, keys: frozenset[str], name: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{name} must be an object")
    if frozenset(value) != keys:
        raise ValueError(f"{name} has unexpected or missing fields")
    return value


def exact_str(value: object, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} is required")
    return value


def exact_int(value: object, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    return value


def exact_list(value: object, name: str) -> list[object]:
    if type(value) is not list:
        raise TypeError(f"{name} must be an array")
    return value
