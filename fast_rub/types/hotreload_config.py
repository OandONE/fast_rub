from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from watchfiles import Change


def _default_hotreload_filter(_change: Change, path: str) -> bool:
    """Watch Python files and ignore __pycache__."""
    return path.endswith(".py") and "__pycache__" not in path


@dataclass(slots=True)
class HotReloadConfig:
    """Settings for FastRub's development-time hot reloader"""

    enabled: bool = True

    # Paths. None means the directory containing the entry-point script.
    watch_paths: Sequence[str | Path] | None = None

    # Filtering. Pass None to disable filtering and watch every file change.
    watch_filter: Callable[[Change, str], bool] | None = _default_hotreload_filter

    # Watch settings (milliseconds)
    debounce: int = 1000
    step: int = 50
    recursive: bool = True

    # Polling
    force_polling: bool | None = None
    poll_delay_ms: int = 300

    # Advanced watchfiles options
    rust_timeout: int | None = None
    debug: bool = False
    ignore_permission_denied: bool | None = None

    # Process management
    shutdown_timeout: float = 5.0

    def __post_init__(self) -> None:
        if self.debounce < 0:
            raise ValueError("debounce must be >= 0")
        if self.step < 0:
            raise ValueError("step must be >= 0")
        if self.poll_delay_ms < 0:
            raise ValueError("poll_delay_ms must be >= 0")
        if self.shutdown_timeout < 0:
            raise ValueError("shutdown_timeout must be >= 0")
        if self.rust_timeout is not None and self.rust_timeout < 0:
            raise ValueError("rust_timeout must be >= 0 or None")
        if isinstance(self.watch_paths, (str, bytes)):
            raise TypeError("watch_paths must be a sequence of paths, not a single string")
