from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ServerSettings:
    host: str = "127.0.0.1"
    port: int = 8000


@dataclass(frozen=True, slots=True)
class Settings:
    source_url: str = "https://jwc.cugb.edu.cn/xszq/"
    request_timeout_seconds: float = 10
    request_retries: int = 2
    cache_ttl_seconds: int = 60
    server: ServerSettings = field(default_factory=ServerSettings)


def load_settings(path: Path) -> Settings:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"Config file not found: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read config file: {path}") from error
    if not isinstance(raw, dict):
        raise ValueError("Config root must be a JSON object")

    server_raw = raw.get("server", {})
    if not isinstance(server_raw, dict):
        raise ValueError("server must be a JSON object")
    settings = Settings(
        source_url=str(raw.get("source_url", "https://jwc.cugb.edu.cn/xszq/")),
        request_timeout_seconds=float(raw.get("request_timeout_seconds", 10)),
        request_retries=int(raw.get("request_retries", 2)),
        cache_ttl_seconds=int(raw.get("cache_ttl_seconds", 60)),
        server=ServerSettings(
            host=str(server_raw.get("host", "127.0.0.1")),
            port=int(server_raw.get("port", 8000)),
        ),
    )
    _validate(settings)
    return settings


def _validate(settings: Settings) -> None:
    parsed = urlparse(settings.source_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("source_url must be an HTTPS URL")
    if settings.request_timeout_seconds <= 0:
        raise ValueError("request_timeout_seconds must be positive")
    if not 0 <= settings.request_retries <= 10:
        raise ValueError("request_retries must be between 0 and 10")
    if not 1 <= settings.cache_ttl_seconds <= 3600:
        raise ValueError("cache_ttl_seconds must be between 1 and 3600")
    if not settings.server.host:
        raise ValueError("server.host must not be empty")
    if not 1 <= settings.server.port <= 65535:
        raise ValueError("server.port must be between 1 and 65535")
