"""Structured logging setup with request correlation tracking."""

import contextvars
import logging
import sys

# Context variable holding correlation ID for the current request context
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="system")


class RequestIdFilter(logging.Filter):
    """Logging filter that injects the current request correlation ID."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach request_id to log records.

        Args:
            record (logging.LogRecord): The log record being processed.

        Returns:
            bool: Always True to permit logging.
        """
        record.request_id = request_id_ctx.get()
        return True


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with structured format and request correlation ID.

    Args:
        level (str): Logging level string (e.g. 'DEBUG', 'INFO', 'WARNING').
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    log_format = (
        "[%(asctime)s] [%(levelname)s] [request_id=%(request_id)s] "
        "[%(name)s:%(funcName)s:%(lineno)d]: %(message)s"
    )

    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup is called multiple times
    root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Obtain a namespaced logger with correlation ID filter attached.

    Args:
        name (str): Component or module name.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    return logger
