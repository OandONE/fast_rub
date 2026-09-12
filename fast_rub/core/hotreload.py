import asyncio
import contextlib
import logging
import os
import sys
from pathlib import Path


class HotReload:
    """
    Hot Reload async-native برای fast_rub.

    در فرآیند والد اجرا می‌شود، یک فرآیند فرزند از اسکریپت اصلی می‌سازد،
    تغییرات فایل‌های .py را در پوشه‌ی اسکریپت زیر نظر می‌گیرد و در صورت
    تغییر، فرزند را تمیز terminate کرده و دوباره راه‌اندازی می‌کند.

    ویژگی‌ها:
    - event loop والد بلاک نمی‌شود
    - فرزند روی cancel شدن یا خطا حتماً بسته می‌شود (بدون zombie)
    - در برابر Ctrl+C دوباره و cancel هم‌زمان مقاوم است
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
        shutdown_timeout: float = 5.0,
        debounce_ms: int = 500,
    ):
        self.logger = logger or logging.getLogger("fast_rub.hotreload")
        self.shutdown_timeout = shutdown_timeout
        self.debounce_ms = debounce_ms
        self._process: asyncio.subprocess.Process | None = None

    # Public API

    def run_sync(self, script_path: str) -> None:
        """نگه‌داشته شده برای سازگاری عقب‌رو — از run_async استفاده کنید."""
        asyncio.run(self.run_async(script_path))

    async def run_async(self, script_path: str) -> None:
        try:
            import watchfiles
        except ImportError as e:
            raise ImportError(
                "کتابخانه 'watchfiles' نصب نیست. برای نصب: pip install watchfiles"
            ) from e

        script_path = str(Path(script_path).resolve())
        watch_dir = os.path.dirname(script_path)
        self.logger.info(f"Hot Reload فعال شد. مسیر تحت نظر: {watch_dir}")

        env = os.environ.copy()
        env["FASTRUB_RELOAD_CHILD"] = "1"

        await self._spawn(script_path, env)

        try:
            async for changes in watchfiles.awatch(
                watch_dir,
                watch_filter=self._filter,
                debounce=self.debounce_ms,
            ):
                if not changes:
                    continue
                changed = sorted({path for _, path in changes})
                self.logger.info(f"تغییر در: {changed}")
                await self._restart(script_path, env)
        finally:
            await self._shutdown_uninterruptible()

    async def stop(self) -> None:
        """توقف دستی hot reload (برای فراخوانی از بیرون)."""
        await self._shutdown_uninterruptible()

    # Internals

    @staticmethod
    def _filter(_change, path: str) -> bool:
        return path.endswith(".py") and "__pycache__" not in path

    async def _spawn(self, script_path: str, env: dict[str, str]) -> None:
        self._process = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            env=env,
        )
        self.logger.info(f"ربات با PID {self._process.pid} شروع شد")

    async def _restart(self, script_path: str, env: dict[str, str]) -> None:
        await self._terminate_child()
        await self._spawn(script_path, env)

    async def _terminate_child(self) -> None:
        proc = self._process
        if proc is None or proc.returncode is not None:
            self._process = None
            return

        try:
            proc.terminate()
        except ProcessLookupError:
            self._process = None
            return

        try:
            await asyncio.wait_for(
                proc.wait(), timeout=self.shutdown_timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning(
                f"فرآیند فرزند (PID {proc.pid}) در {self.shutdown_timeout}s "
                f"پاسخ نداد، kill اجباری."
            )
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            await proc.wait()
        finally:
            self._process = None

    async def _shutdown_uninterruptible(self) -> None:
        """
        فرزند رو می‌بنده، حتی اگر coroutine جاری یک یا چند بار cancel بشه.

        الگو: cleanup رو به یه task مستقل تبدیل می‌کنیم و با shield منتظرش
        می‌مونیم. اگر cancel برسه، shield خطا می‌ده ولی task پس‌زمینه ادامه
        می‌ده. بعدش دوباره روی همون task await می‌کنیم تا واقعاً تموم شه،
        و در نهایت CancelledError رو re-raise می‌کنیم.
        """
        cleanup_task = asyncio.ensure_future(self._terminate_child())

        cancelled = False
        while not cleanup_task.done():
            try:
                await asyncio.shield(cleanup_task)
            except asyncio.CancelledError:
                cancelled = True
                continue

        if cancelled:
            raise asyncio.CancelledError()

