"""Adapter boundary for Dream Geometry V2.

Allowed: thin, host-controlled, read-only typed shells over sealed public
surfaces.
Forbidden: defining geometry math, bypassing ledgers, recomputing geometry
internals, plugin install, CLI registration, OpenClaw runtime, or memory writes.
"""

from .errors import DI1ErrorCode
from .integration_shell import IntegrationShell, capabilities, handle
from .types import CapabilitiesInvocation, IntegrationReadContext, IntegrationResponse, RecallInvocation

__all__ = [
    "CapabilitiesInvocation",
    "DI1ErrorCode",
    "IntegrationReadContext",
    "IntegrationResponse",
    "IntegrationShell",
    "RecallInvocation",
    "capabilities",
    "handle",
]
