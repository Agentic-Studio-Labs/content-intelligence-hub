from pathlib import Path

from shared.config import settings


def sanitize_object_path(object_path: str) -> Path:
    object_path = object_path.lstrip("/").replace("..", "")
    return settings.object_root / object_path


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_object(object_path: str, data: bytes) -> str:
    path = sanitize_object_path(object_path)
    ensure_parent(path)
    path.write_bytes(data)
    return str(path)


def read_object_text(object_path: str) -> str:
    path = sanitize_object_path(object_path)
    return path.read_text(encoding="utf-8")
