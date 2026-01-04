import logging
import json
import sys
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler


# -------- Context --------
request_id = ContextVar("request_id", default=None)
job_id = ContextVar("job_id", default=None)
task_id = ContextVar("task_id", default=None)
pipeline = ContextVar("pipeline", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "file": record.filename,
            "line": record.lineno,
            "request_id": request_id.get(),
            "job_id": job_id.get(),
            "task_id": task_id.get(),
            "pipeline": pipeline.get(),
        }

        if hasattr(record, "extra_fields"):
            base.update(record.extra_fields)

        return json.dumps(base)



_CONFIGURED = False


def info(message: str, **fields):
    log.info(message, extra={"extra_fields": fields})

def error(message: str, **fields):
    log.error(message, extra={"extra_fields": fields})

def exception(message: str, **fields):
    log.exception(message, extra={"extra_fields": fields})

def debug(message: str, **fields):
    log.debug(message, extra={"extra_fields": fields})

def warning(message: str, **fields):
    log.warning(message, extra={"extra_fields": fields})



def configure_logger(level=logging.INFO):
    global _CONFIGURED

    logger = logging.getLogger("APP")
    logger.setLevel(level)

    if _CONFIGURED:
        return logger

    # Ensure log directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    formatter = JsonFormatter()

    # ---- stdout handler (for docker / airflow / systemd) ----
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    # ---- file handler (local / legacy) ----
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=50_000_000,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

    logger.propagate = False
    _CONFIGURED = True

    return logger


log = configure_logger()

