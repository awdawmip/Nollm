"""Compatibility entrypoint for the renamed synthetic contract conformance."""

from run_synthetic_lens_contract_conformance import validate


if __name__ == "__main__":
    import json
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True, indent=2))
