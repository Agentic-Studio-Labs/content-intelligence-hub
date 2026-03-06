import time
from pathlib import Path
from unittest.mock import MagicMock
from watcher import ContentWatcher
import pytest


def test_watcher_init(tmp_path):
    watcher = ContentWatcher(
        watched_dirs=[str(tmp_path)],
        on_file_changed=MagicMock(),
    )
    assert len(watcher.watched_dirs) == 1


def test_watcher_detects_new_file(tmp_path):
    callback = MagicMock()
    watcher = ContentWatcher(
        watched_dirs=[str(tmp_path)],
        on_file_changed=callback,
    )
    watcher.start()
    try:
        test_file = tmp_path / "new-post.md"
        test_file.write_text("# New Post\n\nContent here.")
        time.sleep(1.5)
    finally:
        watcher.stop()
    assert callback.call_count >= 1
    call_args = [str(c[0][0]) for c in callback.call_args_list]
    assert any("new-post.md" in arg for arg in call_args)


def test_watcher_ignores_unsupported_files(tmp_path):
    callback = MagicMock()
    watcher = ContentWatcher(
        watched_dirs=[str(tmp_path)],
        on_file_changed=callback,
    )
    watcher.start()
    try:
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        time.sleep(1.5)
    finally:
        watcher.stop()
    call_args = [str(c[0][0]) for c in callback.call_args_list]
    assert not any(".png" in arg for arg in call_args)
