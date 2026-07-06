"""HCG1 file-first capture gateway.

This package only adapts host-provided files to CI1 capture and CI1 explicit
visibility reads through HX1's trusted host bridge.
"""

from .gateway import capture, capture_from_text, read, read_from_text

__all__ = ["capture", "capture_from_text", "read", "read_from_text"]
