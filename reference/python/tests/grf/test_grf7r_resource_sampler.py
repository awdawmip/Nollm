from __future__ import annotations

from types import SimpleNamespace
import sys

import pytest

from nollm.grf.resource_sampler import sample_process_resources


def test_linux_proc_backend_parses_current_and_peak_bytes() -> None:
    sample = sample_process_resources("linux", "Name:\tpython\nVmHWM:\t2048 kB\nVmRSS:\t1024 kB\n")
    assert sample.current_rss_bytes == 1024 * 1024
    assert sample.peak_rss_bytes == 2048 * 1024
    assert sample.backend_name == "linux_proc_self_status"


def test_macos_resource_backend_has_explicit_peak_only_limitation() -> None:
    sample = sample_process_resources("darwin", resource_usage=SimpleNamespace(ru_maxrss=123456))
    assert sample.current_rss_bytes == sample.peak_rss_bytes == 123456
    assert sample.backend_name == "macos_resource_ru_maxrss"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows backend runs only on Windows")
def test_windows_process_memory_backend_runs() -> None:
    sample = sample_process_resources()
    assert sample.current_rss_bytes > 0
    assert sample.peak_rss_bytes >= sample.current_rss_bytes
    assert sample.backend_name == "windows_GetProcessMemoryInfo"


def test_windows_backend_is_guarded_on_non_windows() -> None:
    if sys.platform != "win32":
        with pytest.raises(RuntimeError, match="requires Windows"):
            sample_process_resources("win32")
