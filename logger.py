import logging

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler("fast_rub.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("fast_rub")
client_logger = logging.getLogger("fast_rub.client")
filters_logger = logging.getLogger("fast_rub.filters")