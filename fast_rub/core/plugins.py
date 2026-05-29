import os
import importlib.util
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client

class PluginManager:
    """مدیریت پلاگین‌ها — لود خودکار پلاگین‌ها از پوشه"""
    @staticmethod
    def load(
        client: "Client",
        folder: str = "plugins",
        logger: Optional[logging.Logger] = None
    ) -> int:
        """لود کردن همه پلاگین‌ها از یه پوشه."""
        log = logger or logging.getLogger("fast_rub.plugins")
        if not os.path.exists(folder):
            log.warning(f"پوشه پلاگین‌ها پیدا نشد: {folder}")
            os.makedirs(folder, exist_ok=True)
            log.info(f"پوشه پلاگین‌ها ساخته شد: {folder}")
            return 0
        if not os.path.isdir(folder):
            log.error(f"مسیر پلاگین‌ها یه پوشه نیست: {folder}")
            return 0
        loaded = 0
        skipped = 0
        for filename in sorted(os.listdir(folder)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            filepath = os.path.join(folder, filename)
            plugin_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(
                    f"fast_rub_plugin_{plugin_name}",
                    filepath
                )
                if spec is None or spec.loader is None:
                    log.warning(f"⚠️ نتونستیم پلاگین {plugin_name} رو لود کنیم")
                    skipped += 1
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "setup"):
                    if callable(module.setup):
                        module.setup(client)
                        loaded += 1
                        log.info(f"✅ پلاگین لود شد: {plugin_name}")
                    else:
                        log.warning(f"⚠️ پلاگین {plugin_name} تابع setup نداره")
                        skipped += 1
                else:
                    log.warning(f"⚠️ پلاگین {plugin_name} تابع setup نداره")
                    skipped += 1
            except Exception as e:
                log.error(f"❌ خطا در لود پلاگین {plugin_name}: {e}")
                skipped += 1
        log.info(f"پلاگین‌ها: {loaded} لود شد, {skipped} رد شد")
        return loaded
    
    @staticmethod
    def load_single(
        client: "Client",
        filepath: str
    ) -> bool:
        """لود یه پلاگین خاص."""
        if not os.path.exists(filepath):
            return False
        plugin_name = os.path.basename(filepath)[:-3]
        try:
            spec = importlib.util.spec_from_file_location(
                f"fast_rub_plugin_{plugin_name}",
                filepath
            )
            if spec is None or spec.loader is None:
                return False
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "setup") and callable(module.setup):
                module.setup(client)
                return True
        except Exception:
            pass
        return False
