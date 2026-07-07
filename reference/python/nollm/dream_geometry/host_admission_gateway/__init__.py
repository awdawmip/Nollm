"""HAG1 file-first explicit admission gateway."""

from .gateway import admit, admit_from_text
from .serialization import canonical_json

__all__ = ["admit", "admit_from_text", "canonical_json"]
