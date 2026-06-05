import os
import sys
import subprocess
import logging


class HotReload:
    def __init__(
        self,
        logger: logging.Logger | None = None
    ):
        self.logger = logger or logging.getLogger("fast_rub.hotreload")
    
    def run_sync(
        self,
        script_path: str
    ):
        try:
            import watchfiles
        except ImportError:
            raise ImportError("کتابخانه 'watchfiles' نصب نیست. برای نصب: pip install watchfiles")
        
        watch_dir = os.path.dirname(os.path.abspath(script_path))
        self.logger.info(f"Hot Reload فعال شد. مسیر تحت نظر: {watch_dir}")
        
        env = os.environ.copy()
        env["FASTRUB_RELOAD_CHILD"] = "1"
        
        process = subprocess.Popen([sys.executable, script_path], env=env)
        self.logger.info(f"ربات با PID {process.pid} شروع شد")
        
        for changes in watchfiles.watch(
            watch_dir,
            watch_filter=lambda _, p: p.endswith(".py") and "__pycache__" not in p
        ):
            if changes:
                changed_files = [path for _, path in changes]
                self.logger.info(f"تغییر در: {changed_files}")
                
                process.terminate()
                process.wait()
                
                process = subprocess.Popen([sys.executable, script_path], env=env)
                self.logger.info(f"راه‌اندازی مجدد با PID {process.pid}")
