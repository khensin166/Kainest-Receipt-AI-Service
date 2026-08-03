import logging
import sys
from loguru import logger
from app.core.config import settings

class InterceptHandler(logging.Handler):
    """
    Mengalihkan log bawaan Python (seperti dari Uvicorn/FastAPI) ke Loguru
    sehingga format log menjadi seragam dan rapi.
    """
    def emit(self, record: logging.LogRecord):
        # Ambil nama level loguru yang sesuai
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Cari frame pemanggil agar informasi baris kode tetap akurat (opsional, tapi bagus untuk debug)
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    logger.remove()

    # Format log yang jauh lebih rapi, mirip Winston di backend
    log_format = (
        "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> "
        "<level>[{level: <5}]</level> "
        "<cyan>[{name}]</cyan> - "
        "<level>{message}</level>"
    )

    plain_format = "[{time:YYYY-MM-DD HH:mm:ss}] [{level: <5}] [{name}] - {message}"

    # Console Output (Berwarna)
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=log_format,
        colorize=True,
    )

    # File Output (Plain Text)
    logger.add(
        "logs/receipt_ai_{time:YYYY-MM-DD}.log",
        level=settings.log_level,
        rotation="1 day",
        retention="7 days",
        compression="zip",
        format=plain_format,
    )

    # Tangkap semua log dari library standar Python & Uvicorn
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Supaya log uvicorn.access dan uvicorn.error juga masuk ke format kita
    for _log in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False


setup_logging()

__all__ = ["logger"]
