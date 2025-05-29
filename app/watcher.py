import logging
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFHandler(FileSystemEventHandler):
    def __init__(self, queue, directory):
        self.queue = queue
        self.directory = Path(directory)

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".pdf"):
            logger.info(f"New PDF detected: {event.src_path}")
            asyncio.run_coroutine_threadsafe(
                self.queue.put(event.src_path), asyncio.get_event_loop()
            )

    def on_modified(self, event):
        self.on_created(event)


async def start_watcher(directory: str, queue: asyncio.Queue):
    event_handler = PDFHandler(queue, directory)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    logger.info(f"Started directory watcher on {directory}")
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        observer.stop()
        observer.join()
