"""Cross-platform current and peak process RSS sampling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class ResourceSample:
    current_rss_bytes: int
    peak_rss_bytes: int
    backend_name: str

    def __post_init__(self) -> None:
        if self.current_rss_bytes < 1 or self.peak_rss_bytes < self.current_rss_bytes:
            raise ValueError("invalid RSS sample")
        if not self.backend_name:
            raise ValueError("backend_name must be non-empty")

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


def sample_process_resources(platform_name: str | None = None, proc_status_text: str | None = None, resource_usage: object | None = None) -> ResourceSample:
    platform_name = platform_name or sys.platform
    if platform_name == "win32":
        if sys.platform != "win32":
            raise RuntimeError("Windows resource backend requires Windows")
        return _windows_sample()
    if platform_name.startswith("linux"):
        text = proc_status_text
        if text is None:
            text = Path("/proc/self/status").read_text(encoding="utf-8")
        return _linux_sample(text)
    if platform_name == "darwin":
        usage = resource_usage
        if usage is None:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
        peak = int(usage.ru_maxrss)
        return ResourceSample(peak, peak, "macos_resource_ru_maxrss")
    raise RuntimeError(f"unsupported resource platform: {platform_name}")


def _linux_sample(text: str) -> ResourceSample:
    values = {}
    for line in text.splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, value, unit = line.split()[:3]
            if unit != "kB":
                raise ValueError("unexpected /proc RSS unit")
            values[key.rstrip(":")] = int(value) * 1024
    if "VmRSS" not in values or "VmHWM" not in values:
        raise ValueError("/proc/self/status missing VmRSS or VmHWM")
    return ResourceSample(values["VmRSS"], values["VmHWM"], "linux_proc_self_status")


def _windows_sample() -> ResourceSample:
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = (ctypes.c_void_p, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD)
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return ResourceSample(int(counters.WorkingSetSize), int(counters.PeakWorkingSetSize), "windows_GetProcessMemoryInfo")
