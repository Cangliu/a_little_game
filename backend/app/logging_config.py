"""Unified logging configuration for the cultivation game backend.

Provides structured logging with rotation and consistent formatting
across all game engine modules.
"""
import logging
import logging.handlers
import os


def setup_logging(log_dir: str = "logs", level: str = "INFO") -> None:
    """Configure unified logging for the application.

    Args:
        log_dir: Directory for log files (created if not exists)
        level: Root log level (INFO for production)
    """
    # Create log directory if needed
    os.makedirs(log_dir, exist_ok=True)

    # Unified format
    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    # Root logger
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler (INFO level)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    # File handler with rotation (10MB, 3 backups)
    log_path = os.path.join(log_dir, "game.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Clear existing handlers and add new ones
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    logging.info("Logging configured: level=%s, file=%s", level, log_path)
