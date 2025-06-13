import ee
import time
import threading

from ee_wildfire.constants import EXPORT_QUEUE_SIZE, USA_COORDS
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.ExportQueue.ExportMonitor import ExportMonitor

class QueueManager:
    MAX_ACTIVE_TASKS = 3  # GEE typically limits to 2–3 concurrent tasks
    TASK_POLL_INTERVAL = 10  # seconds

    def __init__(self, poll_interval: int = 10):
        self.task_queue = []
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._monitor, daemon=False)
        self._lock = threading.RLock()

    def start(self):
        ConsoleUI.debug("Starting export monitor thread.")
        self.thread.start()

    def _monitor(self):
        unfinished = self.task_queue
        total = max(len(unfinished), EXPORT_QUEUE_SIZE)
        ConsoleUI.add_bar(key="export_queue", total=total, desc="Export Queue")
        while unfinished and not self._stop.is_set():
            ConsoleUI.set_bar_position(key="export_queue", value=len(unfinished))
            for task in list(unfinished):
                st = task.status()
                state = st.get("state")
                ConsoleUI.debug(f"Task {st.get('id')} state: {state}")
                if state in ("COMPLETED", "FAILED", "CANCELLED"):
                    unfinished.remove(task)
                    ConsoleUI.print(f"Task {st['description']} finished: {state}")
                    if state == "FAILED":
                        ConsoleUI.error(f"Error: {st.get('error_message')}")
            time.sleep(self.poll_interval)

    def stop(self):
        self._stop.set()
        self.thread.join()

    # FIX: this needs to be generalized.
    def add_export(self, image: ee.Image, description: str, filename: str):
        """
        Queue an export task to Google Drive.
        """
        # TODO: invalidate this stuff yo

        # task_args = {
        #     'image': image,
        #     'description': description,
        #     'folder': folder,
        #     'region': USA_COORDS,
        # }
        ConsoleUI.print(f"Exporting image as {filename}")
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            folder="EE-Wildfire-Test",
            region=USA_COORDS,
            fileNamePrefix=filename,
        )
        
        task.start()
        with self._lock:
            self.task_queue.append(task)


    def is_done(self) -> bool:
        """Check if all tasks are done."""
        with self._lock:
            return not self.task_queue and not self.running_tasks

