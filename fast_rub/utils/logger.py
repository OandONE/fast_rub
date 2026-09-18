import logging

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_LOG_FILE = "fast_rub.log"

class CallbackHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._callback = None
    
    def set_callback(self, callback):
        self._callback = callback
    
    def emit(self, record):
        if self._callback:
            log_entry = {
                "level": record.levelname,
                "message": self.format(record),
                "time": record.created,
                "name": record.name,
            }
            self._callback(log_entry)

def setup_logging(
    *,
    log_to_file: bool = True,
    log_to_console: bool = True,
    level: int = logging.INFO,
    log_file: str = DEFAULT_LOG_FILE
):
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)
    root_logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)
    if log_to_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)
    if log_to_console:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        root_logger.addHandler(sh)
    # httpx هر درخواست را با URL کامل در INFO لاگ می‌کند که توکن ربات داخل URL است —
    # جلوگیری از نشت توکن در فایل لاگ
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # CallbackHandler همیشه باید بماند — وگرنه on_log بعد از start() کار نمی‌کند
    if _callback_handler not in root_logger.handlers:
        root_logger.addHandler(_callback_handler)
    return logging.getLogger("fast_rub")

_callback_handler = CallbackHandler()
_callback_handler.setLevel(logging.DEBUG)

_default_logger = setup_logging(log_to_file=True, log_to_console=True)
logger = logging.getLogger("fast_rub")

def set_log_callback(callback):
    _callback_handler.set_callback(callback)
