import logging
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from sources.local_files import LocalFileSource

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = LocalFileSource().supported_extensions()


class _ContentHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event.src_path)

    def _handle(self, path: str) -> None:
        if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS:
            logger.info(f"File change detected: {path}")
            self.callback(path)


class ContentWatcher:
    def __init__(
        self,
        watched_dirs: list[str],
        on_file_changed: Callable[[str], None],
        *,
        recursive: bool = True,
    ):
        self.watched_dirs = watched_dirs
        self.on_file_changed = on_file_changed
        self._recursive = recursive
        self._observer = Observer()
        self._handler = _ContentHandler(on_file_changed)
        self._started = False

    def start(self) -> None:
        scheduled = 0
        for dir_path in self.watched_dirs:
            p = Path(dir_path)
            if p.is_dir():
                self._observer.schedule(self._handler, str(p.resolve()), recursive=self._recursive)
                scheduled += 1
                logger.info("Watching (recursive=%s): %s", self._recursive, p)
        if scheduled:
            self._observer.start()
            self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._observer.stop()
        self._observer.join(timeout=5)
        self._started = False

    def update_dirs(self, new_dirs: list[str]) -> None:
        self.stop()
        self.watched_dirs = new_dirs
        self._observer = Observer()
        self._handler = _ContentHandler(self.on_file_changed)
        self.start()
