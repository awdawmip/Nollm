"""Compatibility entrypoint for the synthetic long-arm conformance."""

from run_synthetic_long_arm_conformance import validate


if __name__ == "__main__":
    import json
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True, indent=2))
