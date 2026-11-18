from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import sys
from pathlib import Path

from ..types.hotreload_config import HotReloadConfig


class HotReload:
    """Run the entry-point script in a child process and restart it on changes"""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        config: HotReloadConfig | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger("fast_rub.hotreload")
        self.config = config if config is not None else HotReloadConfig()
        self._process: asyncio.subprocess.Process | None = None
        self._stop_event: asyncio.Event | None = None

    def run_sync(self, script_path: str) -> None:
        """Synchronous wrapper; prefer run_async() inside async applications."""
        asyncio.run(self.run_async(script_path))

    async def run_async(self, script_path: str) -> None:
        try:
            import watchfiles
        except ImportError as exc:
            raise ImportError(
                "The 'watchfiles' package is required for hot reload. "
                "Install it with: pip install watchfiles"
            ) from exc

        script = Path(script_path).expanduser().resolve()
        if not script.is_file():
            raise FileNotFoundError(f"Hot reload entry-point not found: {script}")
        if self._process is not None:
            raise RuntimeError("This HotReload instance is already running.")

        watch_paths = self._resolve_watch_paths(script)
        env = os.environ.copy()
        env["FASTRUB_RELOAD_CHILD"] = "1"
        self._stop_event = asyncio.Event()

        self.logger.info(
            "Hot Reload فعال شد. مسیرهای تحت نظر: %s",
            ", ".join(watch_paths),
        )

        try:
            await self._spawn(str(script), env)

            async for changes in watchfiles.awatch(
                *watch_paths,
                watch_filter=self.config.watch_filter,
                debounce=self.config.debounce,
                step=self.config.step,
                stop_event=self._stop_event,
                rust_timeout=self.config.rust_timeout,
                debug=self.config.debug,
                force_polling=self.config.force_polling,
                poll_delay_ms=self.config.poll_delay_ms,
                recursive=self.config.recursive,
                ignore_permission_denied=self.config.ignore_permission_denied,
            ):
                if not changes:
                    continue

                changed = sorted({path for _, path in changes})
                self.logger.info("تغییر در فایل‌ها: %s", changed)

                # stop() may be called while awatch is yielding changes
                if self._stop_event.is_set():
                    break
                await self._restart(str(script), env)
        finally:
            self._stop_event.set()
            await self._shutdown_uninterruptible()
            self._stop_event = None

    async def stop(self) -> None:
        """Request watcher shutdown and stop the child process"""
        if self._stop_event is not None:
            self._stop_event.set()
        await self._shutdown_uninterruptible()

    def _resolve_watch_paths(self, script: Path) -> tuple[str, ...]:
        configured = self.config.watch_paths
        if configured is None:
            paths = (script.parent,)
        else:
            paths = tuple(Path(path).expanduser().resolve() for path in configured)
            if not paths:
                raise ValueError("watch_paths cannot be empty")

        for path in paths:
            if not path.exists():
                raise FileNotFoundError(f"Hot reload watch path not found: {path}")

        return tuple(str(path) for path in paths)

    async def _spawn(self, script_path: str, env: dict[str, str]) -> None:
        self._process = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            env=env,
        )
        self.logger.info("ربات با PID %s شروع شد", self._process.pid)

    async def _restart(self, script_path: str, env: dict[str, str]) -> None:
        await self._terminate_child()
        if self._stop_event is not None and self._stop_event.is_set():
            return
        await self._spawn(script_path, env)

    async def _terminate_child(self) -> None:
        process = self._process
        self._process = None

        if process is None or process.returncode is not None:
            return

        try:
            process.terminate()
        except ProcessLookupError:
            return

        try:
            await asyncio.wait_for(
                process.wait(),
                timeout=self.config.shutdown_timeout,
            )
        except asyncio.TimeoutError:
            self.logger.warning(
                "فرآیند فرزند (PID %s) در %ss متوقف نشد؛ kill اجباری",
                process.pid,
                self.config.shutdown_timeout,
            )
            with contextlib.suppress(ProcessLookupError):
                process.kill()
            await process.wait()

    async def _shutdown_uninterruptible(self) -> None:
        """Complete child cleanup even if the caller is cancelled"""
        cleanup_task = asyncio.create_task(self._terminate_child())
        cancelled = False

        while not cleanup_task.done():
            try:
                await asyncio.shield(cleanup_task)
            except asyncio.CancelledError:
                cancelled = True

        # Surface cleanup errors instead of hiding them
        cleanup_task.result()

        if cancelled:
            raise asyncio.CancelledError()
