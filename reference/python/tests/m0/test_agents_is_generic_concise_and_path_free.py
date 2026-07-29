import hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]


def test_agents_is_the_canonical_empty_overlay() -> None:
    data = (ROOT / "AGENTS.md").read_bytes()
    assert data == b""
    assert hashlib.sha256(data).hexdigest() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
