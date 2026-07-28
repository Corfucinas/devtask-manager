"""Structured logging configuration."""
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class LogConfig:
    """Logging configuration."""
    level: str = "INFO"
    format_type: str = "text"
    destination: str = "console"
    file_path: str = ""
    include_timestamp: bool = True
    include_module: bool = True
    include_level: bool = True
    extra_fields: Dict[str, str] = field(default_factory=dict)

    @property
    def level_value(self) -> int:
        return getattr(logging, self.level.upper(), logging.INFO)


class JSONFormatter(logging.Formatter):
    """JSON structured log formatter."""

    def __init__(self, include_timestamp: bool = True,
                 include_module: bool = True,
                 include_level: bool = True,
                 extra_fields: dict = None):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_module = include_module
        self.include_level = include_level
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        data = {"message": record.getMessage()}
        if self.include_timestamp:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        if self.include_module:
            data["module"] = record.name
        if self.include_level:
            data["level"] = record.levelname
        data.update(self.extra_fields)
        if record.exc_info and record.exc_info[1]:
            data["exception"] = str(record.exc_info[1])
        return json.dumps(data)


class TextFormatter(logging.Formatter):
    """Readable text log formatter."""

    def __init__(self, include_timestamp: bool = True,
                 include_module: bool = True,
                 include_level: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_module = include_module
        self.include_level = include_level

    def format(self, record: logging.LogRecord) -> str:
        parts = []
        if self.include_timestamp:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[{ts}]")
        if self.include_level:
            parts.append(f"[{record.levelname}]")
        if self.include_module:
            parts.append(f"[{record.name}]")
        parts.append(record.getMessage())
        return " ".join(parts)


def setup_logging(config: LogConfig = None) -> logging.Logger:
    if config is None:
        config = LogConfig()
    root_logger = logging.getLogger()
    root_logger.setLevel(config.level_value)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    if config.destination == "file" and config.file_path:
        handler = logging.FileHandler(config.file_path)
    else:
        handler = logging.StreamHandler(sys.stdout)
    if config.format_type == "json":
        formatter = JSONFormatter(
            include_timestamp=config.include_timestamp,
            include_module=config.include_module,
            include_level=config.include_level,
            extra_fields=config.extra_fields,
        )
    else:
        formatter = TextFormatter(
            include_timestamp=config.include_timestamp,
            include_module=config.include_module,
            include_level=config.include_level,
        )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    return root_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event_type: str,
              message: str, **kwargs) -> None:
    extra = {"event_type": event_type}
    extra.update(kwargs)
    logger.info(message, extra=extra)


def default_config() -> LogConfig:
    return LogConfig(level="INFO", format_type="text", destination="console")


def debug_config() -> LogConfig:
    return LogConfig(level="DEBUG", format_type="json", destination="console")


def file_config(file_path: str, level: str = "INFO") -> LogConfig:
    return LogConfig(level=level, format_type="json", destination="file", file_path=file_path)


def silence_logger(name: str) -> None:
    logging.getLogger(name).setLevel(logging.WARNING)


def log_level_name(level: int) -> str:
    return logging.getLevelName(level)
