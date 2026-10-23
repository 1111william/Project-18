"""Production container entry point.

Builds an explicit Uvicorn argument vector and then replaces this process, so
Uvicorn is PID 1 and receives SIGTERM directly from the container runtime.
"""

from __future__ import annotations

import os
import sys


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}
LOG_LEVELS = {"critical", "error", "warning", "info", "debug", "trace"}


def boolean_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ValueError(f"{name} must be one of 1/0, true/false, yes/no, or on/off")


def integer_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def build_command() -> list[str]:
    host = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"
    port = integer_env("PORT", 8000, 1, 65535)
    workers = integer_env("WEB_CONCURRENCY", 1, 1, 32)
    log_level = os.getenv("LOG_LEVEL", "info").strip().lower()
    if log_level not in LOG_LEVELS:
        raise ValueError(f"LOG_LEVEL must be one of {', '.join(sorted(LOG_LEVELS))}")

    command = [
        "uvicorn",
        "backend.app.main:app",
        "--host",
        host,
        "--port",
        str(port),
        "--workers",
        str(workers),
        "--log-level",
        log_level,
        "--no-server-header",
    ]

    if boolean_env("UVICORN_ACCESS_LOG", True):
        command.append("--access-log")
    else:
        command.append("--no-access-log")

    if boolean_env("TRUSTED_PROXY_HEADERS", False):
        allowed = os.getenv("FORWARDED_ALLOW_IPS", "").strip()
        if not allowed:
            raise ValueError(
                "FORWARDED_ALLOW_IPS is required when TRUSTED_PROXY_HEADERS=1"
            )
        command.extend(["--proxy-headers", "--forwarded-allow-ips", allowed])
    else:
        command.append("--no-proxy-headers")

    return command


def main() -> None:
    try:
        command = build_command()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(2) from exc

    print(
        f"Starting API on {command[command.index('--host') + 1]}:"
        f"{command[command.index('--port') + 1]}",
        flush=True,
    )
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
