"""Immediate halt for new orders: env var and/or a local file."""

from __future__ import annotations

import os
from pathlib import Path

ENV_FLAG = "DTA_KILL_SWITCH"
DEFAULT_FILE = Path("data/KILL")


def file_path(configured: str | None = None) -> Path:
    return Path(configured or DEFAULT_FILE)


def is_active(configured_file: str | None = None) -> bool:
    env = os.getenv(ENV_FLAG, "").strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    return file_path(configured_file).exists()


def pause(configured_file: str | None = None) -> Path:
    path = file_path(configured_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("paused\n", encoding="utf-8")
    return path


def resume(configured_file: str | None = None) -> bool:
    path = file_path(configured_file)
    if path.exists():
        path.unlink()
        return True
    return False


def reason(configured_file: str | None = None) -> str | None:
    if not is_active(configured_file):
        return None
    env = os.getenv(ENV_FLAG, "").strip().lower()
    parts = []
    if env in {"1", "true", "yes", "on"}:
        parts.append(f"{ENV_FLAG}={os.getenv(ENV_FLAG)}")
    if file_path(configured_file).exists():
        parts.append(f"file {file_path(configured_file)}")
    return "kill switch ON (" + ", ".join(parts) + ")"
